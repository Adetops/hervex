# runner.py is the executor — the engine that drives task execution.
# It receives a goal's session ID, loads all pending tasks,
# and processes them sequentially.
#
# The executor does not know HOW to execute a task — it delegates
# to the tool registry for tool-based tasks and to the LLM
# for reasoning-only tasks.
#
# Design principle: one task failure should not stop the entire run.
# The executor logs the failure, marks the task as failed,
# and moves to the next task.

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
from app.core.settings import APP_NAME

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
            # Attempt to execute the task
            # In Phase 3, execution is simulated — real tool calls come in Phase 4
            result = await _execute_task(description, tool)

            # Mark the task as completed and save the result
            await update_task_status(
                session_id,
                task_id,
                TaskStatus.COMPLETED,
                result=result
            )
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

    # All tasks processed — update goal and run status
    await update_goal_status(session_id, GoalStatus.AGGREGATING)
    await complete_run(session_id, GoalStatus.AGGREGATING)
    print(f"[{APP_NAME}] Executor: All tasks processed for session {session_id}. Ready for aggregation.")

async def _execute_task(description: str, tool: Optional[str]) -> str:
    """
    Executes a single task by delegating to the appropriate handler.

    In Phase 3, tool-based tasks return a placeholder result.
    Real tool execution is wired in Phase 4.

    In Phase 3, reasoning-only tasks return a simulated LLM response.
    Real LLM reasoning per task is wired in Phase 6 with memory context.

    Args:
        description: What the task requires
        tool: The tool to use, or None for reasoning-only tasks

    Returns:
        A string result from the task execution
    """

    if tool == "web_search":
        # Placeholder — replaced with real web search in Phase 4
        return f"[Phase 3 placeholder] Web search result for: {description}"

    # Reasoning-only task — no tool required
    # Placeholder — will use memory context in Phase 6
    return f"[Phase 3 placeholder] Reasoning result for: {description}"
