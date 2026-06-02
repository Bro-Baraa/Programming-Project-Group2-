"""Logbook service layer."""
from datetime import datetime, UTC
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Internship, Logbook
from app.schemas import LogbookCreate, LogbookUpdate
from .common import ensure_internship_access


def create_logbook(
    db: Session,
    internship: Internship,
    current_user,
    data: LogbookCreate,
) -> Logbook:
    """Create a weekly logbook entry for a student-owned internship."""
    ensure_internship_access(current_user, internship)

    if internship.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if internship.status not in ["Lopend", "Afgerond"]:
        raise HTTPException(
            status_code=400,
            detail="Can only create logbooks for ongoing or completed internships"
        )

    if data.week_number < 1:
        raise HTTPException(status_code=400, detail="Week number must be at least 1")

    existing = (
        db.query(Logbook)
        .filter(
            Logbook.internship_id == internship.id,
            Logbook.week_number == data.week_number,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400, detail=f"Logbook for week {data.week_number} already exists"
        )

    logbook = Logbook(
        internship_id=internship.id,
        week_number=data.week_number,
        tasks=data.tasks,
        reflection=data.reflection,
        issues=data.issues,
        status="draft",
    )

    db.add(logbook)
    db.commit()
    db.refresh(logbook)
    return logbook


def update_logbook(
    db: Session,
    logbook: Logbook,
    current_user,
    update: LogbookUpdate,
) -> Logbook:
    """Update a logbook entry while preserving role-specific rules."""
    internship = logbook.internship

    if current_user.role == "student":
        ensure_internship_access(current_user, internship)
        if update.mentor_validated is not None:
            raise HTTPException(
                status_code=403, detail="Cannot change mentor validation"
            )

    if current_user.role == "mentor":
        ensure_internship_access(current_user, internship)
        if any([update.tasks, update.reflection, update.issues, update.status]):
            raise HTTPException(
                status_code=403, detail="Mentors can only validate logbooks and give feedback"
            )
        if update.mentor_validated is not None:
            logbook.mentor_validated = update.mentor_validated
        if update.mentor_feedback is not None:
            logbook.mentor_feedback = update.mentor_feedback

    if current_user.role == "teacher":
        ensure_internship_access(current_user, internship)

    if update.tasks is not None:
        logbook.tasks = update.tasks
    if update.reflection is not None:
        logbook.reflection = update.reflection
    if update.issues is not None:
        logbook.issues = update.issues
    if update.status is not None and current_user.role != "mentor":
        logbook.status = update.status
        if update.status == "submitted":
            logbook.submitted_at = datetime.now(UTC)

    db.commit()
    db.refresh(logbook)
    return logbook
