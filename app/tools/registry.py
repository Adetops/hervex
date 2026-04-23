# registry.py is the Tool Registry - HERVES's catalogue of available tools.
# The executor consults this registry to find the right tool for each task.

# Design principle: Adding a new tool to HEREX only requires two things - writing the
# tool function and registering it here. Nothing else in the codebase needs to change.

# Each tool is registered as a callable async function mapped to a string key.
# The key matches what the planner returns in the task's "tool" field.


from typing import Callable, Dict, Optional
from app.tools.web_search import web_search
from app.tools.calculator import calculate


# Tool Registry: maps tool name strings to their async function
# The planner uses these exact string keys when assigning tools to tasks
TOOL_REGISTRY: Dict[str, Callable] = {
    "web_search": web_search,
    
    # Calculator — evaluates mathematical expressions safely
    "calculator": calculate,
    
    # future tools:
    # "calculator": calculate,
    # "file_reader": read_file,
    # "email_sender": send_email,
}

def get_tool(tool_name: str) -> Optional[Callable]:
    """
    Looks up a tool by name in the registry.
    Returns None if the tool doesn't exist - executor
    handles the None case gracefully rather than crashing.
    
    Args:
        tool_name: The string key of the tool to retrieve
    
    Returns:
        The tool's async callable function or None if not found.
    """
    
    return TOOL_REGISTRY.get(tool_name)


def list_available_tools() -> list:
    """
    Returns a list of all registered tool names.
    Used by the planner system prompt to tell the LLM
    which tools are available for task assignment.
    
    Returns:
        A list of tool name strings
    """
    
    return list(TOOL_REGISTRY.keys())
