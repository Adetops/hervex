# goal_document.py — updated for Phase 5
# Added institution_id field so goals are tied to institutions
# and the executor can enforce namespace isolation during RAG.

from datetime import datetime, timezone
from typing import Optional
from app.enums.status import GoalStatus, Priority

class GoalDocument:
    """
    Represents a goal document in the MongoDB 'goals' collection.
    """

    @staticmethod
    def create(
        session_id: str,
        goal: str,
        priority: Priority,
        institution_id: str = "default"
    ) -> dict:
        """
        Builds a new goal document ready for MongoDB insertion.

        Args:
            session_id: Unique identifier for this agent session
            goal: The raw goal string submitted by the client
            priority: Execution priority level
            institution_id: Institution this goal belongs to
                           Used by executor for RAG namespace isolation

        Returns:
            A dictionary representing the MongoDB document
        """
        return {
            "session_id": session_id,
            "goal": goal,
            "priority": priority,
            "institution_id": institution_id,
            "status": GoalStatus.RECEIVED,
            "tasks": [],
            "final_result": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
