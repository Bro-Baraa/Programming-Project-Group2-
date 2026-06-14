"""Internship endpoints."""

from datetime import date
from pathlib import Path
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_

from app.database import get_db
from app.models import Internship, Company, User
from app.schemas import (
    InternshipCreate,
    InternshipResponse,
    InternshipUpdate,
    InternshipListResponse,
)
from app.auth import (
    get_current_active_user,
    require_student,
    require_any_staff,
)
from app.services.common import ensure_internship_access
from app.services.lifecycle import InternshipLifecycle, LifecycleConfig
from app.services.audit import log_event
from app.dependencies import pagination, search_query

router = APIRouter(prefix="/internships", tags=["internships"])

_CONFIG = LifecycleConfig(agreements_dir=Path("uploads/agreements"))


VALID_STATUSES = {
    "Ingediend",
    "In Beoordeling",
    "Goedgekeurd",
    "Afgekeurd",
    "Aanpassingen Vereist",
    "Overeenkomst Ingediend",
    "Lopend",
    "Afgerond",
    "Stopgezet",
}

_EAGER_LOADS = [
    joinedload(Internship.student),
    joinedload(Internship.company),
    joinedload(Internship.teacher),
    joinedload(Internship.mentor),
    joinedload(Internship.proposal),
    joinedload(Internship.agreement),
]


@router.get("", response_model=List[InternshipListResponse])
def list_internships(
    response: Response,
    status: Optional[str] = None,
    search: Annotated[
        Optional[str],
        Query(
            min_length=1,
            max_length=100,
            description="Search student name or company name",
        ),
    ] = None,
    start_date_from: Annotated[
        Optional[date], Query(description="Filter from start date")
    ] = None,
    start_date_to: Annotated[
        Optional[date], Query(description="Filter to start date")
    ] = None,
    sort: Annotated[
        Optional[str],
        Query(
            pattern=r"^-?[a-zA-Z_]+$",
            description="Sort field. Prefix with - for descending. E.g. created_at, -status",
        ),
    ] = "-created_at",
    pag: Annotated[dict, Depends(pagination)] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):

    status_filter = None
    if status:
        statuses = [s.strip() for s in status.split(",")]
        invalid = [s for s in statuses if s not in VALID_STATUSES]
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status(es): {', '.join(invalid)}. Must be one of: {', '.join(VALID_STATUSES)}",
            )
        status_filter = statuses

    query = db.query(Internship).options(*_EAGER_LOADS)

    if current_user.role == "student":
        query = query.filter(Internship.student_id == current_user.id)
    elif current_user.role == "mentor":
        query = query.filter(Internship.mentor_id == current_user.id)
    elif current_user.role == "teacher":
        query = query.filter(Internship.teacher_id == current_user.id)

    if status_filter:
        query = query.filter(Internship.status.in_(status_filter))

    if start_date_from:
        query = query.filter(Internship.start_date >= start_date_from)
    if start_date_to:
        query = query.filter(Internship.start_date <= start_date_to)

    if search:
        search_term = f"%{search}%"
        query = (
            query.join(Internship.student)
            .join(Internship.company)
            .filter(
                or_(
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    Company.name.ilike(search_term),
                )
            )
        )

    total_count = query.with_entities(func.count(Internship.id)).scalar()

    sort_field = sort.lstrip("-") if sort else "created_at"
    sort_desc = sort and sort.startswith("-")

    order_col = {
        "created_at": Internship.created_at,
        "status": Internship.status,
        "start_date": Internship.start_date,
        "end_date": Internship.end_date,
    }.get(sort_field, Internship.created_at)

    query = query.order_by(order_col.desc() if sort_desc else order_col.asc())

    skip = pag.get("skip", 0) if pag else 0
    limit = pag.get("limit", 50) if pag else 50
    internships = query.offset(skip).limit(limit).all()

    response.headers["X-Total-Count"] = str(total_count)
    return internships


@router.post("", response_model=InternshipResponse, status_code=status.HTTP_201_CREATED)
def create_internship(
    data: InternshipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):

    lifecycle = InternshipLifecycle(db, _CONFIG)
    result = lifecycle.submit_internship(
        actor=current_user,
        company_name=data.company_name,
        company_address=data.company_address,
        company_sector=data.company_sector,
        contact_person=data.contact_person,
        contact_email=data.contact_email,
        start_date=data.start_date,
        end_date=data.end_date,
        description=data.description,
        teacher_id=data.teacher_id,
        mentor_id=data.mentor_id,
    )
    log_event(
        db,
        "internship.create",
        user=current_user,
        entity_type="internship",
        entity_id=result.id,
        detail="Stage ingediend",
    )
    return result


@router.get("/{internship_id}", response_model=InternshipResponse)
def get_internship(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):

    internship = (
        db.query(Internship)
        .options(*_EAGER_LOADS)
        .filter(Internship.id == internship_id)
        .first()
    )
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")

    ensure_internship_access(
        current_user, internship, "Not authorized to view this internship"
    )
    return internship


@router.patch("/{internship_id}", response_model=InternshipResponse)
def update_internship(
    internship_id: int,
    update: InternshipUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff),
):

    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")

    ensure_internship_access(
        current_user, internship, "Not authorized to update this internship"
    )

    if update.teacher_id is not None:
        teacher = db.query(User).filter(User.id == update.teacher_id).first()
        if not teacher:
            raise HTTPException(status_code=400, detail="Docent niet gevonden")
        if teacher.role != "teacher":
            raise HTTPException(status_code=400, detail="Gebruiker is geen docent")
        internship.teacher_id = update.teacher_id
    if update.mentor_id is not None:
        mentor = db.query(User).filter(User.id == update.mentor_id).first()
        if not mentor:
            raise HTTPException(status_code=400, detail="Mentor niet gevonden")
        if mentor.role != "mentor":
            raise HTTPException(status_code=400, detail="Gebruiker is geen mentor")
        internship.mentor_id = update.mentor_id
    if update.company_id is not None:
        internship.company_id = update.company_id
    if update.start_date is not None:
        internship.start_date = update.start_date
    if update.end_date is not None:
        internship.end_date = update.end_date
    # Status changes must go through lifecycle endpoints.

    db.commit()
    db.refresh(internship)
    return internship
