# run.py defines pydantic schemas for execution run responses
# It gives the client a full picture of what happened during agent exec
# GET /v1/result/{run_id} for execution progress.

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.enums.status import GoalStatus
from app.schemas.task import TaskResponse


class RunStatusResponse(BaseModel):
    """
    Full execution status of a goal run.
    Returned when client polls /v1/result/{run_id}.
    When status is completed, final_result contains
    HERVEX's complete synthesized response.
    """
    run_id: str                    # Renamed from session_id
    goal: str
    status: GoalStatus
    institution_id: str
    tasks: List[TaskResponse]
    final_result: Optional[str]
    created_at: datetime
    updated_at: datetime

class RunStatusOnlyResponse(BaseModel):
    """
    Lightweight status-only response for GET /v1/status/{run_id}.
    Returns status without full task list or final result.
    Useful for polling without the overhead of the full response.
    """
    run_id: str
    status: GoalStatus
    institution_id: str
    task_count: int
    completed_tasks: int
    created_at: datetime
    updated_at: datetime
    
