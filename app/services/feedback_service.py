# feedback_service.py orchestrates feedback recording.
# Sits between the router and the database layer.
# Automatically flags low-rated responses for review.
# This is the improvement loop — poor responses get reviewed
# and the retrieval or prompting is improved for that institution.

import uuid
from datetime import datetime, timezone
from loguru import logger
from app.db.collections.feedback import insert_feedback, REVIEW_THRESHOLD
from app.db.collections.goals import get_goal_by_session
from app.enums.status import FeedbackRating
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.core.settings import APP_NAME

async def record_feedback(payload: FeedbackRequest) -> FeedbackResponse:
    """
    Records student or lecturer feedback for a completed run.
    Automatically flags responses rated 1 or 2 for review.

    Args:
        payload: FeedbackRequest with run_id, rating, and optional comment

    Returns:
        FeedbackResponse confirming the feedback was recorded

    Raises:
        ValueError: If the run_id does not exist
    """
    # Verify the run exists before recording feedback
    goal_doc = await get_goal_by_session(payload.run_id)
    if not goal_doc:
        raise ValueError(
            f"No run found for run_id: {payload.run_id}"
        )

    feedback_id = str(uuid.uuid4())

    # Automatically flag poor responses for review
    # Rating of 1 (very poor) or 2 (poor) triggers the flag
    flagged = payload.rating <= REVIEW_THRESHOLD

    feedback_doc = {
        "feedback_id": feedback_id,
        "run_id": payload.run_id,
        "institution_id": payload.institution_id,
        "rating": payload.rating,
        "comment": payload.comment,
        "user_type": payload.user_type,
        "flagged_for_review": flagged,
        "goal": goal_doc.get("goal", ""),
        "final_result_preview": (
            goal_doc.get("final_result", "")[:200]
            if goal_doc.get("final_result") else None
        ),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    await insert_feedback(feedback_doc)

    if flagged:
        logger.warning(
            f"[{APP_NAME}] Feedback: Run {payload.run_id} flagged "
            f"for review — rating: {payload.rating}"
        )

    return FeedbackResponse(
        feedback_id=feedback_id,
        run_id=payload.run_id,
        rating=payload.rating,
        flagged_for_review=flagged,
        message=(
            "Thank you for your feedback. "
            "This response has been flagged for review."
            if flagged else
            "Thank you for your feedback."
        ),
        created_at=datetime.now(timezone.utc).isoformat()
    )
