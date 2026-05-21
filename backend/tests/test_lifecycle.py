"""Boundary tests for the InternshipLifecycle deep module.

These tests exercise business logic directly through the module interface
without spinning up FastAPI or HTTP.
"""

from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.models import Agreement, Company, Internship, Proposal, User
from app.services.lifecycle import InternshipLifecycle, LifecycleConfig


@pytest.fixture
def config(tmp_path):
    return LifecycleConfig(agreements_dir=tmp_path / "agreements")


class TestSubmitInternship:
    """Test internship creation via the lifecycle module."""

    def test_student_creates_internship(self, db, test_student, config):
        lifecycle = InternshipLifecycle(db, config)
        result = lifecycle.submit_internship(
            actor=test_student,
            company_name="TestCo",
            company_address="123 Main St",
            company_sector="IT",
            contact_person="Alice",
            contact_email="alice@testco.com",
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=120),
            description="Test internship",
        )

        internship = result.internship
        assert internship.status == "Ingediend"
        assert internship.student_id == test_student.id
        assert internship.company is not None
        assert internship.company.name == "TestCo"
        assert internship.proposal is not None
        assert internship.proposal.status == "Ingediend"
        assert internship.proposal.description == "Test internship"

    def test_non_student_cannot_submit(self, db, test_committee, config):
        lifecycle = InternshipLifecycle(db, config)
        with pytest.raises(HTTPException) as exc:
            lifecycle.submit_internship(
                actor=test_committee,
                company_name="TestCo",
                company_address=None,
                company_sector=None,
                contact_person="Alice",
                contact_email="alice@testco.com",
                start_date=date.today(),
                end_date=date.today(),
                description="Test",
            )
        assert exc.value.status_code == 403


class TestReviewProposal:
    """Test proposal review transitions."""

    @pytest.fixture
    def pending_internship(self, db, test_student, config):
        lifecycle = InternshipLifecycle(db, config)
        result = lifecycle.submit_internship(
            actor=test_student,
            company_name="TestCo",
            company_address=None,
            company_sector=None,
            contact_person="Alice",
            contact_email="alice@testco.com",
            start_date=date.today(),
            end_date=date.today(),
            description="Test",
        )
        return result.internship

    def test_committee_approves(self, db, pending_internship, test_committee, config):
        lifecycle = InternshipLifecycle(db, config)
        result = lifecycle.review_proposal(
            internship_id=pending_internship.id,
            actor=test_committee,
            decision="Goedgekeurd",
        )
        assert result.internship.status == "Goedgekeurd"
        assert result.internship.proposal.status == "Goedgekeurd"

    def test_committee_rejects(self, db, pending_internship, test_committee, config):
        lifecycle = InternshipLifecycle(db, config)
        result = lifecycle.review_proposal(
            internship_id=pending_internship.id,
            actor=test_committee,
            decision="Afgekeurd",
        )
        assert result.internship.status == "Afgekeurd"

    def test_committee_requests_changes_with_feedback(
        self, db, pending_internship, test_committee, config
    ):
        lifecycle = InternshipLifecycle(db, config)
        result = lifecycle.review_proposal(
            internship_id=pending_internship.id,
            actor=test_committee,
            decision="Aanpassingen Vereist",
            feedback="Needs more detail",
        )
        assert result.internship.status == "Aanpassingen Vereist"
        assert result.internship.proposal.feedback == "Needs more detail"

    def test_requests_changes_without_feedback_raises_400(
        self, db, pending_internship, test_committee, config
    ):
        lifecycle = InternshipLifecycle(db, config)
        with pytest.raises(HTTPException) as exc:
            lifecycle.review_proposal(
                internship_id=pending_internship.id,
                actor=test_committee,
                decision="Aanpassingen Vereist",
            )
        assert exc.value.status_code == 400

    def test_student_cannot_review(self, db, pending_internship, test_student, config):
        lifecycle = InternshipLifecycle(db, config)
        with pytest.raises(HTTPException) as exc:
            lifecycle.review_proposal(
                internship_id=pending_internship.id,
                actor=test_student,
                decision="Goedgekeurd",
            )
        assert exc.value.status_code == 403

    def test_illegal_transition_raises_400(
        self, db, pending_internship, test_committee, config
    ):
        lifecycle = InternshipLifecycle(db, config)
        with pytest.raises(HTTPException) as exc:
            lifecycle.review_proposal(
                internship_id=pending_internship.id,
                actor=test_committee,
                decision="Lopend",
            )
        assert exc.value.status_code == 400


class TestUploadAgreement:
    """Test agreement upload transitions and file persistence."""

    @pytest.fixture
    def approved_internship(self, db, test_student, test_committee, config):
        lifecycle = InternshipLifecycle(db, config)
        result = lifecycle.submit_internship(
            actor=test_student,
            company_name="TestCo",
            company_address=None,
            company_sector=None,
            contact_person="Alice",
            contact_email="alice@testco.com",
            start_date=date.today(),
            end_date=date.today(),
            description="Test",
        )
        lifecycle.review_proposal(
            internship_id=result.internship.id,
            actor=test_committee,
            decision="Goedgekeurd",
        )
        return result.internship

    def test_student_uploads_pdf(self, db, approved_internship, test_student, config):
        lifecycle = InternshipLifecycle(db, config)
        pdf = b"%PDF-1.4 fake pdf content"
        from io import BytesIO

        result = lifecycle.upload_agreement(
            internship_id=approved_internship.id,
            actor=test_student,
            file_stream=BytesIO(pdf),
            filename="agreement.pdf",
            content_type="application/pdf",
        )

        internship = result.internship
        assert internship.status == "Overeenkomst Ingediend"
        assert internship.agreement is not None
        assert internship.agreement.status == "Ingediend"
        assert Path(internship.agreement.file_path).exists()

    def test_non_pdf_rejected(self, db, approved_internship, test_student, config):
        lifecycle = InternshipLifecycle(db, config)
        from io import BytesIO

        with pytest.raises(HTTPException) as exc:
            lifecycle.upload_agreement(
                internship_id=approved_internship.id,
                actor=test_student,
                file_stream=BytesIO(b"not a pdf"),
                filename="agreement.txt",
                content_type="text/plain",
            )
        assert exc.value.status_code == 400

    def test_non_owner_cannot_upload(
        self, db, approved_internship, test_student, config
    ):
        # Create another student who does not own the internship
        other = User(
            email="other@test.com",
            password_hash="hash",
            first_name="Other",
            last_name="Student",
            role="student",
            is_active=True,
        )
        db.add(other)
        db.commit()

        lifecycle = InternshipLifecycle(db, config)
        from io import BytesIO

        with pytest.raises(HTTPException) as exc:
            lifecycle.upload_agreement(
                internship_id=approved_internship.id,
                actor=other,
                file_stream=BytesIO(b"%PDF-1.4 fake"),
                filename="agreement.pdf",
                content_type="application/pdf",
            )
        assert exc.value.status_code == 403


class TestValidateAgreement:
    """Test agreement validation transitions."""

    @pytest.fixture
    def uploaded_agreement(self, db, test_student, test_committee, config):
        lifecycle = InternshipLifecycle(db, config)
        result = lifecycle.submit_internship(
            actor=test_student,
            company_name="TestCo",
            company_address=None,
            company_sector=None,
            contact_person="Alice",
            contact_email="alice@testco.com",
            start_date=date.today(),
            end_date=date.today(),
            description="Test",
        )
        lifecycle.review_proposal(
            internship_id=result.internship.id,
            actor=test_committee,
            decision="Goedgekeurd",
        )
        from io import BytesIO

        lifecycle.upload_agreement(
            internship_id=result.internship.id,
            actor=test_student,
            file_stream=BytesIO(b"%PDF-1.4 fake"),
            filename="agreement.pdf",
            content_type="application/pdf",
        )
        return result.internship

    def test_committee_validates_to_lopend(
        self, db, uploaded_agreement, test_committee, config
    ):
        lifecycle = InternshipLifecycle(db, config)
        result = lifecycle.validate_agreement(
            internship_id=uploaded_agreement.id,
            actor=test_committee,
            insurance_verified=True,
            agreement_status="Gevalideerd",
        )
        internship = result.internship
        assert internship.status == "Lopend"
        assert internship.agreement.status == "Gevalideerd"
        assert internship.agreement.insurance_verified is True
        assert internship.agreement.validated_at is not None

    def test_committee_marks_onvolledig(
        self, db, uploaded_agreement, test_committee, config
    ):
        lifecycle = InternshipLifecycle(db, config)
        result = lifecycle.validate_agreement(
            internship_id=uploaded_agreement.id,
            actor=test_committee,
            agreement_status="Onvolledig",
        )
        internship = result.internship
        assert internship.status == "Overeenkomst Ingediend"  # unchanged
        assert internship.agreement.status == "Onvolledig"

    def test_invalid_status_raises_400(
        self, db, uploaded_agreement, test_committee, config
    ):
        lifecycle = InternshipLifecycle(db, config)
        with pytest.raises(HTTPException) as exc:
            lifecycle.validate_agreement(
                internship_id=uploaded_agreement.id,
                actor=test_committee,
                agreement_status="Geheim",
            )
        assert exc.value.status_code == 400


class TestResubmitProposal:
    """Test proposal resubmission."""

    @pytest.fixture
    def changes_requested(self, db, test_student, test_committee, config):
        lifecycle = InternshipLifecycle(db, config)
        result = lifecycle.submit_internship(
            actor=test_student,
            company_name="TestCo",
            company_address=None,
            company_sector=None,
            contact_person="Alice",
            contact_email="alice@testco.com",
            start_date=date.today(),
            end_date=date.today(),
            description="Original",
        )
        lifecycle.review_proposal(
            internship_id=result.internship.id,
            actor=test_committee,
            decision="Aanpassingen Vereist",
            feedback="Expand scope",
        )
        return result.internship

    def test_student_resubmits(self, db, changes_requested, test_student, config):
        lifecycle = InternshipLifecycle(db, config)
        result = lifecycle.resubmit_proposal(
            internship_id=changes_requested.id,
            actor=test_student,
            new_description="Expanded scope description",
        )
        internship = result.internship
        assert internship.status == "Ingediend"
        assert internship.proposal.status == "Ingediend"
        assert internship.proposal.description == "Expanded scope description"
        assert internship.proposal.submitted_at is not None

    def test_resubmit_without_changes_status_raises_400(
        self, db, test_student, test_committee, config
    ):
        # Create an internship already at Goedgekeurd
        lifecycle = InternshipLifecycle(db, config)
        result = lifecycle.submit_internship(
            actor=test_student,
            company_name="TestCo",
            company_address=None,
            company_sector=None,
            contact_person="Alice",
            contact_email="alice@testco.com",
            start_date=date.today(),
            end_date=date.today(),
            description="Test",
        )
        lifecycle.review_proposal(
            internship_id=result.internship.id,
            actor=test_committee,
            decision="Goedgekeurd",
        )

        # Resubmit from Goedgekeurd is illegal
        with pytest.raises(HTTPException) as exc:
            lifecycle.resubmit_proposal(
                internship_id=result.internship.id,
                actor=test_student,
                new_description="Nope",
            )
        assert exc.value.status_code == 400


class TestForceStatus:
    """Test admin override."""

    @pytest.fixture
    def any_internship(self, db, test_student, config):
        lifecycle = InternshipLifecycle(db, config)
        result = lifecycle.submit_internship(
            actor=test_student,
            company_name="TestCo",
            company_address=None,
            company_sector=None,
            contact_person="Alice",
            contact_email="alice@testco.com",
            start_date=date.today(),
            end_date=date.today(),
            description="Test",
        )
        return result.internship

    def test_admin_can_force_status(self, db, any_internship, test_admin, config):
        lifecycle = InternshipLifecycle(db, config)
        result = lifecycle.force_status(
            internship_id=any_internship.id,
            actor=test_admin,
            new_status="Afgerond",
            reason="Testing override",
        )
        assert result.status == "Afgerond"

    def test_non_admin_cannot_force(self, db, any_internship, test_committee, config):
        lifecycle = InternshipLifecycle(db, config)
        with pytest.raises(HTTPException) as exc:
            lifecycle.force_status(
                internship_id=any_internship.id,
                actor=test_committee,
                new_status="Afgerond",
                reason="Nope",
            )
        assert exc.value.status_code == 403
