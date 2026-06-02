# goal.py — updated for Phase 5
# Added institution_id to GoalRequest so the executor knows
# which Pinecone namespace to search for curriculum content.

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.enums.status import GoalStatus, Priority

class GoalRequest(BaseModel):
    goal: str = Field(
        ...,
        min_length=10,
        description="The goal for HERVEX to accomplish"
    )
    priority: Optional[Priority] = Field(default=Priority.NORMAL)

    # institution_id ties this goal to a specific school's knowledge base
    # Defaults to 'default' for backward compatibility
    # In production this will be derived from the API key (Phase 7)
    institution_id: Optional[str] = Field(
        default="default",
        description="Institution ID — determines which knowledge base to search"
    )

class GoalResponse(BaseModel):
    session_id: str
    goal: str
    status: GoalStatus
    priority: Priority
    institution_id: str
    created_at: datetime
    message: str
