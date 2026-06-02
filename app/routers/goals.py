# goals.py — updated
# Passes institution_id from request payload to goal_service.

from fastapi import APIRouter, HTTPException, Request
from loguru import logger
from app.schemas.goal import GoalRequest, GoalResponse
from app.services.goal_service import create_goal
from app.exceptions.handlers import PlannerException
from app.core.rate_limiter import limiter
from app.core.settings import APP_NAME

router = APIRouter(prefix="/goals", tags=["Goals"])

@router.post("/", response_model=GoalResponse, status_code=201)
@limiter.limit("10/minute")
async def submit_goal(request: Request, payload: GoalRequest):
    """
    Submits a new goal to HERVEX.
    Returns a session_id immediately — execution runs in background.
    The institution_id in the payload determines which knowledge
    base HERVEX searches for curriculum content.
    """
    logger.info(
        f"[{APP_NAME}] New goal received for institution "
        f"'{payload.institution_id}': {payload.goal[:50]}..."
    )

    try:
        return await create_goal(
            goal=payload.goal,
            priority=payload.priority,
            institution_id=payload.institution_id
        )
    except ValueError as e:
        raise PlannerException(detail=str(e))
    except Exception as e:
        logger.error(f"[{APP_NAME}] Goal creation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"HERVEX encountered an error: {str(e)}"
        )
