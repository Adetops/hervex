# runner.py is the executor — the engine that drives task execution.
# runner.py — updated for Phase 5
# rag_search tool now receives institution_id from the goal document
# so it searches only that institution's Pinecone namespace.
# This enforces cross-institution data isolation at execution time.

import asyncio
from typing import Optional
from loguru import logger
from app.db.collections.goals import get_goal_by_session, update_goal_status
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
from app.memory.context import (
    store_task_result,
    get_session_context,
    clear_session_memory
)
from app.core.settings import APP_NAME, LLM_PLANNER_MODEL, LLM_MAX_TOKENS
from app.core.config import settings
from groq import Groq

_llm_client = Groq(api_key=settings.GROQ_API_KEY)


async def execute_goal(session_id: str):
    """
    Main executor entry point.
    Loads the goal document, creates a run record,
    and processes all tasks sequentially.

    Phase 5 addition: institution_id is extracted from the goal
    document and passed to rag_search for namespace isolation.

    Args:
        session_id: The unique session identifier
    """
    goal_doc = await get_goal_by_session(session_id)

    if not goal_doc:
        logger.error(
            f"[{APP_NAME}] Executor: Goal not found for "
            f"session {session_id}"
        )
        return

    tasks = goal_doc.get("tasks", [])

    if not tasks:
        logger.error(
            f"[{APP_NAME}] Executor: No tasks found for "
            f"session {session_id}"
        )
        await update_goal_status(session_id, GoalStatus.FAILED)
        return

    # Extract institution_id for RAG namespace isolation
    # Falls back to 'default' if not set (backward compatible)
    institution_id = goal_doc.get("institution_id", "default")

    run_doc = RunDocument.create(
        session_id=session_id,
        goal=goal_doc["goal"],
        task_count=len(tasks)
    )
    await insert_run(run_doc)

    logger.info(
        f"[{APP_NAME}] Executor: Starting run for session "
        f"{session_id} — {len(tasks)} tasks — "
        f"institution: {institution_id}"
    )

    for task in tasks:
        task_id = task["task_id"]
        description = task["description"]
        tool = task.get("tool")

        logger.info(
            f"[{APP_NAME}] Executor: Running task {task_id} "
            f"— {description[:60]}..."
        )

        await update_task_status(session_id, task_id, TaskStatus.RUNNING)

        try:
            result = await _execute_task(
                session_id=session_id,
                description=description,
                tool=tool,
                institution_id=institution_id
            )

            await update_task_status(
                session_id, task_id,
                TaskStatus.COMPLETED, result=result
            )
            await store_task_result(session_id, description, result)
            await increment_completed_tasks(session_id)
            logger.info(
                f"[{APP_NAME}] Executor: Task {task_id} completed"
            )

        except Exception as e:
            error_message = str(e)
            await update_task_status(
                session_id, task_id,
                TaskStatus.FAILED, error=error_message
            )
            await increment_failed_tasks(session_id)
            logger.error(
                f"[{APP_NAME}] Executor: Task {task_id} failed "
                f"— {error_message}"
            )

        # Delay between tasks to respect Groq rate limits
        await asyncio.sleep(5)

    await clear_session_memory(session_id)
    await update_goal_status(session_id, GoalStatus.AGGREGATING)
    await complete_run(session_id, GoalStatus.AGGREGATING)

    logger.info(
        f"[{APP_NAME}] Executor: All tasks processed for "
        f"session {session_id}. Ready for aggregation."
    )


async def _execute_task(
    session_id: str,
    description: str,
    tool: Optional[str],
    institution_id: str = "default"
) -> str:
    """
    Executes a single task by calling the appropriate tool.

    Phase 5 addition: rag_search receives institution_id
    so it searches only the correct institution's namespace.

    Args:
        session_id: Used to read Redis memory context
        description: Task description — used as tool query
        tool: Tool name string, or None for reasoning tasks
        institution_id: Institution namespace for RAG isolation

    Returns:
        String result from tool call or LLM reasoning
    """
    if tool:
        tool_fn = get_tool(tool)

        if not tool_fn:
            raise ValueError(
                f"Tool '{tool}' not found in registry. "
                f"Available: {list(get_tool.__globals__.get('TOOL_REGISTRY', {}).keys())}"
            )

        # Pass institution_id to rag_search for namespace isolation
        # Other tools don't need it — only RAG searches institution data
        if tool == "rag_search":
            result = await tool_fn(
                query=description,
                institution_id=institution_id
            )
        else:
            result = await tool_fn(description)

        return result

    # Reasoning-only task — read accumulated memory context
    context = await get_session_context(session_id)

    if context:
        prompt = (
            f"{context}\n\n"
            f"Based on the above results, complete the following task:\n"
            f"{description}\n\n"
            f"If the results are from school materials, base your answer "
            f"on those materials and cite them. If from internet search, "
            f"clearly indicate the source. Provide a clear, detailed response."
        )
    else:
        prompt = (
            f"Complete the following task:\n{description}\n\n"
            f"Provide a clear, detailed response."
        )

    response = _llm_client.chat.completions.create(
        model=LLM_PLANNER_MODEL,
        max_tokens=LLM_MAX_TOKENS,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are HERVEX, an autonomous AI education agent. "
                    "You have access to results from previous tasks including "
                    "content from the institution's uploaded school materials. "
                    "When content is labelled FROM SCHOOL MATERIALS, cite it clearly. "
                    "When content is from internet search, label it as such. "
                    "Never mix sources without labelling them."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content
