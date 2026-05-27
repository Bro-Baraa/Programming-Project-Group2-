"""Tests for agreement endpoints including file download."""

import pytest
from pathlib import Path


class TestDownloadAgreement:
    """Test GET /internships/{id}/agreement/download"""

    def test_download_agreement_success(self, client, db, auth_headers_student, test_student, test_teacher):
        """Student can download their own agreement PDF."""
        from datetime import date, timedelta
        from app.models import Internship, Company, Proposal, Agreement

        # Create company, internship, proposal
        company = Company(name="Test Co", contact_person="John", contact_email="john@test.com")
        db.add(company)
        db.flush()

        internship = Internship(
            student_id=test_student.id,
            teacher_id=test_teacher.id,
            company_id=company.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status="Overeenkomst Ingediend",
        )
        db.add(internship)
        db.flush()

        proposal = Proposal(internship_id=internship.id, description="Test", status="Goedgekeurd")
        db.add(proposal)
        db.flush()

        # Create a fake PDF file on disk
        agreements_dir = Path("uploads/agreements")
        agreements_dir.mkdir(parents=True, exist_ok=True)
        fake_pdf = agreements_dir / f"agreement_{internship.id}_20240527_101010.pdf"
        fake_pdf.write_bytes(b"%PDF-1.4 fake pdf content")

        # Create agreement record pointing to the file
        agreement = Agreement(
            internship_id=internship.id,
            file_path=str(fake_pdf),
            status="Ingediend",
        )
        db.add(agreement)
        db.commit()

        response = client.get(
            f"/internships/{internship.id}/agreement/download",
            headers=auth_headers_student,
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "stage_overeenkomst_" in response.headers.get("content-disposition", "")
        assert response.content == b"%PDF-1.4 fake pdf content"

        # Clean up
        fake_pdf.unlink(missing_ok=True)

    def test_download_agreement_no_auth(self, client, sample_internship):
        """Unauthenticated requests are rejected."""
        response = client.get(f"/internships/{sample_internship.id}/agreement/download")
        assert response.status_code == 401

    def test_download_agreement_not_found(self, client, auth_headers_student, sample_internship):
        """404 when internship has no agreement."""
        response = client.get(
            f"/internships/{sample_internship.id}/agreement/download",
            headers=auth_headers_student,
        )
        assert response.status_code == 404
        assert "Agreement not found" in response.json()["detail"]

    def test_download_agreement_file_missing(self, client, db, auth_headers_student, test_student, test_teacher):
        """404 when agreement record exists but file is missing on disk."""
        from datetime import date, timedelta
        from app.models import Internship, Company, Proposal, Agreement

        company = Company(name="Test Co", contact_person="John", contact_email="john@test.com")
        db.add(company)
        db.flush()

        internship = Internship(
            student_id=test_student.id,
            teacher_id=test_teacher.id,
            company_id=company.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status="Overeenkomst Ingediend",
        )
        db.add(internship)
        db.flush()

        proposal = Proposal(internship_id=internship.id, description="Test", status="Goedgekeurd")
        db.add(proposal)
        db.flush()

        # Point to a non-existent file
        agreement = Agreement(
            internship_id=internship.id,
            file_path="uploads/agreements/nonexistent.pdf",
            status="Ingediend",
        )
        db.add(agreement)
        db.commit()

        response = client.get(
            f"/internships/{internship.id}/agreement/download",
            headers=auth_headers_student,
        )
        assert response.status_code == 404
        assert "file not found on disk" in response.json()["detail"]

    def test_download_agreement_unauthorized_role(self, client, db, auth_headers_student, test_student, test_teacher):
        """Student cannot download another student's agreement."""
        from datetime import date, timedelta
        from app.models import User, Internship, Company, Proposal, Agreement

        # Create another student
        other_student = User(
            email="other@test.com",
            password_hash="hashed",
            first_name="Other",
            last_name="Student",
            role="student",
            is_active=True,
        )
        db.add(other_student)
        db.flush()

        company = Company(name="Test Co", contact_person="John", contact_email="john@test.com")
        db.add(company)
        db.flush()

        internship = Internship(
            student_id=other_student.id,
            teacher_id=test_teacher.id,
            company_id=company.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status="Overeenkomst Ingediend",
        )
        db.add(internship)
        db.flush()

        proposal = Proposal(internship_id=internship.id, description="Test", status="Goedgekeurd")
        db.add(proposal)
        db.flush()

        agreements_dir = Path("uploads/agreements")
        agreements_dir.mkdir(parents=True, exist_ok=True)
        fake_pdf = agreements_dir / f"agreement_{internship.id}_20240527_101010.pdf"
        fake_pdf.write_bytes(b"fake content")

        agreement = Agreement(
            internship_id=internship.id,
            file_path=str(fake_pdf),
            status="Ingediend",
        )
        db.add(agreement)
        db.commit()

        response = client.get(
            f"/internships/{internship.id}/agreement/download",
            headers=auth_headers_student,
        )
        assert response.status_code == 403

        fake_pdf.unlink(missing_ok=True)