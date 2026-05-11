"""Feedback endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User
from app.schemas import FeedbackResponse, FeedbackCreate
from app.auth import get_current_active_user, require_any_staff
from app.services.feedback import list_feedback as list_feedback_svc, create_feedback as create_feedback_svc

router = APIRouter(prefix="/internships", tags=["feedback"])


@router.get("/{internship_id}/feedback", response_model=List[FeedbackResponse])
def list_feedback(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """US-03, US-07: List feedback for an internship"""
    return list_feedback_svc(db, current_user, internship_id)


@router.post("/{internship_id}/feedback", response_model=FeedbackResponse)
def create_feedback(
    internship_id: int,
    data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff),
):
    """US-03, US-07, US-12, US-16, US-20: Create feedback"""
    return create_feedback_svc(db, current_user, internship_id, data)
