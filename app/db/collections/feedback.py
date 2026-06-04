# feedback.py contains all database operations for the feedback collection.
# Feedback is stored per run, per institution.
# Responses rated 1 or 2 are automatically flagged for review.
# This feeds the improvement loop described in the design system.

import uuid
# from datetime import datetime, timezone
from typing import Optional, List
from loguru import logger
from app.db.connection import get_database
from app.enums.status import FeedbackRating
from app.core.settings import APP_NAME

# Responses rated at or below this threshold are flagged for review
REVIEW_THRESHOLD = FeedbackRating.POOR

async def insert_feedback(feedback_document: dict) -> str:
    """
    Inserts a new feedback record into the feedback collection.

    Args:
        feedback_document: Feedback dict including run_id, rating, comment

    Returns:
        The feedback_id of the inserted record
    """
    db = get_database()
    await db.feedback.insert_one(feedback_document)
    logger.info(
        f"[{APP_NAME}] Feedback: Recorded rating "
        f"{feedback_document['rating']} for run "
        f"{feedback_document['run_id']}"
    )
    return feedback_document["feedback_id"]

async def get_feedback_by_run(run_id: str) -> List[dict]:
    """
    Retrieves all feedback for a specific run.

    Args:
        run_id: The run identifier

    Returns:
        List of feedback documents
    """
    db = get_database()
    cursor = db.feedback.find({"run_id": run_id})
    return await cursor.to_list(length=100)

async def get_flagged_feedback(
    institution_id: str,
    limit: int = 50
) -> List[dict]:
    """
    Retrieves all flagged feedback for an institution.
    Used by the HERVEX team to identify and improve
    poorly performing responses.

    Args:
        institution_id: Institution to retrieve flagged feedback for
        limit: Maximum number of records to return

    Returns:
        List of flagged feedback documents ordered by created_at
    """
    db = get_database()
    cursor = db.feedback.find(
        {
            "institution_id": institution_id,
            "flagged_for_review": True
        }
    ).sort("created_at", -1).limit(limit)
    return await cursor.to_list(length=limit)
