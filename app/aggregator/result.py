# result.py is the final stage of the HERVEX pipeline.
# It collects all task results from MongoDB, sends them
# to the LLM with a synthesis prompt, and returns a single
# coherent response that answers the original goal.
#
# The aggregator is the only component that sees the complete
# picture — it has access to every task result from the entire
# session and uses them to construct the final deliverable.
#
# Why send to LLM again here?
# Individual task results are raw and disconnected.
# The LLM's job in aggregation is to weave them into one
# coherent, well-structured response the client can actually use.

from groq import Groq
from app.core.config import settings
from app.core.settings import LLM_AGGREGATOR_MODEL, LLM_MAX_TOKENS, APP_NAME
from app.db.collections.goals import get_goal_with_tasks, update_goal_status
from app.enums.status import GoalStatus, TaskStatus

# Initialize Groq client for aggregation
# Uses LLM_AGGREGATOR_MODEL which can be upgraded independently
# of the planner model in settings.py when quality needs differ
_llm_client = Groq(api_key=settings.SECRET_GROQ_KEY)

async def aggregate_results(session_id: str) -> str:
    """
    Collects all completed task results for a session,
    synthesizes them into a final coherent response via the LLM,
    and saves the result to MongoDB.

    Flow:
    1. Load goal and all tasks from MongoDB
    2. Filter for completed tasks only
    3. Build a synthesis prompt with original goal + all results
    4. Send to LLM for final response generation
    5. Save final result to MongoDB
    6. Update goal status to COMPLETED

    Args:
        session_id: The unique session identifier

    Returns:
        The final synthesized response string

    Raises:
        ValueError: If the goal is not found or has no completed tasks
    """

    # Load the full goal document including all task results
    goal_doc = await get_goal_with_tasks(session_id)

    if not goal_doc:
        raise ValueError(f"Aggregator: Goal not found for session {session_id}")

    original_goal = goal_doc["goal"]
    tasks = goal_doc.get("tasks", [])

    # Filter for only completed tasks — failed tasks are excluded
    # from the final synthesis to avoid polluting the response
    completed_tasks = [
        task for task in tasks
        if task.get("status") == TaskStatus.COMPLETED
        and task.get("result")
    ]

    if not completed_tasks:
        raise ValueError(
            f"Aggregator: No completed tasks found for session {session_id}"
        )

    print(
        f"[{APP_NAME}] Aggregator: Synthesizing {len(completed_tasks)} "
        f"task results for session {session_id}"
    )

    # Build the synthesis prompt
    synthesis_prompt = _build_synthesis_prompt(original_goal, completed_tasks)

    # Send to LLM for final coherent response
    response = _llm_client.chat.completions.create(
        model=LLM_AGGREGATOR_MODEL,
        max_tokens=LLM_MAX_TOKENS,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are HERVEX, an autonomous AI agent delivering a final response. "
                    "You have completed all required tasks and collected their results. "
                    "Your job is to synthesize everything into one clear, well-structured, "
                    "and complete response that directly addresses the original goal. "
                    "Do not reference the task steps — just deliver the final answer."
                )
            },
            {
                "role": "user",
                "content": synthesis_prompt
            }
        ]
    )

    final_result = response.choices[0].message.content

    # Persist the final result to MongoDB
    await _save_final_result(session_id, final_result)

    # Mark the goal as fully completed
    await update_goal_status(session_id, GoalStatus.COMPLETED)

    print(f"[{APP_NAME}] Aggregator: Session {session_id} completed successfully.")

    return final_result

def _build_synthesis_prompt(goal: str, completed_tasks: list) -> str:
    """
    Builds the synthesis prompt that the aggregator sends to the LLM.
    Combines the original goal with all task results in a structured format.

    Args:
        goal: The original goal string submitted by the client
        completed_tasks: List of completed task documents with results

    Returns:
        A formatted prompt string ready for LLM consumption
    """

    # Format each completed task result clearly
    task_results_text = ""
    for i, task in enumerate(completed_tasks, 1):
        task_results_text += (
            f"Task {i}: {task['description']}\n"
            f"Result: {task['result']}\n\n"
        )

    prompt = (
        f"Original Goal:\n{goal}\n\n"
        f"Completed Task Results:\n\n"
        f"{task_results_text}"
        f"Using all the above task results, deliver a complete, "
        f"well-structured final response that fully addresses the original goal."
    )

    return prompt

async def _save_final_result(session_id: str, final_result: str):
    """
    Saves the final aggregated result to the goal document in MongoDB.
    After this, the result is permanently stored and retrievable
    via the /runs/{session_id} endpoint.

    Args:
        session_id: The unique session identifier
        final_result: The synthesized response from the LLM
    """
    from datetime import datetime, timezone
    from app.db.connection import get_database

    db = get_database()
    await db.goals.update_one(
        {"session_id": session_id},
        {
            "$set": {
                # Store the final result directly on the goal document
                "final_result": final_result,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
