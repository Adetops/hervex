# status.py — updated for education branch
# Added DocumentStatus for tracking document ingestion lifecycle

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


class DocumentStatus(str, Enum):
    """
    Tracks the lifecycle of an uploaded document through ingestion.
    UPLOADED: file received, not yet processed
    PROCESSING: chunking and embedding in progress
    INDEXED: successfully stored in Pinecone, ready for RAG queries
    FAILED: ingestion failed at some stage
    """
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"
