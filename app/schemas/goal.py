from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from app.enums.status import GoalStatus, Priority


class GoalRequest(BaseModel):
    goal: str = Field(..., min_length=10, description="The goal for the agent to accomplish")
    priority: Optional[Priority] = Field(default=Priority.NORMAL)


class GoalResponse(BaseModel):
    session_id: str
    goal: str
    status: GoalStatus
    priority: Priority
    created_at: datetime
    message: str
    
