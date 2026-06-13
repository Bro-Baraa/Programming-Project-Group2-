"""Stage lifecycle service."""

from dataclasses import dataclass
from datetime import date, datetime, UTC
from pathlib import Path
from typing import BinaryIO, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import (
    Agreement,
    Company,
    CompetencyProfile,
    Internship,
    Proposal,
    ProposalVersion,
    User,
)
from app.services.notifications import notify
from app.services.common import (
    ensure_internship_access,
    get_active_competency_profile,
)

_TRANSITIONS: dict[str, set[str]] = {
    "Ingediend": {"In Beoordeling"},
    "In Beoordeling": {"Goedgekeurd", "Afgekeurd", "Aanpassingen Vereist"},
    "Aanpassingen Vereist": {"In Beoordeling"},
    "Goedgekeurd": {"Overeenkomst Ingediend", "Stopgezet"},
    "Overeenkomst Ingediend": {"Lopend", "Overeenkomst Ingediend", "Stopgezet"},
    "Lopend": {"Afgerond", "Overeenkomst Ingediend", "Stopgezet"},
    "Afgerond": set(),  # terminal state
    "Stopgezet": set(),  # terminal state — stage vroegtijdig beëindigd
}


@dataclass(frozen=True)
class LifecycleConfig:

    agreements_dir: Path


class InternshipLifecycle:

    def __init__(self, db: Session, config: LifecycleConfig) -> None:
        self.db = db
        self.config = config

    def _get_internship_or_404(self, internship_id: int) -> Internship:
        internship = (
            self.db.query(Internship).filter(Internship.id == internship_id).first()
        )
        if not internship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Internship not found",
            )
        return internship

    def _assert_access(self, user: User, internship: Internship) -> None:
        ensure_internship_access(user, internship)

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

    def _notify_committee(
        self, message: str, link_view: str, internship_id=None
    ) -> None:
        for member in (
            self.db.query(User)
            .filter(User.role == "committee", User.is_active == True)
            .all()
        ):
            notify(
                self.db,
                user_id=member.id,
                message=message,
                internship_id=internship_id,
                link_view=link_view,
            )

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    def _validate_supervisor(self, user_id: Optional[int], expected_role: str) -> None:
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
                detail=f"User {user_id} is not a {expected_role}",
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
    ) -> Internship:
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

        active_profile = get_active_competency_profile(self.db)

        internship = Internship(
            student_id=actor.id,
            company_id=company.id,
            start_date=start_date,
            end_date=end_date,
            status="Ingediend",
            teacher_id=teacher_id,
            mentor_id=mentor_id,
            competency_profile_id=active_profile.id if active_profile else None,
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

        student_name = f"{actor.first_name} {actor.last_name}"
        self._notify_committee(
            f"{student_name} heeft een nieuw stagevoorstel ingediend.",
            "voorstellen",
            internship.id,
        )

        if mentor_id:
            notify(
                self.db,
                user_id=mentor_id,
                message=f"Je bent aangeduid als mentor voor de stage van {student_name}.",
                internship_id=internship.id,
                link_view="logboek",
            )

        self.db.commit()

        return internship

    def review_proposal(
        self,
        *,
        internship_id: int,
        actor: User,
        decision: str,
        feedback: Optional[str] = None,
        teacher_id: Optional[int] = None,
        mentor_id: Optional[int] = None,
    ) -> Internship:
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

        if decision == "Goedgekeurd":
            if not teacher_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Een docent moet worden aangeduid bij goedkeuring",
                )
            self._validate_supervisor(teacher_id, "teacher")
            internship.teacher_id = teacher_id

            # Mentor aanduiden bij goedkeuring (optioneel — kan later via PATCH)
            if mentor_id:
                self._validate_supervisor(mentor_id, "mentor")
                internship.mentor_id = mentor_id

        internship.status = decision
        internship.proposal.status = decision
        if feedback is not None:
            internship.proposal.feedback = feedback

        messages = {
            "In Beoordeling": "Je stagevoorstel wordt beoordeeld door de commissie.",
            "Goedgekeurd": "Gefeliciteerd! Je stagevoorstel is goedgekeurd.",
            "Afgekeurd": "Je stagevoorstel is helaas afgekeurd. Bekijk de feedback.",
            "Aanpassingen Vereist": "Je stagevoorstel vereist aanpassingen. Bekijk de feedback.",
        }
        if decision in messages:
            notify(
                self.db,
                user_id=internship.student_id,
                message=messages[decision],
                internship_id=internship.id,
                link_view="voorstel",
            )

        if decision == "Goedgekeurd" and teacher_id:
            student_name = (
                f"{internship.student.first_name} {internship.student.last_name}"
            )
            notify(
                self.db,
                user_id=teacher_id,
                message=f"Je bent aangeduid als docent-begeleider voor de stage van {student_name}.",
                internship_id=internship.id,
                link_view="logboek",
            )

        if decision == "Goedgekeurd" and mentor_id:
            notify(
                self.db,
                user_id=mentor_id,
                message=f"Je bent aangeduid als mentor voor de stage van {student_name}.",
                internship_id=internship.id,
                link_view="logboek",
            )

        self.db.commit()
        self.db.refresh(internship)
        return internship

    def upload_agreement(
        self,
        *,
        internship_id: int,
        actor: User,
        file_stream: BinaryIO,
        filename: str,
        content_type: str,
    ) -> Internship:
        self._assert_role(actor, {"student"})

        internship = self._get_internship_or_404(internship_id)
        self._assert_access(actor, internship)

        self._assert_transition(internship.status, "Overeenkomst Ingediend")

        if content_type != "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed",
            )

        safe_name = (
            f"agreement_{internship.id}_{self._now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        filepath = self.config.agreements_dir / safe_name
        self.config.agreements_dir.mkdir(parents=True, exist_ok=True)

        MAX_SIZE = 5 * 1024 * 1024
        content = bytearray()
        chunk = file_stream.read(8192)
        while chunk:
            content.extend(chunk)
            if len(content) > MAX_SIZE:
                if hasattr(file_stream, "close") and callable(file_stream.close):
                    file_stream.close()
                raise HTTPException(
                    status_code=413,
                    detail="File too large. Maximum size is 5 MB.",
                )
            chunk = file_stream.read(8192)

        try:
            with open(filepath, "wb") as buffer:
                buffer.write(content)
        finally:
            if hasattr(file_stream, "close") and callable(file_stream.close):
                file_stream.close()

        if internship.agreement:
            agreement = internship.agreement
            agreement.file_path = str(filepath)
            agreement.status = "Ingediend"
            agreement.insurance_verified = False
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

        # We notify via a simple approach: store one notification per committee member.
        self._notify_committee(
            (
                f"{internship.student.first_name} {internship.student.last_name} heeft een stageovereenkomst geüpload."
                if internship.student
                else "Een student heeft een stageovereenkomst geüpload."
            ),
            "overeenkomsten",
            internship.id,
        )

        self.db.commit()
        self.db.refresh(internship)
        return internship

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
    ) -> Internship:
        self._assert_role(actor, {"student"})

        internship = self._get_internship_or_404(internship_id)
        self._assert_access(actor, internship)

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

        # Save current version to history before editing
        old_version = ProposalVersion(
            proposal_id=internship.proposal.id,
            version=internship.proposal.version,
            description=internship.proposal.description,
            status=internship.proposal.status,
            feedback=internship.proposal.feedback,
            submitted_at=internship.proposal.submitted_at,
            resubmitted_at=internship.proposal.resubmitted_at,
        )
        self.db.add(old_version)

        if description is not None:
            internship.proposal.description = description
        internship.proposal.version = (internship.proposal.version or 1) + 1
        internship.proposal.revised_at = self._now()
        internship.proposal.submitted_at = self._now()

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

        if start_date is not None:
            internship.start_date = start_date
        if end_date is not None:
            internship.end_date = end_date

        self.db.commit()
        self.db.refresh(internship)
        return internship

    def create_proposal(
        self,
        *,
        internship_id: int,
        actor: User,
        description: str,
    ) -> Internship:
        self._assert_role(actor, {"student"})

        internship = self._get_internship_or_404(internship_id)
        self._assert_access(actor, internship)

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
        return internship

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
    ) -> Internship:
        self._assert_role(actor, {"student"})

        internship = self._get_internship_or_404(internship_id)
        self._assert_access(actor, internship)

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

        # Save current version to history before resubmitting
        old_version = ProposalVersion(
            proposal_id=internship.proposal.id,
            version=internship.proposal.version,
            description=internship.proposal.description,
            status=internship.proposal.status,
            feedback=internship.proposal.feedback,
            submitted_at=internship.proposal.submitted_at,
            resubmitted_at=internship.proposal.resubmitted_at,
        )
        self.db.add(old_version)

        internship.proposal.description = new_description
        internship.proposal.status = "In Beoordeling"
        internship.proposal.submitted_at = self._now()
        internship.proposal.feedback = None
        internship.proposal.revision_count = (
            internship.proposal.revision_count or 0
        ) + 1
        internship.proposal.resubmitted_at = self._now()
        internship.proposal.version = (internship.proposal.version or 1) + 1
        internship.proposal.revised_at = self._now()
        internship.status = "In Beoordeling"

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

        if start_date is not None:
            internship.start_date = start_date
        if end_date is not None:
            internship.end_date = end_date

        self.db.commit()
        self.db.refresh(internship)

        self._notify_committee(
            f"{actor.first_name} {actor.last_name} heeft zijn/haar stagevoorstel opnieuw ingediend na aanpassingen.",
            "voorstellen",
            internship.id,
        )
        self.db.commit()

        return internship

    def withdraw_proposal(
        self,
        *,
        internship_id: int,
        actor: User,
    ) -> Internship:

        self._assert_role(actor, {"student"})

        internship = self._get_internship_or_404(internship_id)
        self._assert_access(actor, internship)

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
    ) -> Internship:
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
            if not agreement.insurance_verified:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insurance must be verified before validating the agreement",
                )
            self._assert_transition(internship.status, "Lopend")
            agreement.validated_at = self._now()
            internship.status = "Lopend"
            notify(
                self.db,
                user_id=internship.student_id,
                message="Je stageovereenkomst is gevalideerd. Je stage is nu actief!",
                internship_id=internship.id,
                link_view="overeenkomst",
            )
            if internship.mentor_id:
                notify(
                    self.db,
                    user_id=internship.mentor_id,
                    message="De stageovereenkomst is gevalideerd. De stage is nu actief.",
                    internship_id=internship.id,
                    link_view="logboek",
                )
        elif agreement_status == "Onvolledig":
            # Revert internship status so student can re-upload (only if already running)
            if internship.status == "Lopend":
                self._assert_transition(internship.status, "Overeenkomst Ingediend")
                internship.status = "Overeenkomst Ingediend"
            notify(
                self.db,
                user_id=internship.student_id,
                message="Je stageovereenkomst is onvolledig. Gelieve een nieuwe versie te uploaden.",
                internship_id=internship.id,
                link_view="overeenkomst",
            )

        self.db.commit()
        self.db.refresh(internship)
        return internship

    def complete_internship(
        self,
        *,
        internship_id: int,
        actor: User,
    ) -> Internship:

        self._assert_role(actor, {"teacher", "committee", "admin"})

        internship = self._get_internship_or_404(internship_id)
        self._assert_access(actor, internship)

        self._assert_transition(internship.status, "Afgerond")
        internship.status = "Afgerond"

        notify(
            self.db,
            user_id=internship.student_id,
            message="Je stage is afgerond. Gefeliciteerd!",
            internship_id=internship.id,
            link_view="dashboard",
        )
        if internship.mentor_id:
            notify(
                self.db,
                user_id=internship.mentor_id,
                message="De stage is afgerond.",
                internship_id=internship.id,
                link_view="logboek",
            )

        self.db.commit()
        self.db.refresh(internship)
        return internship

    def terminate_internship(
        self,
        *,
        internship_id: int,
        actor: User,
        reason: str,
    ) -> Internship:
        """Zet een stage vroegtijdig stop (bv. student stopt, bedrijf trekt zich terug).

        Alleen commissie en admin mogen dit. Een reden is verplicht en wordt
        vastgelegd in de auditlog. De betrokkenen (student, mentor, docent)
        krijgen een notificatie. 'Stopgezet' is een eindstatus.
        """
        self._assert_role(actor, {"committee", "admin"})

        internship = self._get_internship_or_404(internship_id)
        self._assert_access(actor, internship)

        # Reden is verplicht — zonder reden mag een stage niet stopgezet worden.
        if not reason or not reason.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Een reden is verplicht om een stage stop te zetten",
            )

        # Controleer of de overgang naar 'Stopgezet' is toegestaan vanuit de huidige status
        # (kan vanuit Goedgekeurd, Overeenkomst Ingediend of Lopend).
        self._assert_transition(internship.status, "Stopgezet")
        internship.status = "Stopgezet"

        # Auditlog: leg vast wie de stage stopzette en waarom.
        from app.services.audit import log_event

        log_event(
            self.db,
            "internship.terminate",
            user=actor,
            entity_type="internship",
            entity_id=internship.id,
            detail=f"Stage vroegtijdig stopgezet. Reden: {reason.strip()}",
        )

        # Notificatie naar de student (met de opgegeven reden).
        notify(
            self.db,
            user_id=internship.student_id,
            message=f"Je stage is vroegtijdig stopgezet. Reden: {reason.strip()}",
            internship_id=internship.id,
            link_view="dashboard",
        )
        # Notificatie naar de mentor, indien toegewezen.
        if internship.mentor_id:
            notify(
                self.db,
                user_id=internship.mentor_id,
                message="De stage is vroegtijdig stopgezet door de opleiding.",
                internship_id=internship.id,
                link_view="logboek",
            )
        # Notificatie naar de docent-begeleider, indien toegewezen.
        if internship.teacher_id:
            notify(
                self.db,
                user_id=internship.teacher_id,
                message="De stage is vroegtijdig stopgezet door de opleiding.",
                internship_id=internship.id,
                link_view="opvolging",
            )

        self.db.commit()
        self.db.refresh(internship)
        return internship

    def force_status(
        self,
        *,
        internship_id: int,
        actor: User,
        new_status: str,
        reason: str,
    ) -> Internship:
        self._assert_role(actor, {"admin"})

        internship = self._get_internship_or_404(internship_id)

        from app.services.audit import log_event

        log_event(
            self.db,
            "internship.force_status",
            user=actor,
            entity_type="internship",
            entity_id=internship_id,
            detail=f"Status handmatig gewijzigd naar '{new_status}' door admin. Reden: {reason}",
        )
        internship.status = new_status

        self.db.commit()
        self.db.refresh(internship)
        return internship
