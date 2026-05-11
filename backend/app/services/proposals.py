"""Proposal service layer."""
from datetime import datetime, UTC
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Internship
from app.schemas import ProposalUpdate


def update_proposal(
    db: Session,
    internship: Internship,
    update_data: ProposalUpdate,
) -> None:
    """Apply a proposal decision and mirror the internship status."""
    if not internship.proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    proposal = internship.proposal
    new_status = update_data.status
    valid_statuses = ["Goedgekeurd", "Afgekeurd", "Aanpassingen Vereist"]

    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")

    if new_status == "Aanpassingen Vereist" and not update_data.feedback:
        raise HTTPException(
            status_code=400, detail="Feedback is required when requesting changes"
        )

    proposal.status = new_status
    if update_data.feedback:
        proposal.feedback = update_data.feedback

    internship.status = new_status
    db.commit()
    db.refresh(proposal)


def resubmit_proposal(
    db: Session,
    internship: Internship,
    current_user,
    new_description: str,
) -> None:
    """Resubmit a proposal after changes were requested."""
    if internship.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if not internship.proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    if internship.proposal.status != "Aanpassingen Vereist":
        raise HTTPException(
            status_code=400, detail="Can only resubmit when changes are requested"
        )

    proposal = internship.proposal
    proposal.description = new_description
    proposal.status = "Ingediend"
    proposal.submitted_at = datetime.now(UTC)
    internship.status = "Ingediend"

    db.commit()
    db.refresh(proposal)
