# The brain of HERVEX. It receives a goals, sends it to
# The system prompt now pulls available tools dynamically from the registry
# so the planner always knows exactly which tools HERVEX can use.
# Adding a new tool to the registry automatically updates the planner.


from groq import Groq
import json, uuid
from typing import List
from app.core.config import settings
from app.core.settings import LLM_MAX_TOKENS, LLM_PLANNER_MODEL, MAX_TASKS_PER_GOAL
from app.db.documents.task_document import TaskDocument
from app.tools.registry import list_available_tools


# Initialize Groq client with API key from settings
# Groq's client interface mirrors OpenAI's — messages, system, model
client = Groq(api_key=settings.SECRET_GROQ_KEY)
# client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

def _build_planner_prompt() -> str:
    """
    Builds the planner system prompt dynamically.
    Pulls the current tool list from the registry so the prompt
    always reflect what HERVEX can do.
    
    Returns:
        A formatted system prompt string
    """
    
    # Get live tool list from registry
    available_tools = list_available_tools()
    
    # Format as comma-separated string for the prompt
    tools_str = ", ".join(available_tools) + ", none"
    
    return f"""
    You are HERVEX, an autonomus AI agent planner.

    Your job is to receive a goal, break it down into a clear, ordered list of executable tasks.

    Rules:
    - Each task must be a single, concrete action.
    - Specify which tool to use for each task if applicable
    - Available tools: {tools_str}
    - Use "none" for reasoning-only tasks that doesn't need external data
    - Return valid JSON only - no explanation, no markdown, no preamble
    - Maximum {MAX_TASKS_PER_GOAL} tasks

    Response format:
    {{
        "tasks": [
            {{
                "description": "what to do in this task",
                "tool": "web_search or none"
            }}
        ]
    }}
    """

async def plan_goal(goal: str) -> List[dict]:
    """
    Sends the goal to Groq LLM and returns a strctured list of tasks.
    The planner prompt is built dynamically to reflect current tool availabiity.
    
    Args:
        goal: The raw goal string submitted by client
    
    Returns:
        A list of task dictionaries built by TaskDocument.create()
        
    Raises:
        ValueError: if the LLM returns an invalid or unparseable response.
    """
    
    # try:
    #     print(f"Verified Length: {len(settings.SECRET_GROQ_KEY)}")
    #     # A simple, cheap call to list models to verify the key works
    #     client.models.list()
    #     print("Groq API Key Verified.")
    # except Exception as e:
    #     print(f"CRITICAL: Groq API Key is invalid at the server level: {e}")

    # Groq uses the same chat completions format as OpenAI
    # system prompt goes in the system role message
    # goal goes in the user role message
    response = client.chat.completions.create(
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

    # Extract the raw text response from the LLM
    raw_response = response.choices[0].message.content

    try:
        # Parse the JSON response into a Python dictionary
        parsed = json.loads(raw_response)
        raw_tasks = parsed.get("tasks", [])
    except json.JSONDecodeError:
        raise ValueError(f"Planner received invalid JSON from Groq: {raw_response}")

    # Convert raw task dictionaries into structured TaskDocuments
    tasks = []
    for raw_task in raw_tasks:
        task = TaskDocument.create(
            task_id=str(uuid.uuid4()),
            description=raw_task.get("description", ""),
            tool=raw_task.get("tool") if raw_task.get("tool") != "none" else None
        )
        tasks.append(task)

    return tasks
