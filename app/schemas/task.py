# task.py defines the pydantic schemas for task-related API responses.
# These are what the API reveals to the client

from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from app.enums.status import TaskStatus


class TaskResponse(BaseModel):
    """
    Represents a single task as return by the API
    Exposes only what the client needs - internal fields stay in the document layer
    """
    
    task_id: str
    description: str
    tool: Optional[str]
    status: TaskStatus
    result: Optional[str]
    error: Optional[str]
    created_at: datetime
    updated_at: datetime
