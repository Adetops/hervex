# goals.py — updated for Phase 8
# Added rate limiting: 10 goal submissions per minute per IP.
# This prevents a single client from exhausting Groq/Tavily quotas.
# Custom exceptions replace generic try/except blocks.

from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from loguru import logger
from app.schemas.goal import GoalRequest, GoalResponse
from app.services.goal_service import create_goal
from app.exceptions.handlers import PlannerException
from app.core.rate_limiter import limiter

router = APIRouter(prefix="/goals", tags=["Goals"])

@router.post("/", response_model=GoalResponse, status_code=201)
@limiter.limit("10/minute")  # Max 10 goal submissions per minute per IP
async def submit_goal(request: Request, payload: GoalRequest):
    """
    Endpoint to submit a new goal to HERVEX.
    Rate limited to 10 requests per minute per IP address.
    Returns a session ID immediately — execution runs in background.

    Args:
        request: FastAPI request object (required by slowapi for IP extraction)
        payload: The validated goal request body
    """
    logger.info(f"New goal received: {payload.goal[:50]}...")

    try:
        return await create_goal(
            goal=payload.goal,
            priority=payload.priority
        )
    except ValueError as e:
        raise PlannerException(detail=str(e))
    except Exception as e:
        logger.error(f"Goal creation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"HERVEX encountered an error: {str(e)}"
        )
