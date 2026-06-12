"""Logbook service layer."""

from datetime import date as dt_date, datetime, timedelta, UTC
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Internship, Logbook
from app.schemas import LogbookCreate, LogbookUpdate
from .common import ensure_internship_access
from .notifications import notify


def _log_label(logbook: Logbook) -> str:
    """Return a human-readable label for a logbook entry."""
    if logbook.entry_date:
        return logbook.entry_date.strftime("%d/%m/%Y")
    return f"dag {logbook.week_number}" if logbook.week_number else "onbekend"


def create_logbook(
    db: Session,
    internship: Internship,
    current_user,
    data: LogbookCreate,
) -> Logbook:
    """Create a daily logbook entry for a student-owned internship."""
    ensure_internship_access(current_user, internship)

    if internship.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if internship.status not in ["Lopend", "Afgerond"]:
        raise HTTPException(
            status_code=400,
            detail="Can only create logbooks for ongoing or completed internships",
        )

    # Determine entry_date
    if data.entry_date:
        entry_date = data.entry_date
    elif data.week_number:
        entry_date = internship.start_date + timedelta(days=(data.week_number - 1) * 7) if internship.start_date else None
    else:
        raise HTTPException(status_code=400, detail="entry_date or week_number is required")

    if entry_date and internship.start_date and internship.end_date:
        if entry_date < internship.start_date or entry_date > internship.end_date:
            raise HTTPException(status_code=400, detail="Logbook date must be within the internship period")

    existing = (
        db.query(Logbook)
        .filter(
            Logbook.internship_id == internship.id,
            Logbook.entry_date == entry_date,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Logbook for {entry_date} already exists",
        )

    logbook = Logbook(
        internship_id=internship.id,
        entry_date=entry_date,
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
        if logbook.status in ("submitted", "approved") or logbook.mentor_validated:
            raise HTTPException(
                status_code=403,
                detail="Cannot edit a submitted or validated logbook",
            )
        if update.mentor_validated is not None:
            raise HTTPException(
                status_code=403, detail="Cannot change mentor validation"
            )

    if current_user.role == "mentor":
        ensure_internship_access(current_user, internship)
        if any([update.tasks, update.reflection, update.issues, update.status]):
            raise HTTPException(
                status_code=403,
                detail="Mentors can only validate logbooks and give feedback",
            )
        if update.mentor_validated is not None:
            logbook.mentor_validated = update.mentor_validated
            # ── Notify the student when the mentor validates their logbook ──
            if update.mentor_validated and internship.student_id:
                notify(
                    db,
                    user_id=internship.student_id,
                    message=f"Je logboek van {_log_label(logbook)} is goedgekeurd door je mentor.",
                    internship_id=internship.id,
                    link_view="logboek",  # sends student to their logbook view
                )
        if update.mentor_feedback is not None:
            logbook.mentor_feedback = update.mentor_feedback
            # ── Notify the student when the mentor gives feedback on their logbook ──
            if internship.student_id:
                notify(
                    db,
                    user_id=internship.student_id,
                    message=f"Je mentor heeft feedback gegeven op logboek {_log_label(logbook)}.",
                    internship_id=internship.id,
                    link_view="logboek",
                )

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
