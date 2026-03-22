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

Rules:
- Each task must be a single, concrete action.
- Specify which tool to use for each task if applicable
- Available tools: web search, none [for reasoning-only task]
- Return valid JSON only - no explanation, no markdown, no preamble
- Maximum {max_tasks} tasks

Response format:
{{
    "tasks": [
        {{
            "description": "what to do in this task",
            "tool": "web_search or none"
        }}
    ]
}}
""".format(max_tasks=MAX_TASKS_PER_GOAL)

async def plan_goal(goal: str) -> List[dict]:
    """
    Sends the goal to Claude and returns a strctured list of tasks.
    
    Args:
        goal: The raw goal string submitted by client
    
    Returns:
        A list of task dictionaries built by TaskDocument.create()
        
    Raises:
        ValueError: if Claude returns an invalid or unparseable response.
    """
    
    # sending goal to Claude with the planner system prompt
    # using claude-sonnet cause of its strong instruction-following ability
    message = client.messages.create(
        model=LLM_MODEL,
        max_tokens=LLM_MAX_TOKENS,
        system=PLANNER_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Goal: {goal}"
            }
        ]
    )
    
    # extract raw text response from Claude
    raw_response = message.content[0].text
    
    try:
        # parse claude JSON response into a dict
        parsed = json.loads(raw_response)
        raw_tasks = parsed.get("tasks", [])
    except json.JSONDecodeError:
        raise ValueError(f"Planner received invalid JSON from Claude: {raw_response}")
    
    # convert raw task dict into structure TaskDocument
    # Each task gets a unique ID for tracking through the executor
    tasks = []
    for raw_task in raw_tasks:
        task = TaskDocument.create(
            task_id=str(uuid.uuid4()),
            description=raw_task.get("description", ""),
            tool=raw_task.get("tool") if raw_task.get("tool") != "none" else None
        )
        tasks.append(task)
    
    return tasks
        
