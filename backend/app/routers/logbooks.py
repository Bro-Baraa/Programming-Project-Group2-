"""Logbook endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Internship, Logbook, User
from app.schemas import (
    LogbookResponse,
    LogbookCreate,
    LogbookUpdate,
    LogbookWeekStatus,
)
from app.auth import get_current_active_user, require_student
from app.services.common import ensure_internship_access
from app.services.logbooks import create_logbook as create_logbook_svc, update_logbook as update_logbook_svc
from app.services.notifications import notify

router = APIRouter(prefix="/internships", tags=["logbooks"])


@router.get("/{internship_id}/logbooks", response_model=List[LogbookResponse])
def list_logbooks(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """US-05, US-08, US-14, US-15, US-21: List logbooks for an internship"""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")

    ensure_internship_access(current_user, internship)

    logbooks = db.query(Logbook).filter(Logbook.internship_id == internship_id).all()
    return logbooks


@router.get("/{internship_id}/logbooks/weeks", response_model=List[LogbookWeekStatus])
def get_week_overview(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """US-05, US-08: Get status of all weeks for the internship period"""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")

    ensure_internship_access(current_user, internship)

    if not internship.start_date or not internship.end_date:
        raise HTTPException(status_code=400, detail="Internship dates not set")

    # Calculate total weeks (handles year boundaries correctly)
    total_days = (internship.end_date - internship.start_date).days
    total_weeks = (total_days // 7) + 1

    # Get existing logbooks
    logbooks = db.query(Logbook).filter(Logbook.internship_id == internship_id).all()
    logbook_map = {lb.week_number: lb for lb in logbooks}

    result = []
    for week in range(1, total_weeks + 1):
        if week in logbook_map:
            lb = logbook_map[week]
            result.append(
                LogbookWeekStatus(
                    week_number=week,
                    logbook_id=lb.id,
                    status=lb.status,
                    mentor_validated=lb.mentor_validated,
                    mentor_feedback=lb.mentor_feedback,
                )
            )
        else:
            result.append(
                LogbookWeekStatus(
                    week_number=week,
                    logbook_id=None,
                    status="missing",
                    mentor_validated=False,
                )
            )

    return result


@router.post("/{internship_id}/logbooks", response_model=LogbookResponse)
def create_logbook(
    internship_id: int,
    data: LogbookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """US-05: Create a new logbook entry for a week"""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")

    return create_logbook_svc(db, internship, current_user, data)


@router.patch("/logbooks/{logbook_id}", response_model=LogbookResponse)
def update_logbook(
    logbook_id: int,
    update: LogbookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """US-05: Update logbook - students edit, mentors validate"""
    logbook = db.query(Logbook).filter(Logbook.id == logbook_id).first()
    if not logbook:
        raise HTTPException(status_code=404, detail="Logbook not found")

    return update_logbook_svc(db, logbook, current_user, update)


@router.post("/logbooks/{logbook_id}/submit", response_model=LogbookResponse)
def submit_logbook(
    logbook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """US-05: Student definitively submits a logbook"""
    logbook = db.query(Logbook).filter(Logbook.id == logbook_id).first()
    if not logbook:
        raise HTTPException(status_code=404, detail="Logbook not found")

    if logbook.internship.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if logbook.status == "submitted":
        raise HTTPException(status_code=400, detail="Logbook already submitted")

    logbook.status = "submitted"
    from datetime import datetime, UTC
    logbook.submitted_at = datetime.now(UTC)

    db.commit()
    db.refresh(logbook)

    # ── Notify the mentor that a logbook has been submitted ──
    internship = logbook.internship
    if internship.mentor_id:
        student_name = f"{internship.student.first_name} {internship.student.last_name}" if internship.student else "Een student"
        notify(
            db,
            user_id=internship.mentor_id,
            message=f"{student_name} heeft logboek week {logbook.week_number} ingediend.",
            internship_id=internship.id,
            link_view="validatie",  # sends mentor to their validation tab
        )
        db.commit()

    return logbook
