# result.py is the final stage of the HERVEX pipeline.
## result.py — updated
# Aggregator system prompt now handles source attribution.
# Results labelled FROM SCHOOL MATERIALS are cited as curriculum.
# Results labelled from internet search are cited as web sources.
# This satisfies UR-06 and UR-07 from the SRS.

from groq import Groq
from loguru import logger
from app.core.config import settings
from app.core.settings import LLM_AGGREGATOR_MODEL, LLM_MAX_TOKENS, APP_NAME
from app.db.collections.goals import get_goal_with_tasks, update_goal_status
from app.enums.status import GoalStatus, TaskStatus

_llm_client = Groq(api_key=settings.GROQ_API_KEY)

async def aggregate_results(session_id: str) -> str:
    """
    Collects all completed task results and synthesizes them
    into a final coherent response with proper source attribution.

    Phase 5 addition: The system prompt now instructs the LLM
    to maintain clear source labelling throughout the final response —
    distinguishing school materials from internet sources.

    Args:
        session_id: The unique session identifier

    Returns:
        The final synthesized response string
    """
    goal_doc = await get_goal_with_tasks(session_id)

    if not goal_doc:
        raise ValueError(
            f"Aggregator: Goal not found for session {session_id}"
        )

    original_goal = goal_doc["goal"]
    tasks = goal_doc.get("tasks", [])

    completed_tasks = [
        task for task in tasks
        if task.get("status") == TaskStatus.COMPLETED
        and task.get("result")
    ]

    if not completed_tasks:
        raise ValueError(
            f"Aggregator: No completed tasks for session {session_id}"
        )

    logger.info(
        f"[{APP_NAME}] Aggregator: Synthesizing {len(completed_tasks)} "
        f"results for session {session_id}"
    )

    synthesis_prompt = _build_synthesis_prompt(original_goal, completed_tasks)

    response = _llm_client.chat.completions.create(
        model=LLM_AGGREGATOR_MODEL,
        max_tokens=LLM_MAX_TOKENS,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are HERVEX, an autonomous AI education agent "
                    "delivering a final response to a student or lecturer.\n\n"
                    "SOURCE ATTRIBUTION RULES — follow strictly:\n"
                    "1. Content labelled [FROM SCHOOL MATERIALS] must be cited "
                    "as 'From your school materials' in the response\n"
                    "2. Content labelled [FROM INTERNET] must be cited "
                    "as 'From internet search' in the response\n"
                    "3. Never present internet content as curriculum content\n"
                    "4. If school materials say 'NOT FOUND', clearly tell the "
                    "student this topic is not in their uploaded school materials\n"
                    "5. Write in clear, academic language appropriate for "
                    "the educational level\n"
                    "6. Structure the response clearly with headings where appropriate"
                )
            },
            {
                "role": "user",
                "content": synthesis_prompt
            }
        ]
    )

    final_result = response.choices[0].message.content

    await _save_final_result(session_id, final_result)
    await update_goal_status(session_id, GoalStatus.COMPLETED)

    logger.info(
        f"[{APP_NAME}] Aggregator: Session {session_id} completed."
    )

    return final_result


def _build_synthesis_prompt(goal: str, completed_tasks: list) -> str:
    """
    Builds the synthesis prompt combining original goal
    with all task results and their source labels.
    """
    task_results_text = ""
    for i, task in enumerate(completed_tasks, 1):
        task_results_text += (
            f"Task {i}: {task['description']}\n"
            f"Result: {task['result']}\n\n"
        )

    return (
        f"Original Goal:\n{goal}\n\n"
        f"Completed Task Results:\n\n{task_results_text}"
        f"Synthesize all results into one complete, well-structured "
        f"response that directly addresses the original goal. "
        f"Maintain clear source attribution throughout."
    )


async def _save_final_result(session_id: str, final_result: str):
    """
    Saves the final result to the goal document in MongoDB.
    """
    from datetime import datetime
    from app.db.connection import get_database

    db = get_database()
    await db.goals.update_one(
        {"session_id": session_id},
        {"$set": {
            "final_result": final_result,
            "updated_at": datetime.utcnow()
        }}
    )
