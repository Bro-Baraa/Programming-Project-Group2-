"""Logbook endpoints."""

from datetime import datetime, timedelta, UTC
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Internship, Logbook, User
from app.schemas import (
    LogbookResponse,
    LogbookCreate,
    LogbookUpdate,
    LogbookDayStatus,
    LogbookWeekStatus,
)
from app.auth import get_current_active_user, require_student
from app.services.common import ensure_internship_access
from app.services.logbooks import (
    create_logbook as create_logbook_svc,
    update_logbook as update_logbook_svc,
)
from app.services.notifications import notify
from app.services.audit import log_event

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


@router.get("/{internship_id}/logbooks/days", response_model=List[LogbookDayStatus])
def get_day_overview(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """US-05, US-08: Get status of all days for the internship period"""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")

    ensure_internship_access(current_user, internship)

    if not internship.start_date or not internship.end_date:
        raise HTTPException(status_code=400, detail="Internship dates not set")

    # Calculate total days (handles year boundaries correctly)
    total_days = (internship.end_date - internship.start_date).days + 1

    if total_days < 1:
        raise HTTPException(
            status_code=400,
            detail="Stageperiode is te kort of einddatum ligt voor startdatum",
        )

    # Get existing logbooks
    logbooks = db.query(Logbook).filter(Logbook.internship_id == internship_id).all()
    logbook_map = {}
    for lb in logbooks:
        key = lb.entry_date or (
            internship.start_date + timedelta(days=(lb.week_number - 1) * 7)
            if lb.week_number
            else None
        )
        if key:
            logbook_map[key] = lb

    result = []
    for day in range(total_days):
        entry_date = internship.start_date + timedelta(days=day)
        if entry_date in logbook_map:
            lb = logbook_map[entry_date]
            result.append(
                LogbookDayStatus(
                    day_offset=day,
                    entry_date=entry_date,
                    logbook_id=lb.id,
                    status=lb.status,
                    mentor_validated=lb.mentor_validated,
                    mentor_feedback=lb.mentor_feedback,
                )
            )
        else:
            result.append(
                LogbookDayStatus(
                    day_offset=day,
                    entry_date=entry_date,
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
    """US-05: Create a new daily logbook entry"""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")

    result = create_logbook_svc(db, internship, current_user, data)
    log_event(
        db,
        "logbook.create",
        user=current_user,
        entity_type="internship",
        entity_id=internship_id,
        detail=f"Logboek {data.entry_date} aangemaakt",
    )
    return result


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

    result = update_logbook_svc(db, logbook, current_user, update)
    if current_user.role == "mentor" and update.mentor_validated:
        log_event(
            db,
            "logbook.validate",
            user=current_user,
            entity_type="internship",
            entity_id=logbook.internship_id,
            detail=f"Logboek week {logbook.week_number} gevalideerd",
        )
    return result


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
    logbook.submitted_at = datetime.now(UTC)
    db.commit()
    db.refresh(logbook)

    internship = logbook.internship
    student_name = (
        f"{internship.student.first_name} {internship.student.last_name}"
        if internship.student
        else "Een student"
    )
    log_label = (
        logbook.entry_date.strftime("%d/%m/%Y")
        if logbook.entry_date
        else f"dag {logbook.week_number}"
    )
    if internship.mentor_id:
        notify(
            db,
            user_id=internship.mentor_id,
            message=f"{student_name} heeft logboek {log_label} ingediend.",
            internship_id=internship.id,
            link_view="validatie",
        )
    if internship.teacher_id:
        notify(
            db,
            user_id=internship.teacher_id,
            message=f"{student_name} heeft logboek {log_label} ingediend.",
            internship_id=internship.id,
            link_view="logboek",
        )
    db.commit()

    log_event(
        db,
        "logbook.submit",
        user=current_user,
        entity_type="internship",
        entity_id=logbook.internship_id,
        detail=f"Logboek {log_label} definitief ingediend",
    )
    return logbook


@router.get("/{internship_id}/logbooks/weeks", response_model=List[LogbookWeekStatus])
def get_week_overview(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """US-08: Get status of all weeks for the internship period"""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")

    ensure_internship_access(current_user, internship)

    if not internship.start_date or not internship.end_date:
        raise HTTPException(status_code=400, detail="Internship dates not set")

    total_days = (internship.end_date - internship.start_date).days + 1
    if total_days < 1:
        raise HTTPException(
            status_code=400,
            detail="Stageperiode is te kort of einddatum ligt voor startdatum",
        )

    # Calculate total weeks (using ceiling division)
    total_weeks = (total_days + 6) // 7

    # Get existing logbooks
    logbooks = db.query(Logbook).filter(Logbook.internship_id == internship_id).all()
    logbook_map = {}
    for lb in logbooks:
        # If week_number is set, use it; otherwise compute it from entry_date
        week_num = lb.week_number
        if not week_num and lb.entry_date:
            days_diff = (lb.entry_date - internship.start_date).days
            week_num = (days_diff // 7) + 1
        
        if week_num:
            logbook_map[week_num] = lb

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
                    mentor_feedback=None,
                )
            )

    return result

