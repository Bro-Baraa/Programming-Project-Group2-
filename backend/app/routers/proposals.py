"""Proposal (Stagevoorstel) endpoints."""

from pathlib import Path
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Internship, ProposalVersion, User
from app.schemas import (
    ProposalResponse,
    ProposalUpdate,
    ProposalCreate,
    ProposalVersionResponse,
    ResubmitRequest,
    EditProposalRequest,
)
from app.auth import get_current_active_user, require_committee, require_student
from app.services.common import ensure_internship_access
from app.services.lifecycle import InternshipLifecycle, LifecycleConfig
from app.services.audit import log_event
from app.services.notifications import notify
from typing import List

router = APIRouter(prefix="/internships", tags=["proposals"])

# Shared configuration
_LIFECYCLE_CONFIG = LifecycleConfig(agreements_dir=Path("uploads/agreements"))


def _notify_committee(
    db: Session, current_user: User, internship_id: int, message: str
) -> None:
    """Notify all active committee members about a proposal event."""
    committee_members = (
        db.query(User)
        .filter(
            User.role == "committee",
            User.is_active == True,
        )
        .all()
    )
    student_name = f"{current_user.first_name} {current_user.last_name}"
    full_message = f"{student_name} {message}"
    for member in committee_members:
        notify(
            db,
            user_id=member.id,
            message=full_message,
            internship_id=internship_id,
            link_view="voorstellen",
        )
    db.commit()


def _get_lifecycle(db: Session) -> InternshipLifecycle:
    """Return a configured InternshipLifecycle instance."""
    return InternshipLifecycle(db, _LIFECYCLE_CONFIG)


@router.post(
    "/{internship_id}/proposal",
    response_model=ProposalResponse,
    status_code=status.HTTP_201_CREATED,
)
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
    result = _get_lifecycle(db).create_proposal(
        internship_id=internship_id,
        actor=current_user,
        description=data.description,
    )
    log_event(
        db,
        "proposal.submit",
        user=current_user,
        entity_type="internship",
        entity_id=internship_id,
        detail="Voorstel ingediend",
    )
    return result.proposal


@router.get("/{internship_id}/proposal", response_model=ProposalResponse)
def get_proposal(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
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
    current_user: User = Depends(require_committee),
):
    """US-11, US-12: Committee evaluates proposal.

    Status transitions:
    - Goedgekeurd: Proposal approved — teacher_id is required
    - Afgekeurd: Proposal rejected
    - Aanpassingen Vereist: Feedback required, student must revise
    """
    result = _get_lifecycle(db).review_proposal(
        internship_id=internship_id,
        actor=current_user,
        decision=update_data.status,
        feedback=update_data.feedback,
        teacher_id=update_data.teacher_id,
        mentor_id=update_data.mentor_id,
    )
    log_event(
        db,
        "proposal.review",
        user=current_user,
        entity_type="internship",
        entity_id=internship_id,
        detail=f"Voorstel beoordeeld: {update_data.status}",
    )
    return result.proposal


@router.patch("/{internship_id}/proposal/edit", response_model=ProposalResponse)
def edit_proposal_endpoint(
    internship_id: int,
    data: EditProposalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """Student edits proposal before it has been reviewed."""
    result = _get_lifecycle(db).edit_proposal(
        internship_id=internship_id,
        actor=current_user,
        description=data.description,
        company_name=data.company_name,
        company_address=data.company_address,
        company_sector=data.company_sector,
        contact_person=data.contact_person,
        contact_email=data.contact_email,
        start_date=data.start_date,
        end_date=data.end_date,
    )
    log_event(
        db,
        "proposal.edit",
        user=current_user,
        entity_type="internship",
        entity_id=internship_id,
        detail="Voorstel bewerkt",
    )
    _notify_committee(
        db, current_user, internship_id, "heeft het stagevoorstel bewerkt."
    )
    return result.proposal


@router.post("/{internship_id}/resubmit", response_model=ProposalResponse)
def resubmit_proposal_endpoint(
    internship_id: int,
    data: ResubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """Student resubmits proposal after changes requested."""
    result = _get_lifecycle(db).resubmit_proposal(
        internship_id=internship_id,
        actor=current_user,
        new_description=data.new_description,
        company_name=data.company_name,
        company_address=data.company_address,
        company_sector=data.company_sector,
        contact_person=data.contact_person,
        contact_email=data.contact_email,
        start_date=data.start_date,
        end_date=data.end_date,
    )
    log_event(
        db,
        "proposal.resubmit",
        user=current_user,
        entity_type="internship",
        entity_id=internship_id,
        detail="Voorstel herindienen",
    )
    return result.proposal


@router.get(
    "/{internship_id}/proposal/versions", response_model=List[ProposalVersionResponse]
)
def get_proposal_versions(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get full version history of a proposal (admin, committee, or involved student)."""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")

    ensure_internship_access(current_user, internship)

    if not internship.proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    versions = (
        db.query(ProposalVersion)
        .filter(ProposalVersion.proposal_id == internship.proposal.id)
        .order_by(ProposalVersion.version.desc())
        .all()
    )

    return versions


@router.delete("/{internship_id}/proposal")
def withdraw_proposal_endpoint(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """Student withdraws (deletes) their internship before it is reviewed."""
    result = _get_lifecycle(db).withdraw_proposal(
        internship_id=internship_id,
        actor=current_user,
    )
    log_event(
        db,
        "proposal.withdraw",
        user=current_user,
        entity_type="internship",
        entity_id=internship_id,
        detail="Voorstel ingetrokken",
    )
    _notify_committee(
        db, current_user, internship_id, "heeft het stagevoorstel ingetrokken."
    )
    return {"detail": "Voorstel succesvol ingetrokken"}
