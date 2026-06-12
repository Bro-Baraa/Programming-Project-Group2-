"""Tests for logbook week overview endpoint."""

import pytest
from datetime import date, timedelta
from app.models import Company, Internship, Proposal, Logbook


class TestWeekOverview:
    """Test GET /internships/{id}/logbooks/weeks"""

    @pytest.fixture
    def internship_with_dates(self, db, test_student):
        """Create an internship with valid start/end dates."""
        company = Company(
            name="Week Corp", contact_person="Week", contact_email="week@corp.com"
        )
        db.add(company)
        db.flush()

        internship = Internship(
            student_id=test_student.id,
            company_id=company.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=20),
            status="Lopend",
        )
        db.add(internship)
        db.flush()

        proposal = Proposal(
            internship_id=internship.id, description="Week test", status="Goedgekeurd"
        )
        db.add(proposal)
        db.commit()
        db.refresh(internship)
        return internship

    def test_week_overview_empty(
        self, client, auth_headers_student, internship_with_dates
    ):
        """Week overview shows all weeks as missing when no logbooks."""
        response = client.get(
            f"/api/internships/{internship_with_dates.id}/logbooks/weeks",
            headers=auth_headers_student,
        )
        assert response.status_code == 200
        data = response.json()
        # 20 days = ~3 weeks
        assert len(data) == 3
        for week in data:
            assert week["status"] == "missing"
            assert week["logbook_id"] is None
            assert week["mentor_validated"] is False

    def test_week_overview_with_logbooks(
        self, client, db, auth_headers_student, internship_with_dates
    ):
        """Week overview shows correct status for existing logbooks."""
        # Create logbooks for weeks 1 and 2
        for week_num in [1, 2]:
            lb = Logbook(
                internship_id=internship_with_dates.id,
                week_number=week_num,
                tasks=f"Week {week_num}",
                status="draft" if week_num == 1 else "submitted",
            )
            db.add(lb)
        db.commit()

        response = client.get(
            f"/api/internships/{internship_with_dates.id}/logbooks/weeks",
            headers=auth_headers_student,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["week_number"] == 1
        assert data[0]["status"] == "draft"
        assert data[1]["week_number"] == 2
        assert data[1]["status"] == "submitted"
        assert data[2]["week_number"] == 3
        assert data[2]["status"] == "missing"

    def test_week_overview_mentor_access(
        self, client, db, auth_headers_mentor, test_student, test_mentor
    ):
        """Mentor can access week overview for assigned internship."""
        company = Company(
            name="Mentor Corp",
            contact_person="Mentor",
            contact_email="mentor@corp.com",
        )
        db.add(company)
        db.flush()

        internship = Internship(
            student_id=test_student.id,
            mentor_id=test_mentor.id,
            company_id=company.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=20),
            status="Lopend",
        )
        db.add(internship)
        db.flush()

        proposal = Proposal(
            internship_id=internship.id, description="Mentor test", status="Goedgekeurd"
        )
        db.add(proposal)
        db.commit()

        response = client.get(
            f"/api/internships/{internship.id}/logbooks/weeks",
            headers=auth_headers_mentor,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_week_overview_dates_not_set(
        self, client, db, auth_headers_student, test_student
    ):
        """400 when internship dates are not set."""
        company = Company(
            name="NoDate Corp",
            contact_person="NoDate",
            contact_email="nodate@corp.com",
        )
        db.add(company)
        db.flush()

        internship = Internship(
            student_id=test_student.id,
            company_id=company.id,
            status="Ingediend",
        )
        db.add(internship)
        db.flush()

        proposal = Proposal(
            internship_id=internship.id, description="No dates", status="Ingediend"
        )
        db.add(proposal)
        db.commit()

        response = client.get(
            f"/api/internships/{internship.id}/logbooks/weeks",
            headers=auth_headers_student,
        )
        assert response.status_code == 400
        assert "Internship dates not set" in response.json()["detail"]

    def test_week_overview_invalid_dates(
        self, client, db, auth_headers_student, test_student
    ):
        """400 when end_date is before start_date (negative total_weeks)."""
        company = Company(
            name="BadDate Corp",
            contact_person="BadDate",
            contact_email="baddate@corp.com",
        )
        db.add(company)
        db.flush()

        internship = Internship(
            student_id=test_student.id,
            company_id=company.id,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today(),
            status="Lopend",
        )
        db.add(internship)
        db.flush()

        proposal = Proposal(
            internship_id=internship.id, description="Bad dates", status="Goedgekeurd"
        )
        db.add(proposal)
        db.commit()

        response = client.get(
            f"/api/internships/{internship.id}/logbooks/weeks",
            headers=auth_headers_student,
        )
        assert response.status_code == 400
        assert "einddatum ligt voor startdatum" in response.json()["detail"]

    def test_week_overview_not_found(self, client, auth_headers_student):
        """404 for non-existent internship."""
        response = client.get(
            "/api/internships/99999/logbooks/weeks", headers=auth_headers_student
        )
        assert response.status_code == 404

    def test_week_overview_unauthorized(
        self, client, db, auth_headers_student, test_student
    ):
        """Student cannot access another student's week overview."""
        from app.auth import get_password_hash
        from app.models import User

        other_student = User(
            email="other_student@test.com",
            password_hash=get_password_hash("other123"),
            first_name="Other",
            last_name="Student",
            role="student",
            is_active=True,
        )
        db.add(other_student)
        db.flush()

        company = Company(
            name="Other Corp",
            contact_person="Other",
            contact_email="other@corp.com",
        )
        db.add(company)
        db.flush()

        internship = Internship(
            student_id=other_student.id,
            company_id=company.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=20),
            status="Lopend",
        )
        db.add(internship)
        db.flush()

        proposal = Proposal(
            internship_id=internship.id, description="Other", status="Goedgekeurd"
        )
        db.add(proposal)
        db.commit()

        response = client.get(
            f"/api/internships/{internship.id}/logbooks/weeks",
            headers=auth_headers_student,
        )
        assert response.status_code == 403
