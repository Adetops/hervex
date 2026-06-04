# runs.py handles the status endpoint.
# After submitting a goal, the client uses this endpoint
# to poll for progress — checking which tasks are done,
# which failed, and what the final result is.
# GET /v1/result/{run_id} — full result with tasks and final answer
# GET /v1/status/{run_id} — lightweight status only for polling

from fastapi import APIRouter, HTTPException
from loguru import logger
from app.schemas.run import RunStatusResponse, RunStatusOnlyResponse
from app.schemas.task import TaskResponse
from app.db.collections.goals import get_goal_with_tasks, get_goal_status_only
from app.db.collections.runs import get_run_by_session
from app.core.settings import APP_NAME

router = APIRouter(prefix="/v1", tags=["Runs"])

@router.get("/result/{run_id}", response_model=RunStatusResponse)
async def get_result(run_id: str):
    """
    Retrieve the full result of a goal run.

    Returns the complete response including all task results
    and the final synthesized answer when status is 'completed'.

    Poll this endpoint after submitting a goal. When status
    changes to 'completed', the final_result field contains
    HERVEX's complete answer to your goal.
    """
    goal_doc = await get_goal_with_tasks(run_id)

    if not goal_doc:
        raise HTTPException(
            status_code=404,
            detail=f"No run found for run_id: {run_id}"
        )

    tasks = [
        TaskResponse(**task)
        for task in goal_doc.get("tasks", [])
    ]

    return RunStatusResponse(
        run_id=goal_doc["session_id"],    # Map internal session_id to run_id
        goal=goal_doc["goal"],
        status=goal_doc["status"],
        institution_id=goal_doc.get("institution_id", "default"),
        tasks=tasks,
        final_result=goal_doc.get("final_result"),
        created_at=goal_doc["created_at"],
        updated_at=goal_doc["updated_at"]
    )


@router.get("/status/{run_id}", response_model=RunStatusOnlyResponse)
async def get_status(run_id: str):
    """
    Retrieve lightweight status for a goal run.

    Returns status, task counts, and timestamps only —
    without the full task list or final result.

    Use this endpoint for efficient polling to avoid
    the overhead of loading full task results on every check.
    Switch to GET /v1/result/{run_id} only when you need
    the complete response.
    """
    goal_doc = await get_goal_status_only(run_id)
    run_doc = await get_run_by_session(run_id)

    if not goal_doc:
        raise HTTPException(
            status_code=404,
            detail=f"No run found for run_id: {run_id}"
        )

    return RunStatusOnlyResponse(
        run_id=goal_doc["session_id"],
        status=goal_doc["status"],
        institution_id=goal_doc.get("institution_id", "default"),
        task_count=run_doc.get("task_count", 0) if run_doc else 0,
        completed_tasks=run_doc.get("completed_tasks", 0) if run_doc else 0,
        created_at=goal_doc["created_at"],
        updated_at=goal_doc["updated_at"]
    )
