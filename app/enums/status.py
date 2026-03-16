from enum import Enum

class GoalStatus(str, Enum):
    RECEIVED = "received"
    PLANNING = "planning"
    EXECUTING = "executing"
    AGGREGATING = "aggregating"
    COMPLETED = "completed"
    FAILED = "failed"
    

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    

class Priority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
