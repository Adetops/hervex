from fastapi import APIRouter, HTTPException
from app.schemas.goal import GoalRequest, GoalResponse
from app.enums.status import GoalStatus
from datetime import datetime, timezone
import uuid


router = APIRouter(prefix="/goals", tags=["Goals"])

@router.post("/", response_model=GoalResponse, status_code=201)
async def submit_goal(payload: GoalRequest):
    if len(payload.goal.strip()) < 10:
        raise HTTPException(status_code=400, detail="Goal is too vague. Be more specific, please.")
    
    session_id = str(uuid.uuid4())

    return GoalResponse(
        session_id=session_id,
        goal=payload.goal,
        status=GoalStatus.RECEIVED,
        priority=payload.priority,
        created_at=datetime.now(timezone.utc).isoformat(),
        message=f"Goal received. Session {session_id} created. Agent will begin shortly."        
    )
