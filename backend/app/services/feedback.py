"""Feedback service layer."""

from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.models import Internship, Feedback
from app.schemas import FeedbackCreate
from .common import ensure_internship_access


def list_feedback(db: Session, current_user, internship_id: int) -> List[Feedback]:
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")

    ensure_internship_access(current_user, internship)
    return db.query(Feedback).filter(Feedback.internship_id == internship_id).all()


def create_feedback(
    db: Session, current_user, internship_id: int, data: FeedbackCreate
) -> Feedback:
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")

    valid_recipients = [
        internship.student_id,
        internship.teacher_id,
        internship.mentor_id,
    ]
    if data.to_user_id not in valid_recipients:
        raise HTTPException(
            status_code=400,
            detail="Recipient must be a participant in this internship (student, teacher, or mentor)",
        )

    feedback = Feedback(
        internship_id=internship_id,
        from_user_id=current_user.id,
        to_user_id=data.to_user_id,
        message=data.message,
    )

    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback
