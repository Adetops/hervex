# The brain of HERVEX. It receives a goals, sends it to
# planner.py — updated for Phase 5
# Planner prompt now includes rag_search tool with clear guidance
# on when to use curriculum search vs internet search.
# The priority rule is critical: always search school materials
# first before going to the internet.

from groq import Groq
import json
import uuid
from typing import List
from loguru import logger
from app.core.config import settings
from app.core.settings import (
    LLM_PLANNER_MODEL, LLM_MAX_TOKENS,
    MAX_TASKS_PER_GOAL, APP_NAME
)
from app.db.documents.task_document import TaskDocument
from app.tools.registry import list_available_tools

_client = Groq(api_key=settings.SECRET_GROQ_KEY)


def _build_planner_prompt() -> str:
    """
    Builds the planner system prompt dynamically.
    Pulls the current tool list from the registry and includes
    specific guidance on tool selection priority for education.

    The tool priority rules are critical for curriculum integrity:
    rag_search must always be attempted before web_search
    for any academic or curriculum-related question.

    Returns:
        A formatted system prompt string
    """
    available_tools = list_available_tools()
    tools_str = ", ".join(available_tools) + ", none"

    return f"""
You are HERVEX, an autonomous AI education agent planner.

Your job is to receive a goal from a student or lecturer and break it
into a clear, ordered list of executable tasks.

TOOL SELECTION RULES — follow these strictly:
1. For any question about curriculum, course content, textbooks,
   lecture notes, schemes of work, or academic topics:
   → Use 'rag_search' FIRST to search school materials
   → Only use 'web_search' if rag_search returns "NOT FOUND"

2. For general research not tied to curriculum content:
   → Use 'web_search'

3. For mathematical calculations:
   → Use 'calculator'

4. For reasoning, writing, summarising, or structuring content:
   → Use 'none' (LLM reasoning only)

Available tools: {tools_str}

Rules:
- Each task must be a single, concrete action
- Maximum {MAX_TASKS_PER_GOAL} tasks
- Always search school materials before the internet
- Return ONLY valid JSON — no explanation, no markdown, no preamble

Response format:
{{
  "tasks": [
    {{
      "description": "what to do in this task",
      "tool": "rag_search, web_search, calculator, or none"
    }}
  ]
}}
"""


async def plan_goal(goal: str) -> List[dict]:
    """
    Sends the goal to Groq LLM and returns a structured task list.
    The planner prompt is built dynamically to always reflect
    the current tool registry and education-specific tool rules.

    Args:
        goal: The raw goal string submitted by the student or lecturer

    Returns:
        A list of task dictionaries built by TaskDocument.create()

    Raises:
        ValueError: If the LLM returns an invalid or unparseable response
    """
    logger.info(f"[{APP_NAME}] Planner: Planning goal — {goal[:80]}...")

    response = _client.chat.completions.create(
        model=LLM_PLANNER_MODEL,
        max_tokens=LLM_MAX_TOKENS,
        messages=[
            {
                "role": "system",
                "content": _build_planner_prompt()
            },
            {
                "role": "user",
                "content": f"Goal: {goal}"
            }
        ]
    )

    raw_response = response.choices[0].message.content

    try:
        parsed = json.loads(raw_response)
        raw_tasks = parsed.get("tasks", [])
    except json.JSONDecodeError:
        raise ValueError(
            f"Planner received invalid JSON from Groq: {raw_response}"
        )

    tasks = []
    for raw_task in raw_tasks:
        task = TaskDocument.create(
            task_id=str(uuid.uuid4()),
            description=raw_task.get("description", ""),
            tool=raw_task.get("tool") if raw_task.get("tool") != "none" else None
        )
        tasks.append(task)

    logger.info(
        f"[{APP_NAME}] Planner: Generated {len(tasks)} tasks"
    )
    return tasks
