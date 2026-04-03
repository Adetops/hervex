# agent_service.py orchestrates the full agent execution flow.
# It is called after goal_service.py has saved the goal and tasks.
# It triggers the executor and bridges the service layer
# with the executor layer.
#
# Later, Celery will take over from here -
# execution will be handed off to a background worker instead
# of running synchronously.

from app.executor.runner import execute_goal
from app.core.settings import APP_NAME

async def run_agent(session_id: str):
    """
    Triggers the executor for a given session.
    Currently runs synchronously — will become async via Celery in Phase 5.

    Args:
        session_id: The unique session identifier of the goal to execute
    """
    print(f"[{APP_NAME}] Agent service: Triggering executor for session {session_id}")
    await execute_goal(session_id)
