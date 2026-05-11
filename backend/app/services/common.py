"""Common service utilities."""
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import User, Internship, CompetencyProfile


def can_access_internship(user: User, internship: Internship) -> bool:
    """Return whether a user may view or act on an internship resource."""
    if user.role in {"committee", "admin"}:
        return True
    if user.role == "student":
        return internship.student_id == user.id
    if user.role == "mentor":
        return internship.mentor_id == user.id
    if user.role == "teacher":
        return internship.teacher_id == user.id
    return False


def ensure_internship_access(
    user: User,
    internship: Internship,
    detail: str = "Not authorized",
) -> None:
    """Raise a 403 if the user cannot access the internship."""
    if not can_access_internship(user, internship):
        raise HTTPException(status_code=403, detail=detail)


def get_active_competency_profile(db: Session) -> Optional[CompetencyProfile]:
    """Return the currently active competency profile, if any."""
    return db.query(CompetencyProfile).filter(CompetencyProfile.active == True).first()
