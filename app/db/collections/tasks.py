# tasks.py contains database operations for individual tasks
# embedded inside goal documents.
# Tasks are not a separate collection — they live inside the goal document.
# These operations use MongoDB's positional operator ($) to update
# a specific task within the goal's tasks array.

from datetime import datetime, timezone
from typing import Optional
from app.db.connection import get_database
from app.enums.status import TaskStatus

async def update_task_status(
    session_id: str,
    task_id: str,
    status: TaskStatus,
    result: Optional[str] = None,
    error: Optional[str] = None
):
    """
    Updates the status, result, and error of a specific task
    inside the goal document's tasks array.

    Uses MongoDB's positional operator to target the exact task
    without replacing the entire array.

    Args:
        session_id: The parent goal's session identifier
        task_id: The unique identifier of the task to update
        status: The new TaskStatus value
        result: The output of the task if successful
        error: The error message if the task failed
    """
    db = get_database()

    # Build the update fields dynamically
    # Only include result and error if they are provided
    update_fields = {
        "tasks.$.status": status,
        "tasks.$.updated_at": datetime.now(timezone.utc).isoformat()
    }

    if result is not None:
        update_fields["tasks.$.result"] = result
    if error is not None:
        update_fields["tasks.$.error"] = error

    # The positional operator $ matches the task whose task_id
    # matches the filter condition
    await db.goals.update_one(
        {
            "session_id": session_id,
            "tasks.task_id": task_id
        },
        {"$set": update_fields}
    )
