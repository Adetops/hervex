# task_document.py defines the shape of a single task
# as stored in a goal document in MongoDB

from datetime import datetime, timezone
from typing import Optional
from app.enums.status import TaskStatus


class TaskDocument:
    """
    Represents a single task within a goal's task list
    embedded inside the GoalDocument's 'tasks' array.
    """
    
    @staticmethod
    def create(task_id: str, description: str, tool: Optional[str] = None) -> dict:
        """
        Builds a new task document ready for embedding in a goal
        
        Args:
            task_id: Unique identifier for current task within the session
            description: What the executor needs to do for this task
            tool: The tool the executor should use (e.g, web search, etc)
                    None if the task requires only LLM reasoning.
        
        Returns:
            A dictionary representing the task document 
        """
        return {
            "task_id": task_id,
            "description": description,
            "tool": tool,
            "status": TaskStatus.PENDING,
            "result": None,     # populated by executor after completion
            "error": None,      # populated if the task fails
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
