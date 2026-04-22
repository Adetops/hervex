# runner.py is the executor — the engine that drives task execution.
# It receives a goal's session ID, loads all pending tasks,
# and processes them sequentially.
#
# Two key changes:
# 1. After each successful task, result is stored in Redis memory
# 2. Reasoning-only tasks now read accumulated context from Redis
#    and pass it to the LLM

import asyncio
from typing import Optional
from app.db.collections.goals import (
    get_goal_by_session,
    update_goal_status,
    update_goal_tasks
)
from app.db.collections.tasks import update_task_status
from app.db.collections.runs import (
    insert_run,
    increment_completed_tasks,
    increment_failed_tasks,
    complete_run
)
from app.db.documents.run_document import RunDocument
from app.enums.status import GoalStatus, TaskStatus
from app.tools.registry import get_tool
from app.core.settings import APP_NAME
from app.memory.context import store_task_result, get_session_context, clear_session_memory
from groq import Groq
from app.core.config import settings
from app.core.settings import LLM_PLANNER_MODEL, LLM_MAX_TOKENS


# Groq client for reasoning-only task execution
# Same client as the planner — reused here for consistency
_llm_client = Groq(api_key=settings.SECRET_GROQ_KEY)

async def execute_goal(session_id: str):
    """
    Main executor entry point.
    Loads the goal, creates a run record, and processes all tasks.

    Args:
        session_id: The unique session identifier for the goal to execute
    """

    # Load the goal document from MongoDB
    goal_doc = await get_goal_by_session(session_id)

    if not goal_doc:
        print(f"[{APP_NAME}] Executor: Goal not found for session {session_id}")
        return

    tasks = goal_doc.get("tasks", [])

    if not tasks:
        print(f"[{APP_NAME}] Executor: No tasks found for session {session_id}")
        await update_goal_status(session_id, GoalStatus.FAILED)
        return

    # Create an execution run record to track this agent run
    run_doc = RunDocument.create(
        session_id=session_id,
        goal=goal_doc["goal"],
        task_count=len(tasks)
    )
    await insert_run(run_doc)

    print(f"[{APP_NAME}] Executor: Starting run for session {session_id} — {len(tasks)} tasks")

    # Process each task sequentially
    for task in tasks:
        task_id = task["task_id"]
        description = task["description"]
        tool = task.get("tool")

        print(f"[{APP_NAME}] Executor: Running task {task_id} — {description}")

        # Mark the task as running before execution begins
        await update_task_status(session_id, task_id, TaskStatus.RUNNING)

        try:
            result = await _execute_task(session_id, description, tool)

            # Mark the task as completed and save the result
            await update_task_status(
                session_id,
                task_id,
                TaskStatus.COMPLETED,
                result=result
            )
            
            # Store the result in Redis memory for subsequent tasks
            # This is the core of Phase 6 — every result builds context
            await store_task_result(session_id, description, result)

            await increment_completed_tasks(session_id)
            print(f"[{APP_NAME}] Executor: Task {task_id} completed.")

        except Exception as e:
            # Mark the task as failed but continue to the next task
            error_message = str(e)
            await update_task_status(
                session_id,
                task_id,
                TaskStatus.FAILED,
                error=error_message
            )
            await increment_failed_tasks(session_id)
            print(f"[{APP_NAME}] Executor: Task {task_id} failed — {error_message}")
            
        # Small delay between tasks to avoid hammering Groq's rate limiter
        # 2 seconds is enough to stay within the TPM window
        await asyncio.sleep(2)

    # All tasks processed — update goal and run status
    await update_goal_status(session_id, GoalStatus.AGGREGATING)
    await complete_run(session_id, GoalStatus.AGGREGATING)
    print(f"[{APP_NAME}] Executor: All tasks processed for session {session_id}. Ready for aggregation.")

async def _execute_task(session_id: str, description: str, tool: Optional[str]) -> str:
    """
    Executes a single task.
    
    For tool-based tasks: retrieves the tool function from the registry
    and calls it with the task description as the query. 

    Reasoning-only tasks: reads accumulated Redis memory and passes
    it as context to the LLM — replacing the Phase 3/4 placeholder.

    Args:
        session_id: Used to read and write Redis memory
        description: The task description — used as tool query or LLM prompt
        tool: The tool name string, or None for reasoning-only tasks

    Returns:
        A string result from the tool call or LLM reasoning

    Raises:
        ValueError: If the specified tool is not found in the registry
    """

    if tool:
        # Tool-based task — look up and call the tool
        tool_fn = get_tool(tool)

        if not tool_fn:
            raise ValueError(
                f"Tool '{tool}' not found in registry."
            )

        result = await tool_fn(description)
        return result

    # Reasoning-only task — read accumulated memory context
    # and send to LLM with the task description
    context = await get_session_context(session_id)

    # Build the reasoning prompt with full memory context
    # The LLM uses previous results to perform the current task
    if context:
        prompt = (
            f"{context}\n\n"
            f"Based on the above results, complete the following task:\n"
            f"{description}\n\n"
            f"Provide a clear, detailed response."
        )
    else:
        # No prior context yet — first reasoning task in the session
        prompt = (
            f"Complete the following task:\n"
            f"{description}\n\n"
            f"Provide a clear, detailed response."
        )

    # Call the LLM with the context-aware prompt
    response = _llm_client.chat.completions.create(
        model=LLM_PLANNER_MODEL,
        max_tokens=LLM_MAX_TOKENS,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are HERVEX, an autonomous AI agent executing a task. "
                    "You have access to results from previous tasks. "
                    "Use them to complete the current task accurately and thoroughly."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content
