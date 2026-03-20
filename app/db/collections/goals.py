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


async 
    
