"""Proposal (Stagevoorstel) endpoints."""
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Internship, User
from app.schemas import ProposalResponse, ProposalUpdate
from app.auth import get_current_active_user, require_committee, require_student
from app.services.proposals import update_proposal, resubmit_proposal
from app.services.common import ensure_internship_access

router = APIRouter(prefix="/internships", tags=["proposals"])


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
    """US-11, US-12: Committee evaluates proposal
    
    Status transitions:
    - Goedgekeurd: Proposal approved, student can upload agreement
    - Afgekeurd: Proposal rejected
    - Aanpassingen Vereist: Feedback required, student must revise
    """
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    if not internship.proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    update_proposal(db, internship, update_data)
    return internship.proposal


@router.post("/{internship_id}/resubmit", response_model=ProposalResponse)
def resubmit_proposal_endpoint(
    internship_id: int,
    new_description: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student)
):
    """Student resubmits proposal after changes requested"""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    ensure_internship_access(current_user, internship)

    resubmit_proposal(db, internship, current_user, new_description)
    return internship.proposal
