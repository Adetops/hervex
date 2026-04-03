# run_document.py defines the shape of an execution run document in MongoDB created when executor begins
# processing a goal to track the entire lifecycle of a single agent run for auditing and debugging.

from datetime import datetime, timezone
from app.enums.status import GoalStatus


class RunDocument:
    """
    Represents an execution run document in the MongoDB 'runs' collection.
    One run is created per goal submission.
    Distinct from the goal document — the goal holds the plan,
    the run holds the execution history.
    """

    @staticmethod
    def create(session_id: str, goal: str, task_count: int) -> dict:
        """
        Builds a new run document ready for insertion into MongoDB.

        Args:
            session_id: Links this run back to its parent goal
            goal: The original goal string for quick reference
            task_count: Total number of tasks to be executed

        Returns:
            A dictionary representing the MongoDB run document
        """
        return {
            "session_id": session_id,
            "goal": goal,
            "status": GoalStatus.EXECUTING,
            "task_count": task_count,
            "completed_tasks": 0,       # Incremented by executor after each task
            "failed_tasks": 0,          # Incremented by executor on task failure
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,       # Populated when all tasks are done
            "error": None,              # Populated if the entire run fails
        }
