# goal_service.py orchestrates the goal intake flow, sitting btwn the router and database/planner
# layers. The router calls this service - never touching MongoDB or Claude directly.
# Updated for phase 3 - runner [Added: triggers the agent executor after tasks are saved]


import uuid
from datetime import datetime, timezone
from app.db.documents.goal_document import GoalDocument
from app.db.collections.goals import insert_goal, update_goal_status, update_goal_tasks
from app.agents.planner import plan_goal
from app.services.agent_service import run_agent
from app.enums.status import GoalStatus, Priority
from app.schemas.goal import GoalResponse


async def create_goal(goal: str, priority: Priority) -> GoalResponse:
    """
    Handles the full goal creation flow. It:
     1. generates a session ID
     2. saves the goal to MongoDB
     3. sends the goal to the planner
     4. saves the generated tasks from planner to MongoDB
     5. triggers executor to begin task execution
     6. Returns the API response to the router
    
    Args:
        goal: The raw goal string from the client
        priority: Execution priority level
    
    Returns:
        A GoalResponse schema ready to be returned by the router
    """
    
    session_id = str(uuid.uuid4())
    
    # build and persist the goal document in MongoDB
    goal_doc = GoalDocument.create(
        session_id=session_id,
        goal=goal,
        priority=priority
    )
    await insert_goal(goal_doc)
    
    # update status to PLANNING before calling the planner
    await update_goal_status(session_id, GoalStatus.PLANNING)
    
    # send goal to Claude planner and get structured task list back
    tasks = await plan_goal(goal)
    
    # save the generated task list into MongoDB goal document
    await update_goal_tasks(session_id, tasks)
    
    # update status to EXECUTING before triggering the executor
    await update_goal_status(session_id, GoalStatus.EXECUTING)
    
    # Trigger the executor, to be handled by Celery later on
    await run_agent(session_id)
    
    return GoalResponse(
        session_id=session_id,
        goal=goal,
        status=GoalStatus.EXECUTING,
        priority=priority,
        created_at=datetime.now(timezone.utc).isoformat(),
        message=f"HERVEX has planned {len(tasks)} tasks. Now executing..."
    )



    
