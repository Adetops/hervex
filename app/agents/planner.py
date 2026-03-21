# The brain of HERVEX. It receives a goals, sends it to
# Claude with a structured prompt, and parses the response
# into a list of executable tasks. No execution, planning only.

import anthropic, json, uuid
from typing import List
from app.core.config import settings
from app.core.settings import LLM_MAX_TOKENS, LLM_MODEL, MAX_TASKS_PER_GOAL
from app.db.documents.task_document import TaskDocument


client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

PLANNER_SYSTEM_PROMPT = """
You are HERVEX, an autonomus AI agent planner.

Your job is to receive a goal, break it down into a clear, ordered list of executable tasks.


"""

