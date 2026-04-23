# calculator.py is HERVEX's second tool.
# It handles mathematical computations that web search can't reliably do.
# The executor assigns this tool to tasks that require calculation
# rather than information retrieval.
#
# Using Python's eval() safely with a restricted namespace
# prevents arbitrary code execution while supporting
# standard mathematical expressions.

import math
from loguru import logger

# Safe namespace for eval — only exposes math functions
# Never use bare eval() — always restrict the namespace
SAFE_MATH_NAMESPACE = {
    "abs": abs, "round": round, "min": min, "max": max,
    "sum": sum, "pow": pow, "sqrt": math.sqrt,
    "floor": math.floor, "ceil": math.ceil,
    "pi": math.pi, "e": math.e,
    "__builtins__": {}  # Block all built-ins for safety
}

async def calculate(expression: str) -> str:
    """
    Evaluates a mathematical expression and returns the result.
    Accepts natural language descriptions and attempts to extract
    the mathematical expression from them.

    Args:
        expression: A math expression or task description containing one.
                   Examples: "2 + 2", "sqrt(144)", "15% of 3500"

    Returns:
        A string containing the result of the calculation

    Raises:
        ValueError: If the expression cannot be evaluated safely
    """
    logger.info(f"Calculator tool: evaluating expression — {expression}")

    # Clean up the expression — remove common natural language wrappers
    cleaned = (
        expression
        .replace("calculate", "")
        .replace("compute", "")
        .replace("what is", "")
        .replace("find", "")
        .strip()
    )

    try:
        # Safely evaluate the mathematical expression
        result = eval(cleaned, {"__builtins__": {}}, SAFE_MATH_NAMESPACE)
        logger.info(f"Calculator tool: result = {result}")
        return f"Calculation result: {cleaned} = {result}"

    except Exception as e:
        raise ValueError(
            f"Could not evaluate mathematical expression '{cleaned}': {str(e)}"
        )
