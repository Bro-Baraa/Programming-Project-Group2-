"""Core internship (stage) CRUD endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from pathlib import Path

from app.database import get_db
from app.models import User, Internship
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

router = APIRouter(prefix="/internships", tags=["internships"])

_CONFIG = LifecycleConfig(agreements_dir=Path("uploads/agreements"))


VALID_STATUSES = {"Ingediend", "In Beoordeling", "Goedgekeurd", "Afgekeurd", "Aanpassingen Vereist", "Overeenkomst Ingediend", "Lopend", "Afgerond"}


@router.get("", response_model=List[InternshipListResponse])
def list_internships(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List internships - filtered by role.

    Returns enriched list data including proposal status, agreement status,
    assigned teacher/mentor, and agreement-uploaded flag.
    """
    if status and status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}. Must be one of: {', '.join(VALID_STATUSES)}")

    query = db.query(Internship).options(
        joinedload(Internship.student),
        joinedload(Internship.company),
        joinedload(Internship.teacher),
        joinedload(Internship.mentor),
        joinedload(Internship.proposal),
        joinedload(Internship.agreement),
    )

    # Filter based on role
    if current_user.role == "student":
        query = query.filter(Internship.student_id == current_user.id)
    elif current_user.role == "mentor":
        query = query.filter(Internship.mentor_id == current_user.id)
    elif current_user.role == "teacher":
        query = query.filter(Internship.teacher_id == current_user.id)
    # Committee and admin see all

    if status:
        query = query.filter(Internship.status == status)

    internships = query.order_by(Internship.created_at.desc()).all()

    # Build enriched response manually so computed fields are populated
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
