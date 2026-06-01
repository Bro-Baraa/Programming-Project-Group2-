"""Internship lifecycle deep module.

Single source of truth for internship status transitions, role-based gatekeeping,
aggregate persistence, and side effects (file uploads, timestamps).
"""

import os
import shutil
from dataclasses import dataclass
from datetime import date, datetime, UTC
from pathlib import Path
from typing import BinaryIO, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Agreement, Company, Internship, Proposal, User


# ── Internal: legal status transitions ──
_TRANSITIONS: dict[str, set[str]] = {
    "Ingediend": {"In Beoordeling"},
    "In Beoordeling": {"Goedgekeurd", "Afgekeurd", "Aanpassingen Vereist"},
    "Aanpassingen Vereist": {"In Beoordeling"},
    "Goedgekeurd": {"Overeenkomst Ingediend"},
    "Overeenkomst Ingediend": {"Lopend", "Overeenkomst Ingediend"},
}


# ── Configuration ──

@dataclass(frozen=True)
class LifecycleConfig:
    """Immutable runtime configuration injected once at module creation."""
    agreements_dir: Path


# ── Return types ──

@dataclass(frozen=True)
class NewInternship:
    internship: Internship


@dataclass(frozen=True)
class ReviewDecision:
    internship: Internship


@dataclass(frozen=True)
class AgreementUpload:
    internship: Internship


# ── Deep Module ──

class InternshipLifecycle:
    """Encapsulates every legal status transition for the Internship aggregate."""

    def __init__(self, db: Session, config: LifecycleConfig) -> None:
        self.db = db
        self.config = config

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_internship_or_404(self, internship_id: int) -> Internship:
        internship = (
            self.db.query(Internship)
            .filter(Internship.id == internship_id)
            .first()
        )
        if not internship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Internship not found",
            )
        return internship

    @staticmethod
    def _can_access_internship(user: User, internship: Internship) -> bool:
        if user.role in {"committee", "admin"}:
            return True
        if user.role == "student":
            return internship.student_id == user.id
        if user.role == "mentor":
            return internship.mentor_id == user.id
        if user.role == "teacher":
            return internship.teacher_id == user.id
        return False

    def _assert_access(self, user: User, internship: Internship) -> None:
        if not self._can_access_internship(user, internship):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
            )

    def _assert_role(self, user: User, allowed: set[str]) -> None:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
            )

    def _assert_transition(self, from_status: str, to_status: str) -> None:
        legal = _TRANSITIONS.get(from_status, set())
        if to_status not in legal:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid transition: cannot move from "
                    f"'{from_status}' to '{to_status}'"
                ),
            )

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    # ------------------------------------------------------------------
    # Hot-path operations
    # ------------------------------------------------------------------

    def _validate_supervisor(self, user_id: Optional[int], expected_role: str) -> None:
        """Validate that the referenced user exists and has the expected role."""
        if user_id is None:
            return
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{expected_role.capitalize()} with id {user_id} not found",
            )
        if user.role != expected_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User {user_id} is not a {expected_role} (role: {user.role})",
            )

    def submit_internship(
        self,
        *,
        actor: User,
        company_name: str,
        company_address: Optional[str],
        company_sector: Optional[str],
        contact_person: str,
        contact_email: str,
        start_date: date,
        end_date: date,
        description: str,
        teacher_id: Optional[int] = None,
        mentor_id: Optional[int] = None,
    ) -> NewInternship:
        """Student creates a new Internship + Company + Proposal."""
        self._assert_role(actor, {"student"})

        self._validate_supervisor(teacher_id, "teacher")
        self._validate_supervisor(mentor_id, "mentor")

        company = Company(
            name=company_name,
            address=company_address,
            sector=company_sector,
            contact_person=contact_person,
            contact_email=contact_email,
        )
        self.db.add(company)
        self.db.flush()

        internship = Internship(
            student_id=actor.id,
            company_id=company.id,
            start_date=start_date,
            end_date=end_date,
            status="Ingediend",
            teacher_id=teacher_id,
            mentor_id=mentor_id,
        )
        self.db.add(internship)
        self.db.flush()

        proposal = Proposal(
            internship_id=internship.id,
            description=description,
            status="Ingediend",
        )
        self.db.add(proposal)

        self.db.commit()
        self.db.refresh(internship)
        return NewInternship(internship=internship)

    def review_proposal(
        self,
        *,
        internship_id: int,
        actor: User,
        decision: str,
        feedback: Optional[str] = None,
    ) -> ReviewDecision:
        """Committee evaluates a proposal."""
        self._assert_role(actor, {"committee", "admin"})

        internship = self._get_internship_or_404(internship_id)
        self._assert_access(actor, internship)

        if not internship.proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proposal not found",
            )

        self._assert_transition(internship.status, decision)

        if decision == "Aanpassingen Vereist" and not feedback:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Feedback is required when requesting changes",
            )

        internship.status = decision
        internship.proposal.status = decision
        if feedback is not None:
            internship.proposal.feedback = feedback

        self.db.commit()
        self.db.refresh(internship)
        return ReviewDecision(internship=internship)

    def upload_agreement(
        self,
        *,
        internship_id: int,
        actor: User,
        file_stream: BinaryIO,
        filename: str,
        content_type: str,
    ) -> AgreementUpload:
        """Student uploads a PDF agreement."""
        self._assert_role(actor, {"student"})

        internship = self._get_internship_or_404(internship_id)
        self._assert_access(actor, internship)

        if internship.student_id != actor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
            )

        self._assert_transition(internship.status, "Overeenkomst Ingediend")

        if content_type != "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed",
            )

        safe_name = f"agreement_{internship.id}_{self._now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = self.config.agreements_dir / safe_name
        self.config.agreements_dir.mkdir(parents=True, exist_ok=True)

        try:
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(file_stream, buffer)
        finally:
            if hasattr(file_stream, "close") and callable(file_stream.close):
                file_stream.close()

        if internship.agreement:
            agreement = internship.agreement
            agreement.file_path = str(filepath)
            agreement.status = "Ingediend"
            agreement.uploaded_at = self._now()
        else:
            agreement = Agreement(
                internship_id=internship.id,
                file_path=str(filepath),
                status="Ingediend",
                uploaded_at=self._now(),
            )
            self.db.add(agreement)

        internship.status = "Overeenkomst Ingediend"

        self.db.commit()
        self.db.refresh(internship)
        return AgreementUpload(internship=internship)

    # ------------------------------------------------------------------
    # Secondary operations
    # ------------------------------------------------------------------

    def edit_proposal(
        self,
        *,
        internship_id: int,
        actor: User,
        description: Optional[str] = None,
        company_name: Optional[str] = None,
        company_address: Optional[str] = None,
        company_sector: Optional[str] = None,
        contact_person: Optional[str] = None,
        contact_email: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> ReviewDecision:
        """Student edits their proposal while status is still 'Ingediend'."""
        self._assert_role(actor, {"student"})

        internship = self._get_internship_or_404(internship_id)
        self._assert_access(actor, internship)

        if internship.student_id != actor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
            )

        if not internship.proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proposal not found",
            )

        if internship.status != "Ingediend":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only edit proposals that have not yet been reviewed",
            )

        if description is not None:
            internship.proposal.description = description
        internship.proposal.submitted_at = self._now()

        # Update company details if provided
        if internship.company:
            if company_name is not None:
                internship.company.name = company_name
            if company_address is not None:
                internship.company.address = company_address
            if company_sector is not None:
                internship.company.sector = company_sector
            if contact_person is not None:
                internship.company.contact_person = contact_person
            if contact_email is not None:
                internship.company.contact_email = contact_email

        # Update internship dates if provided
        if start_date is not None:
            internship.start_date = start_date
        if end_date is not None:
            internship.end_date = end_date

        self.db.commit()
        self.db.refresh(internship)
        return ReviewDecision(internship=internship)

    def create_proposal(
        self,
        *,
        internship_id: int,
        actor: User,
        description: str,
    ) -> ReviewDecision:
        """Student creates a proposal for an existing internship."""
        self._assert_role(actor, {"student"})

        internship = self._get_internship_or_404(internship_id)
        self._assert_access(actor, internship)

        if internship.student_id != actor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
            )

        if internship.proposal:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Proposal already exists for this internship",
            )

        proposal = Proposal(
            internship_id=internship.id,
            description=description,
            status="Ingediend",
            submitted_at=self._now(),
        )
        self.db.add(proposal)

        internship.status = "Ingediend"

        self.db.commit()
        self.db.refresh(internship)
        return ReviewDecision(internship=internship)

    def resubmit_proposal(
        self,
        *,
        internship_id: int,
        actor: User,
        new_description: str,
        company_name: Optional[str] = None,
        company_address: Optional[str] = None,
        company_sector: Optional[str] = None,
        contact_person: Optional[str] = None,
        contact_email: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> ReviewDecision:
        """Student resubmits after 'Aanpassingen Vereist'."""
        self._assert_role(actor, {"student"})

        internship = self._get_internship_or_404(internship_id)
        self._assert_access(actor, internship)

        if internship.student_id != actor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
            )

        if not internship.proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proposal not found",
            )

        if internship.proposal.status != "Aanpassingen Vereist":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only resubmit when changes are requested",
            )

        self._assert_transition(internship.status, "In Beoordeling")

        internship.proposal.description = new_description
        internship.proposal.status = "In Beoordeling"
        internship.proposal.submitted_at = self._now()
        internship.proposal.feedback = None  # Clear old feedback
        internship.proposal.revision_count = (internship.proposal.revision_count or 0) + 1
        internship.proposal.resubmitted_at = self._now()
        internship.status = "In Beoordeling"

        # Update company details if provided
        if internship.company:
            if company_name is not None:
                internship.company.name = company_name
            if company_address is not None:
                internship.company.address = company_address
            if company_sector is not None:
                internship.company.sector = company_sector
            if contact_person is not None:
                internship.company.contact_person = contact_person
            if contact_email is not None:
                internship.company.contact_email = contact_email

        # Update internship dates if provided
        if start_date is not None:
            internship.start_date = start_date
        if end_date is not None:
            internship.end_date = end_date

        self.db.commit()
        self.db.refresh(internship)
        return ReviewDecision(internship=internship)

    def withdraw_proposal(
        self,
        *,
        internship_id: int,
        actor: User,
    ) -> Internship:
        """Student withdraws (deletes) their internship before it is reviewed.
        Only allowed when status is 'Ingediend'."""
        self._assert_role(actor, {"student"})

        internship = self._get_internship_or_404(internship_id)
        self._assert_access(actor, internship)

        if internship.student_id != actor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
            )

        if internship.status != "Ingediend":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only withdraw proposals that have not yet been reviewed",
            )

        self.db.delete(internship)
        self.db.commit()
        return internship

    def validate_agreement(
        self,
        *,
        internship_id: int,
        actor: User,
        insurance_verified: Optional[bool] = None,
        agreement_status: str,
    ) -> AgreementUpload:
        """Committee/admin validates an agreement."""
        self._assert_role(actor, {"committee", "admin"})

        internship = self._get_internship_or_404(internship_id)
        self._assert_access(actor, internship)

        if not internship.agreement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agreement not found",
            )

        if agreement_status not in {"Gevalideerd", "Onvolledig"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status",
            )

        agreement = internship.agreement
        if insurance_verified is not None:
            agreement.insurance_verified = insurance_verified
        agreement.status = agreement_status

        if agreement_status == "Gevalideerd":
            self._assert_transition(internship.status, "Lopend")
            agreement.validated_at = self._now()
            internship.status = "Lopend"

        self.db.commit()
        self.db.refresh(internship)
        return AgreementUpload(internship=internship)

    # ------------------------------------------------------------------
    # Admin escape hatch
    # ------------------------------------------------------------------

    def force_status(
        self,
        *,
        internship_id: int,
        actor: User,
        new_status: str,
        reason: str,
    ) -> Internship:
        """Admin-only override. Skips transition validation."""
        self._assert_role(actor, {"admin"})

        internship = self._get_internship_or_404(internship_id)

        # Audit logging not yet implemented (see docs/feature-todo.md #1)
        internship.status = new_status

        self.db.commit()
        self.db.refresh(internship)
        return internship
