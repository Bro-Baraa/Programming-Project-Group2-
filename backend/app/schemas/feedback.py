"""Feedback schemas."""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from .user import UserResponse


class FeedbackBase(BaseModel):
    message: str


class FeedbackCreate(FeedbackBase):
    to_user_id: int


class FeedbackResponse(FeedbackBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    internship_id: int
    from_user_id: int
    to_user_id: int
    created_at: datetime

    from_user: Optional[UserResponse] = None
    to_user: Optional[UserResponse] = None
