# agent_tasks.py defines the Celery task functions for HERVEX.
# These are the functions that Celery workers actually execute
# when a goal is submitted.
#
# After the executor finishes all tasks, the Celery worker
# now triggers the aggregator to generate the final response.
# The full pipeline is now connected end to end.

import asyncio
from app.tasks.celery_app import celery_app
from app.core.settings import APP_NAME

@celery_app.task(
    name="execute_goal_task",
    bind=True,           # Gives the task access to self for retries
    max_retries=3,       # Retry up to 3 times on unexpected failure
    default_retry_delay=5  # Wait 5 seconds between retries
)
def execute_goal_task(self, session_id: str):
    """
    Celery task that runs the full agent pipeline for a session:
    1. Connects to MongoDB
    2. Runs the executor — all tasks executed with tool calls and memory
    3. Runs the aggregator — synthesizes results into final response
    4. Goal is marked COMPLETED in MongoDB

    Args:
        session_id: The unique session identifier of the goal to execute
    """
    print(f"[{APP_NAME}] Celery worker: Picked up task for session {session_id}")

    try:
        from app.db.connection import connect_to_mongodb
        from app.executor.runner import execute_goal
        from app.services.result_service import finalize_result

        async def run():
            """
            Inner async function that runs the full pipeline.
            MongoDB connection is established once and shared
            across both executor and aggregator.
            """
            # Establish MongoDB connection for this worker process
            await connect_to_mongodb()

            # Phase 3-6: Execute all tasks with tools and memory
            await execute_goal(session_id)

            # Phase 7: Aggregate all results into final response
            await finalize_result(session_id)

        # Bridge async pipeline into sync Celery task
        asyncio.run(run())

    except Exception as exc:
        print(
            f"[{APP_NAME}] Celery worker: Pipeline failed "
            f"for session {session_id} — {exc}"
        )
        raise self.retry(exc=exc)
