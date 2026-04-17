# celery_app.py configures the Celery application for HERVEX.
# Celery is a distributed task queue that allows functions to run
# asynchronously in background worker processes.
#
# How it works in HERVEX:
# 1. API receives a goal and returns immediately
# 2. API sends the execution job to Celery via Redis (the broker)
# 3. A Celery worker process picks up the job from Redis
# 4. Worker runs the full executor pipeline in the background
# 5. Client polls /runs/{session_id} to check progress
#
# broker: Redis channel where task messages are sent and received
# backend: Redis store where Celery saves task completion results

from celery import Celery
from app.core.config import settings

# Initialize Celery with Redis as both broker and backend
# broker: where tasks are queued (Redis list)
# backend: where task results are stored (Redis hash)
celery_app = Celery(
    "hervex",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Celery configuration
celery_app.conf.update(
    # Tell Celery where to find task functions
    # All tasks in app/tasks/ will be auto-discovered
    include=["app.tasks.agent_tasks"],

    # Serialize task arguments and results as JSON
    # More readable and debuggable than default pickle
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Timezone configuration
    timezone="UTC",
    enable_utc=True,

    # Worker configuration
    # prefetch_multiplier=1 means each worker takes one task at a time
    # Prevents one slow task from blocking others in the queue
    worker_prefetch_multiplier=1,

    # Task acknowledgement — mark task as done only after completion
    # Prevents task loss if the worker crashes mid-execution
    task_acks_late=True,
)
