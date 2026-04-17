# agent_service.py orchestrates the full agent execution flow.
# It is called after goal_service.py has saved the goal and tasks.
# 
# Instead of calling the executor directly (which blocks the API),
# we now dispatch a Celery task that runs in a background worker.
# The API returns immediately and the client polls for progress.

# from app.executor.runner import execute_goal
from app.tasks.agent_tasks import execute_goal_task
from app.core.settings import APP_NAME

async def run_agent(session_id: str):
    """
    Dispatches the agent execution to a Celery background worker.
    Returns immediately — execution happens asynchronously.

    The .delay() method is Celery's shorthand for sending a task
    to the queue. The worker picks it up and calls execute_goal_task(session_id).

    Args:
        session_id: The unique session identifier of the goal to execute
    """
    print(f"[{APP_NAME}] Agent service: Dispatching Celery task for session {session_id}")

    # .delay() sends the task to the Redis queue and returns immediately
    # The Celery worker picks it up asynchronously
    execute_goal_task.delay(session_id)

    print(f"[{APP_NAME}] Agent service: Task queued. API returning immediately.")
