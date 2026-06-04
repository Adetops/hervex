# goal_service.py — updated
# Passes institution_id through the full creation flow
# so the goal document and executor both have it.

import uuid
from datetime import datetime, timezone
from loguru import logger
from app.db.documents.goal_document import GoalDocument
from app.db.collections.goals import (
    insert_goal,
    update_goal_status,
    update_goal_tasks
)
from app.agents.planner import plan_goal
from app.services.agent_service import run_agent
from app.enums.status import GoalStatus, Priority
from app.schemas.goal import GoalResponse
from app.core.settings import APP_NAME

async def create_goal(
    goal: str,
    priority: Priority,
    institution_id: str = "default"
) -> GoalResponse:
    """
    Handles the full goal creation and execution dispatch flow.
    Now passes institution_id so RAG searches the correct namespace.

    Args:
        goal: The raw goal string
        priority: Execution priority level
        institution_id: Institution this goal belongs to

    Returns:
        GoalResponse — client uses run_id to poll for progress
    """
    session_id = str(uuid.uuid4())

    goal_doc = GoalDocument.create(
        session_id=session_id,
        goal=goal,
        priority=priority,
        institution_id=institution_id
    )
    await insert_goal(goal_doc)
    await update_goal_status(session_id, GoalStatus.PLANNING)

    tasks = await plan_goal(goal)
    await update_goal_tasks(session_id, tasks)
    await update_goal_status(session_id, GoalStatus.EXECUTING)

    await run_agent(session_id)

    logger.info(
        f"[{APP_NAME}] Goal Service: Goal created — "
        f"run_id: {session_id} — institution: {institution_id}"
    )

    return GoalResponse(
        run_id=session_id,
        goal=goal,
        status=GoalStatus.PLANNING,
        priority=priority,
        institution_id=institution_id,
        created_at=datetime.now(timezone.utc).isoformat(),
        message=(
            f"HERVEX has planned {len(tasks)} tasks. "
            f"Execution started in background. "
            f"Poll /v1/result/{session_id} for progress."
        )
    )
