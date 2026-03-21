# goals.py contains all database operations for the goals collection.
# Services call this, not the other way round

from datetime import datetime, timezone
from typing import Optional
from app.db.connection import get_database
from app.enums.status import GoalStatus


async def insert_goal(goal_document: dict) -> str:
    """
    Insert a new goal document into the goal's collection
    
    Args:
        goal_document: A dictionary built by GoalDocument.create()
    
    Returns:
        The session_id of the inserted goal
    """
    
    db = get_database()
    await db.goals.insert_one(goal_document)
    return (goal_document["session_id"])


async def get_goal_by_session(session_id: str) -> Optional[dict]:
    """
    Retrieves a goal document by its session id
    
    Args:
        session_id: Unique session ID of a goal
        
    Returns:
        The goal document or None if not found.
    """
    
    db = get_database()
    return (await db.goals.find_one({"session_id": session_id}))


async def update_goal_status(session_id: str, status: GoalStatus):
    """
    Updates the status of a goal and updated_at timestamp
    
    Args:
        session_id: unique identifier of the goal
        status: The new goal status value
    """
    
    db = get_database()
    await db.goals.update_one(
        {"session_id": session_id},
        {"$set": {
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    

async def update_goal_tasks(session_id: str, tasks: list):
    """
    Saves generated task list into goal document, called by the
    Planner after breaking down the goal.
    
    Args:
        session_id: unique session identifier
        tasks: List of task dictionaries built by TaskDocument.create()
    """
    
    db = get_database()
    await db.goals.update_one(
        {"session_id": session_id},
        {"$set": {
            "tasks": tasks,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
