# feedback.py defines Pydantic schemas for the feedback endpoint.
# Students and lecturers rate HERVEX responses after receiving them.
# Poorly rated responses are flagged for review and improvement.


from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.enums.status import FeedbackRating

class FeedbackRequest(BaseModel):
    """
    Submitted by a student or lecturer after receiving a result.
    Links feedback to a specific run and institution.
    """
    run_id: str = Field(
        ...,
        description="The run ID of the goal this feedback is for"
    )
    institution_id: str = Field(
        ...,
        description="Institution the feedback belongs to"
    )
    rating: FeedbackRating = Field(
        ...,
        description="1 (very poor) to 5 (excellent)"
    )
    comment: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional written feedback from the user"
    )
    user_type: Optional[str] = Field(
        default="student",
        description="student or lecturer"
    )

class FeedbackResponse(BaseModel):
    """
    Returned after feedback is successfully recorded.
    """
    feedback_id: str
    run_id: str
    rating: FeedbackRating
    flagged_for_review: bool
    message: str
    created_at: datetime
