# runs.py contains all database operations for the runs collection.
# The executor writes to this collection to track progress.
# The status endpoint reads from it to report back to the client.

from datetime import datetime, timezone
from typing import Optional
from app.db.connection import get_database
from app.enums.status import GoalStatus

async def insert_run(run_document: dict) -> str:
    """
    Inserts a new execution run document into the 'runs' collection.

    Args:
        run_document: A dictionary built by RunDocument.create()

    Returns:
        The session_id of the inserted run
    """
    db = get_database()
    await db.runs.insert_one(run_document)
    return run_document["session_id"]

async def get_run_by_session(session_id: str) -> Optional[dict]:
    """
    Retrieves an execution run by its session ID.

    Args:
        session_id: The unique session identifier

    Returns:
        The run document or None if not found
    """
    db = get_database()
    return await db.runs.find_one({"session_id": session_id})

async def increment_completed_tasks(session_id: str):
    """
    Increments the completed task counter on a run document.
    Called by the executor after each successful task.

    Args:
        session_id: The unique session identifier
    """
    db = get_database()
    await db.runs.update_one(
        {"session_id": session_id},
        {"$inc": {"completed_tasks": 1}}
    )

async def increment_failed_tasks(session_id: str):
    """
    Increments the failed task counter on a run document.
    Called by the executor when a task fails but execution continues.

    Args:
        session_id: The unique session identifier
    """
    db = get_database()
    await db.runs.update_one(
        {"session_id": session_id},
        {"$inc": {"failed_tasks": 1}}
    )

async def complete_run(session_id: str, status: GoalStatus):
    """
    Marks a run as completed or failed and records the completion time.
    Called by the executor after all tasks have been processed.

    Args:
        session_id: The unique session identifier
        status: GoalStatus.COMPLETED or GoalStatus.FAILED
    """
    db = get_database()
    await db.runs.update_one(
        {"session_id": session_id},
        {"$set": {
            "status": status,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
