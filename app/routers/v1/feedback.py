# v1/feedback.py — versioned feedback endpoint
# POST /v1/feedback
# Students and lecturers rate responses after receiving them.
# Poor ratings trigger automatic flagging for HERVEX team review.

from fastapi import APIRouter, HTTPException, Request
from loguru import logger
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.services.feedback_service import record_feedback
from app.core.rate_limiter import limiter
from app.core.settings import APP_NAME

router = APIRouter(prefix="/v1", tags=["Feedback"])

@router.post("/feedback", response_model=FeedbackResponse, status_code=201)
@limiter.limit("30/minute")
async def submit_feedback(request: Request, payload: FeedbackRequest):
    """
    Submit feedback for a completed HERVEX response.

    Rate the response from 1 (very poor) to 5 (excellent).
    Ratings of 1 or 2 are automatically flagged for review
    so the HERVEX team can identify and improve poor responses.

    Include an optional comment to help identify what went wrong
    or what was particularly helpful.
    """
    logger.info(
        f"[{APP_NAME}] POST /v1/feedback — run: {payload.run_id} "
        f"— rating: {payload.rating}"
    )

    try:
        return await record_feedback(payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"[{APP_NAME}] Feedback recording failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to record feedback: {str(e)}"
        )
