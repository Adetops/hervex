# agent_tasks.py defines the Celery task functions for HERVEX.
# These are the functions that Celery workers actually execute
# when a goal is submitted.
#
# Important: Celery tasks are synchronous functions that run in
# separate worker processes. Since our executor is async, we use
# asyncio.run() to run the async executor from inside the sync Celery task.
#
# This file is separate from celery_app.py to keep configuration
# and task logic clearly separated.

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
    Celery task that runs the full agent execution pipeline
    for a given session in a background worker process.

    Because Celery tasks are synchronous but our executor is async,
    asyncio.run() bridges the two — it creates a new event loop,
    runs the async function to completion, then closes the loop.

    Args:
        session_id: The unique session identifier of the goal to execute

    The task imports executor and db connection inside the function
    to avoid import-time issues in the Celery worker process.
    """
    print(f"[{APP_NAME}] Celery worker: Picked up task for session {session_id}")

    try:
        # Import here to avoid circular imports and ensure
        # the worker process has its own clean import context
        from app.db.connection import connect_to_mongodb
        from app.executor.runner import execute_goal

        async def run():
            """
            Inner async function that sets up MongoDB and runs the executor.
            The worker process needs its own MongoDB connection
            since it's a separate process from the FastAPI server.
            """
            # Each worker needs its own MongoDB connection
            await connect_to_mongodb()
            # Run the full executor pipeline
            await execute_goal(session_id)

        # Bridge async executor into sync Celery task
        asyncio.run(run())

    except Exception as exc:
        print(f"[{APP_NAME}] Celery worker: Task failed for session {session_id} — {exc}")
        # Retry the task if it fails unexpectedly
        raise self.retry(exc=exc)
