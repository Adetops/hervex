# result_service.py orchestrates the aggregation flow.
# It sits between the Celery task layer and the aggregator,
# following the same service pattern used throughout HERVEX.
# Nothing calls the aggregator directly — it always goes through here.

from app.aggregator.result import aggregate_results
from app.core.settings import APP_NAME
from loguru import logger

async def finalize_result(session_id: str) -> str:
    """
    Triggers the aggregator for a completed session.
    Called after all tasks have been executed successfully.

    Args:
        session_id: The unique session identifier

    Returns:
        The final synthesized response string
    """
    logger.info(f"Result service: Starting aggregation for session {session_id}")
    final_result = await aggregate_results(session_id)
    logger.info(f"Result service: Aggregation complete for session {session_id}")
    return final_result
