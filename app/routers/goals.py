# goals.py handles all HTTP routing for goal-related endpoints
# implemented to handle HTTP concerns only - all business-logic in goal_service.py

from fastapi import APIRouter, HTTPException
from app.schemas.goal import GoalRequest, GoalResponse
from app.enums.status import GoalStatus
from app.services.goal_service import create_goal
from datetime import datetime, timezone
import uuid


router = APIRouter(prefix="/goals", tags=["Goals"])

@router.post("/", response_model=GoalResponse, status_code=201)
async def submit_goal(payload: GoalRequest):
    """
    Endpoint to submit a new goal to HERVEX. It validates the requests,
    delegates to goal_service, and returns a session ID and planned task count.
    """
    
    try:
        await create_goal(
            goal=payload.goal,
            priority=payload.priority
        )
    except ValueError as e:
        # raised by the planner if Claude returns an invalid response
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        # catches all unexpected errors during goal creation
        raise HTTPException(status_code=500, detail=f"Hervex encountered an error: {str(e)}")
