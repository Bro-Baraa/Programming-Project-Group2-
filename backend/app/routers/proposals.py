"""Proposal (Stagevoorstel) endpoints."""
from pathlib import Path
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Internship, User
from app.schemas import ProposalResponse, ProposalUpdate, ProposalCreate
from app.auth import get_current_active_user, require_committee, require_student
from app.services.common import ensure_internship_access
from app.services.lifecycle import InternshipLifecycle, LifecycleConfig

router = APIRouter(prefix="/internships", tags=["proposals"])


@router.post("/{internship_id}/proposal", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
def create_proposal_endpoint(
    internship_id: int,
    data: ProposalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """US-01: Student submits a proposal for an existing internship.

    Use this when an internship was created by staff/admin and the student
    still needs to submit the actual proposal description.
    """
    lifecycle = InternshipLifecycle(db, LifecycleConfig(agreements_dir=Path("uploads/agreements")))
    result = lifecycle.create_proposal(
        internship_id=internship_id,
        actor=current_user,
        description=data.description,
    )
    return result.internship.proposal


@router.get("/{internship_id}/proposal", response_model=ProposalResponse)
def get_proposal(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """US-02: Get proposal status"""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    ensure_internship_access(current_user, internship)

    if not internship.proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    return internship.proposal


@router.patch("/{internship_id}/proposal", response_model=ProposalResponse)
def update_proposal_endpoint(
    internship_id: int,
    update_data: ProposalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_committee)
):
    """US-11, US-12: Committee evaluates proposal.

    Status transitions:
    - Goedgekeurd: Proposal approved, student can upload agreement
    - Afgekeurd: Proposal rejected
    - Aanpassingen Vereist: Feedback required, student must revise
    """
    lifecycle = InternshipLifecycle(db, LifecycleConfig(agreements_dir=Path("uploads/agreements")))
    result = lifecycle.review_proposal(
        internship_id=internship_id,
        actor=current_user,
        decision=update_data.status,
        feedback=update_data.feedback,
    )
    return result.internship.proposal


@router.post("/{internship_id}/resubmit", response_model=ProposalResponse)
def resubmit_proposal_endpoint(
    internship_id: int,
    new_description: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student)
):
    """Student resubmits proposal after changes requested."""
    lifecycle = InternshipLifecycle(db, LifecycleConfig(agreements_dir=Path("uploads/agreements")))
    result = lifecycle.resubmit_proposal(
        internship_id=internship_id,
        actor=current_user,
        new_description=new_description,
    )
    return result.internship.proposal
