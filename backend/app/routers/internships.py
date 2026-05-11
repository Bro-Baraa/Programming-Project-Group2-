"""Core internship (stage) CRUD endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import User, Internship, Company, Proposal
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

router = APIRouter(prefix="/internships", tags=["internships"])


@router.get("", response_model=List[InternshipListResponse])
def list_internships(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List internships - filtered by role"""
    query = db.query(Internship)

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
    return internships


@router.post("", response_model=InternshipResponse, status_code=status.HTTP_201_CREATED)
def create_internship(
    data: InternshipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """US-01: Student submits a new internship proposal

    Creates:
    1. A Company
    2. An Internship record
    3. A Proposal record with the description
    """
    # Create company
    company = Company(
        name=data.company_name,
        address=data.company_address,
        sector=data.company_sector,
        contact_person=data.contact_person,
        contact_email=data.contact_email,
    )
    db.add(company)
    db.flush()  # Get company ID

    # Create internship
    internship = Internship(
        student_id=current_user.id,
        company_id=company.id,
        start_date=data.start_date,
        end_date=data.end_date,
        status="Ingediend",
    )
    db.add(internship)
    db.flush()  # Get internship ID

    # Create proposal
    proposal = Proposal(
        internship_id=internship.id,
        description=data.description,
        status="Ingediend",
    )
    db.add(proposal)

    db.commit()
    db.refresh(internship)

    return internship


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
    """Update internship details - staff only (teacher, committee, admin)"""
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
    if update.status is not None:
        internship.status = update.status

    db.commit()
    db.refresh(internship)

    return internship
