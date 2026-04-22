# runs.py handles the status endpoint.
# After submitting a goal, the client uses this endpoint
# to poll for progress — checking which tasks are done,
# which failed, and what the final result is.

from fastapi import APIRouter, HTTPException
from app.schemas.run import RunStatusResponse
from app.schemas.task import TaskResponse
from app.db.collections.goals import get_goal_with_tasks

router = APIRouter(prefix="/runs", tags=["Runs"])

@router.get("/{session_id}", response_model=RunStatusResponse)
async def get_run_status(session_id: str):
    """
    Returns the full execution status of a goal run.
    When status is COMPLETED, final_result contains
    HERVEX's complete synthesized response to the original goal.

    The client flow is:
    1. POST /goals/ — submit goal, get session_id back immediately
    2. GET /runs/{session_id} — poll until status is COMPLETED
    3. Read final_result from the response

    Args:
        session_id: The session ID returned when the goal was submitted
    """
    goal_doc = await get_goal_with_tasks(session_id)

    if not goal_doc:
        raise HTTPException(
            status_code=404,
            detail=f"No run found for session ID: {session_id}"
        )

    # Convert embedded task dictionaries into TaskResponse schemas
    tasks = [TaskResponse(**task) for task in goal_doc.get("tasks", [])]

    return RunStatusResponse(
        session_id=goal_doc["session_id"],
        goal=goal_doc["goal"],
        status=goal_doc["status"],
        tasks=tasks,
        final_result=goal_doc.get("final_result"),
        created_at=goal_doc["created_at"],
        updated_at=goal_doc["updated_at"]
    )
