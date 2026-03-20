# goal_document.py defines the shape of a goal as stored in MongoDB

from datetime import datetime, timezone
from typing import Optional
from app.enums.status import GoalStatus, Priority


class GoalDocument:
    """
    Represents a goal document in the MongoDB 'goals' collection.
    Not a pydantic model - used as a plain dictionary builder to keep
    MongoDB operations explicit and readable
    """
    
    @staticmethod
    def create(session_id: str, goal: str, priority: Priority) -> dict:
        """
        Builds a new goal document to insert into MongoDB
        
        Args:
            session_id: Unique identifier for current agent session
            goal: The goal string submitted by the user/client
            priority: Goal execution priority level
        
        Returns:
            A dictionary that represents MongoDB document
        """
        return {
            "session_id": session_id,
            "goal": goal,
            "priority": priority,
            "status": GoalStatus.RECEIVED,
            "tasks": [],               # populated by the planner in Phase 2
            "final_result": None,      # populated by the Result Aggregator in Phase 7
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
