# settings.py holds hervex constants and configurations that are not sensitive
# enough to be in .env file but must be consistent across entire codebase

from app.core.config import settings


# LLM model to use for all Claude API calls
# LLM_MODEL = "claude-sonnet-4-20250514"

# Model for planning and task reasoning
LLM_PLANNER_MODEL = "llama-3.3-70b-versatile"

# Model for final response aggregation
# Using the same model keeps things consistent
# Swap to llama-3.1-8b-instant if you hit rate limits
LLM_AGGREGATOR_MODEL = "llama-3.3-70b-versatile"

# Maximum tokens claude can return in a single response
LLM_MAX_TOKENS = 8096

# Maximum number of tasks the planner can generate for a goal
MAX_TASKS_PER_GOAL = 6

# App name to be used in logs and API responses
APP_NAME = "HERVEX"
