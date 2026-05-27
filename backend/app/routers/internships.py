"""Core internship (stage) CRUD endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from typing import List, Optional
from datetime import date
from pathlib import Path
from typing import Annotated

from app.database import get_db
from app.models import User, Internship, Company
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
from app.dependencies import pagination, search_query

router = APIRouter(prefix="/internships", tags=["internships"])

_CONFIG = LifecycleConfig(agreements_dir=Path("uploads/agreements"))


VALID_STATUSES = {"Ingediend", "In Beoordeling", "Goedgekeurd", "Afgekeurd", "Aanpassingen Vereist", "Overeenkomst Ingediend", "Lopend", "Afgerond"}


@router.get("", response_model=List[InternshipListResponse])
def list_internships(
    response: Response,
    status: Optional[str] = None,
    search: Annotated[Optional[str], Query(min_length=1, max_length=100, description="Search student name or company name")] = None,
    start_date_from: Annotated[Optional[date], Query(description="Filter from start date")] = None,
    start_date_to: Annotated[Optional[date], Query(description="Filter to start date")] = None,
    sort: Annotated[Optional[str], Query(pattern=r"^-?[a-zA-Z_]+$", description="Sort field. Prefix with - for descending. E.g. created_at, -status")] = "-created_at",
    pag: Annotated[dict, Depends(pagination)] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List internships - filtered by role with pagination, search, and sorting.

    Query params:
    - status: single status or comma-separated (e.g. `Ingediend,Goedgekeurd`)
    - search: keyword search across student name and company name
    - start_date_from / start_date_to: date range filter
    - sort: sort field, prefix with `-` for descending
    - skip / limit: pagination (default limit=50, max=200)

    Response headers:
    - X-Total-Count: total matching items (for pagination UI)
    """
    # Validate status(es)
    status_filter = None
    if status:
        statuses = [s.strip() for s in status.split(",")]
        invalid = [s for s in statuses if s not in VALID_STATUSES]
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status(es): {', '.join(invalid)}. Must be one of: {', '.join(VALID_STATUSES)}"
            )
        status_filter = statuses

    # Base query with eager loads
    query = db.query(Internship).options(
        joinedload(Internship.student),
        joinedload(Internship.company),
        joinedload(Internship.teacher),
        joinedload(Internship.mentor),
        joinedload(Internship.proposal),
        joinedload(Internship.agreement),
    )

    # Role-based access filter
    if current_user.role == "student":
        query = query.filter(Internship.student_id == current_user.id)
    elif current_user.role == "mentor":
        query = query.filter(Internship.mentor_id == current_user.id)
    elif current_user.role == "teacher":
        query = query.filter(Internship.teacher_id == current_user.id)
    # Committee and admin see all

    # Status filter (supports multi-status)
    if status_filter:
        if len(status_filter) == 1:
            query = query.filter(Internship.status == status_filter[0])
        else:
            query = query.filter(Internship.status.in_(status_filter))

    # Date range filter
    if start_date_from:
        query = query.filter(Internship.start_date >= start_date_from)
    if start_date_to:
        query = query.filter(Internship.start_date <= start_date_to)

    # Search: join with User (student) and Company for name filtering
    if search:
        search_term = f"%{search}%"
        query = query.join(Internship.student).join(Internship.company).filter(
            or_(
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
                Company.name.ilike(search_term),
            )
        )

    # Count total before pagination
    total_count = query.with_entities(func.count(Internship.id)).scalar()

    # Sorting
    sort_field = sort.lstrip("-") if sort else "created_at"
    sort_desc = sort and sort.startswith("-")

    if sort_field == "created_at":
        order_col = Internship.created_at
    elif sort_field == "status":
        order_col = Internship.status
    elif sort_field == "start_date":
        order_col = Internship.start_date
    elif sort_field == "end_date":
        order_col = Internship.end_date
    else:
        order_col = Internship.created_at

    query = query.order_by(order_col.desc() if sort_desc else order_col.asc())

    # Pagination
    skip = pag.get("skip", 0) if pag else 0
    limit = pag.get("limit", 50) if pag else 50
    internships = query.offset(skip).limit(limit).all()

    # Set total count header for pagination UI
    response.headers["X-Total-Count"] = str(total_count)

    # Build enriched response
    return [
        {
            "id": i.id,
            "student_id": i.student_id,
            "company_id": i.company_id,
            "start_date": i.start_date,
            "end_date": i.end_date,
            "status": i.status,
            "created_at": i.created_at,
            "student": i.student,
            "company": i.company,
            "teacher": i.teacher,
            "mentor": i.mentor,
            "proposal_status": i.proposal.status if i.proposal else None,
            "agreement_status": i.agreement.status if i.agreement else None,
            "agreement_uploaded": i.agreement is not None,
        }
        for i in internships
    ]


@router.post("", response_model=InternshipResponse, status_code=status.HTTP_201_CREATED)
def create_internship(
    data: InternshipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """US-01: Student submits a new internship proposal."""
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
    return result.internship


@router.get("/{internship_id}", response_model=InternshipResponse)
def get_internship(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get detailed internship information"""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
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
    """Update internship meta details - staff only (teacher, committee, admin).
    Status changes must go through the dedicated lifecycle endpoints."""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")

    if update.teacher_id is not None:
        internship.teacher_id = update.teacher_id
    if update.mentor_id is not None:
        internship.mentor_id = update.mentor_id
    if update.company_id is not None:
        internship.company_id = update.company_id
    if update.start_date is not None:
        internship.start_date = update.start_date
    if update.end_date is not None:
        internship.end_date = update.end_date
    # Note: status updates are intentionally ignored here;
    # use review_proposal, validate_agreement, etc. instead.

    db.commit()
    db.refresh(internship)

    return internship
