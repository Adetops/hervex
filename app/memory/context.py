# context.py manages HERVEX's short-term memory using Redis.
# Each agent session gets its own memory space in Redis,
# keyed by session_id.
#
# How it works:
# - After each task completes, its result is written to Redis
# - Before each reasoning task runs, all previous results are read
# - The accumulated results are passed to the LLM as context
# - Redis keys expire after 24 hours to prevent memory buildup
#
# Why Redis and not MongoDB for this?
# Redis is an in-memory store — reads and writes are microseconds.
# Between tasks in a running session, speed matters more than
# persistence. MongoDB is for long-term storage after the run ends.

import json
from loguru import logger
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.settings import APP_NAME

# TTL (time to live) for session memory in Redis
# After 24 hours, the session context is automatically deleted
SESSION_MEMORY_TTL = 86400  # 24 hours in seconds

# Initialize async Redis client
# redis.asyncio is the async version of the redis client
# compatible with FastAPI and Celery's async context
_redis_client = aioredis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True  # Return strings instead of bytes
)

def _memory_key(session_id: str) -> str:
    """
    Builds the Redis key for a session's memory.
    Namespaced under 'hervex:memory:' to avoid key collisions
    with other Redis data (e.g. Celery's own keys).

    Args:
        session_id: The unique session identifier

    Returns:
        A namespaced Redis key string
    """
    return f"hervex:memory:{session_id}"

async def store_task_result(session_id: str, task_description: str, result: str):
    """
    Stores a completed task's result in Redis session memory.
    Called by the executor after each successful task completion.

    Results are stored as a JSON list — each entry is a dict
    with the task description and its result. This preserves
    the order and context of what was done and what was found.

    Args:
        session_id: The unique session identifier
        task_description: What the task was — gives context to the result
        task_result: The output of the task execution
    """
    key = _memory_key(session_id)

    # Load existing memory or start fresh
    existing = await _redis_client.get(key)
    memory = json.loads(existing) if existing else []

    # Append the new task result to memory
    memory.append({
        "task": task_description,
        "result": result
    })

    # Save back to Redis with TTL refresh
    # json.dumps converts the list to a string for Redis storage
    await _redis_client.setex(
        key,
        SESSION_MEMORY_TTL,
        json.dumps(memory)
    )

    logger.info(f"[{APP_NAME}] Memory: Stored result for task in session {session_id}. "
          f"Total memory entries: {len(memory)}")

async def get_session_context(session_id: str, max_chars: int = 3000) -> str:
    """
    Retrieves all accumulated task results for a session, truncates to prevent exceeding token limits
    and formats them as a readable context string for the LLM.

    Called by the executor before running a reasoning-only task
    so the LLM has full awareness of what has already been done.

    Args:
        session_id: The unique session identifier
        max_chars: Maximum characters of context to return (default=3000)

    Returns:
        A formatted string of all previous task results,
        or an empty string if no memory exists yet
    """
    key = _memory_key(session_id)
    existing = await _redis_client.get(key)

    if not existing:
        return ""

    memory = json.loads(existing)

    if not memory:
        return ""

    # Format memory as a numbered list for clear LLM consumption
    # Each entry shows what was done and what was found
    formatted_entries = []
    for i, entry in enumerate(memory, 1):
        # Truncate individual result to avoid bloating context
        result_preview = entry['result'][:500] + "..." \
            if len(entry['result']) > 500 else entry['result']

        formatted_entries.append(
            f"Step {i}:\n"
            f"Task: {entry['task']}\n"
            f"Result: {result_preview}\n"
        )

    context = "Previous task results:\n\n" + "\n".join(formatted_entries)
    # Final safety truncation on the entire context string
    if len(context) > max_chars:
        context = context[:max_chars] + "\n...[context truncated]"
        
    return context

async def clear_session_memory(session_id: str):
    """
    Deletes all memory for a session from Redis.
    Called after the aggregator completes its final response
    since results are now persisted in MongoDB.

    Args:
        session_id: The unique session identifier
    """
    key = _memory_key(session_id)
    await _redis_client.delete(key)
    logger.info(f"Memory: Cleared session memory for {session_id}")
