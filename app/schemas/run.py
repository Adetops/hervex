# run.py defines pydantic schemas for execution run responses
# It gives the client a full picture of what happened during agent exec

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.enums.status import GoalStatus
from app.schemas.task import TaskResponse


class RunStatusResponse(BaseModel):
    """
    Represents the full execution status of a goal run
    Returned when client polls for progress on a submitted goal
    """
    
    session_id: str
    goal: str
    status: GoalStatus
    tasks: List[TaskResponse]
    final_result: Optional[str]
    created_at: datetime
    updated_at: datetime
    
