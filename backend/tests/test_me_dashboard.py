"""Tests for /me/dashboard endpoint."""

import pytest


class TestMeDashboardUnauthorized:
    """Auth requirements."""

    def test_dashboard_requires_auth(self, client):
        response = client.get("/api/me/dashboard")
        assert response.status_code == 401


class TestMeDashboardStudent:
    """Student view: sees their own internships, logbooks, evaluations, feedback."""

    def test_student_dashboard_empty(self, client, auth_headers_student):
        """Student with no internships gets empty but valid dashboard."""
        response = client.get("/api/me/dashboard", headers=auth_headers_student)
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "student@test.com"
        assert data["role"] == "student"
        assert data["internships"] == []
        assert data["stats"]["total_internships"] == 0
        assert data["alerts"] == []
        assert "generated_at" in data

    def test_student_dashboard_with_internship(
        self, client, auth_headers_student, sample_internship
    ):
        """Student sees their internship with computed summaries."""
        response = client.get("/api/me/dashboard", headers=auth_headers_student)
        assert response.status_code == 200
        data = response.json()

        assert len(data["internships"]) == 1
        item = data["internships"][0]

        # Internship summary
        assert item["internship"]["id"] == sample_internship.id
        assert item["internship"]["status"] == "Lopend"
        assert item["proposal_status"] == "Goedgekeurd"
        assert item["agreement_uploaded"] is False

        # Logbook summary (no logbooks yet)
        assert item["total_weeks"] > 0
        assert item["logbooks_submitted"] == 0
        assert item["logbooks_missing"] > 0
        assert item["next_due_week"] == 1

        # Evaluations
        assert item["evaluations_count"] == 0

        # Stats
        assert data["stats"]["total_internships"] == 1
        assert data["stats"]["ongoing"] == 1

    def test_student_dashboard_alert_for_missing_agreement(
        self, client, db, auth_headers_student, test_student, test_teacher
    ):
        """Student gets alert when proposal is approved but no agreement uploaded."""
        from datetime import date, timedelta
        from app.models import Internship, Company, Proposal

        company = Company(
            name="Test Co", contact_person="John", contact_email="john@test.com"
        )
        db.add(company)
        db.flush()

        internship = Internship(
            student_id=test_student.id,
            teacher_id=test_teacher.id,
            company_id=company.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status="Goedgekeurd",
        )
        db.add(internship)
        db.flush()

        proposal = Proposal(
            internship_id=internship.id, description="Test", status="Goedgekeurd"
        )
        db.add(proposal)
        db.commit()

        response = client.get("/api/me/dashboard", headers=auth_headers_student)
        assert response.status_code == 200
        data = response.json()

        # Should have an alert about uploading agreement
        alert = next(
            (a for a in data["alerts"] if "overeenkomst" in a["message"].lower()), None
        )
        assert alert is not None
        assert alert["severity"] == "warning"

    def test_student_dashboard_no_other_students_data(
        self, client, db, auth_headers_student, test_teacher
    ):
        """Student cannot see another student's internship on their dashboard."""
        from app.models import User, Internship, Company, Proposal
        from datetime import date, timedelta

        other = User(
            email="other@test.com",
            password_hash="hashed",
            first_name="Other",
            last_name="Student",
            role="student",
            is_active=True,
        )
        db.add(other)
        db.flush()

        company = Company(
            name="Other Co", contact_person="Jane", contact_email="jane@test.com"
        )
        db.add(company)
        db.flush()

        internship = Internship(
            student_id=other.id,
            teacher_id=test_teacher.id,
            company_id=company.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status="Lopend",
        )
        db.add(internship)
        db.flush()

        proposal = Proposal(
            internship_id=internship.id, description="Other", status="Goedgekeurd"
        )
        db.add(proposal)
        db.commit()

        response = client.get("/api/me/dashboard", headers=auth_headers_student)
        assert response.status_code == 200
        data = response.json()
        assert len(data["internships"]) == 0


class TestMeDashboardTeacher:
    """Teacher view: sees assigned internships."""

    def test_teacher_dashboard(self, client, auth_headers_teacher, sample_internship):
        """Teacher sees internships where they are assigned."""
        response = client.get("/api/me/dashboard", headers=auth_headers_teacher)
        assert response.status_code == 200
        data = response.json()

        assert data["user"]["role"] == "teacher"
        assert len(data["internships"]) == 1
        assert data["internships"][0]["internship"]["id"] == sample_internship.id
        assert data["stats"]["total_internships"] == 1

    def test_teacher_dashboard_empty(self, client, auth_headers_teacher):
        """Teacher with no assigned internships gets empty dashboard."""
        response = client.get("/api/me/dashboard", headers=auth_headers_teacher)
        assert response.status_code == 200
        data = response.json()
        assert data["internships"] == []
        assert data["stats"]["total_internships"] == 0


class TestMeDashboardCommittee:
    """Committee view: sees all internships."""

    def test_committee_sees_all(
        self, client, auth_headers_committee, sample_internship
    ):
        """Committee sees all internships in the system."""
        response = client.get("/api/me/dashboard", headers=auth_headers_committee)
        assert response.status_code == 200
        data = response.json()

        assert data["user"]["role"] == "committee"
        assert len(data["internships"]) >= 1
        ids = [i["internship"]["id"] for i in data["internships"]]
        assert sample_internship.id in ids

    def test_committee_alert_pending_proposal(
        self, client, db, auth_headers_committee, test_student
    ):
        """Committee gets alert for proposals waiting review."""
        from datetime import date, timedelta
        from app.models import Internship, Company, Proposal

        company = Company(
            name="New Co", contact_person="John", contact_email="john@test.com"
        )
        db.add(company)
        db.flush()

        internship = Internship(
            student_id=test_student.id,
            company_id=company.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status="In Beoordeling",
        )
        db.add(internship)
        db.flush()

        proposal = Proposal(
            internship_id=internship.id, description="Test", status="In Beoordeling"
        )
        db.add(proposal)
        db.commit()

        response = client.get("/api/me/dashboard", headers=auth_headers_committee)
        assert response.status_code == 200
        data = response.json()

        alert = next(
            (a for a in data["alerts"] if "beoordeling" in a["message"].lower()), None
        )
        assert alert is not None
        assert alert["severity"] == "warning"


class TestMeDashboardAdmin:
    """Admin view: sees everything."""

    def test_admin_dashboard(
        self, client, auth_headers_admin, test_admin, sample_internship
    ):
        """Admin sees all internships."""
        response = client.get("/api/me/dashboard", headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.json()

        assert data["user"]["role"] == "admin"
        assert len(data["internships"]) >= 1


class TestMeDashboardMentor:
    """Mentor view: sees mentored internships."""

    def test_mentor_dashboard(
        self, client, db, auth_headers_mentor, test_student, test_mentor
    ):
        """Mentor sees internships where they are assigned as mentor."""
        from datetime import date, timedelta
        from app.models import Internship, Company, Proposal

        company = Company(
            name="Mentor Co", contact_person="John", contact_email="john@test.com"
        )
        db.add(company)
        db.flush()

        internship = Internship(
            student_id=test_student.id,
            mentor_id=test_mentor.id,
            company_id=company.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status="Lopend",
        )
        db.add(internship)
        db.flush()

        proposal = Proposal(
            internship_id=internship.id, description="Test", status="Goedgekeurd"
        )
        db.add(proposal)
        db.commit()

        response = client.get("/api/me/dashboard", headers=auth_headers_mentor)
        assert response.status_code == 200
        data = response.json()

        assert data["user"]["role"] == "mentor"
        assert len(data["internships"]) == 1
        assert data["internships"][0]["internship"]["id"] == internship.id

    def test_mentor_dashboard_empty(self, client, auth_headers_mentor):
        """Mentor with no mentees gets empty dashboard."""
        response = client.get("/api/me/dashboard", headers=auth_headers_mentor)
        assert response.status_code == 200
        data = response.json()
        assert data["internships"] == []


class TestMeDashboardResponseShape:
    """Verify the response structure is consistent."""

    def test_response_has_all_required_fields(
        self, client, auth_headers_student, sample_internship
    ):
        response = client.get("/api/me/dashboard", headers=auth_headers_student)
        assert response.status_code == 200
        data = response.json()

        # Top-level keys
        assert "user" in data
        assert "role" in data
        assert "internships" in data
        assert "stats" in data
        assert "alerts" in data
        assert "generated_at" in data

        # User shape
        user = data["user"]
        assert "id" in user
        assert "email" in user
        assert "first_name" in user
        assert "last_name" in user
        assert "role" in user
        assert "password_hash" not in user
        assert "password" not in user

        # Internship item shape
        item = data["internships"][0]
        assert "internship" in item
        assert "proposal_status" in item
        assert "agreement_status" in item
        assert "agreement_uploaded" in item
        assert "total_weeks" in item
        assert "logbooks_submitted" in item
        assert "logbooks_missing" in item
        assert "logbooks_draft" in item
        assert "next_due_week" in item
        assert "evaluations_count" in item
        assert "evaluations_finalized" in item
        assert "latest_evaluation_status" in item
        assert "recent_feedback" in item

        # Stats shape
        stats = data["stats"]
        assert "total_internships" in stats
        assert "pending_approval" in stats
        assert "approved" in stats
        assert "rejected" in stats
        assert "ongoing" in stats
        assert "completed" in stats
        assert "agreements_received" in stats
        assert "agreements_pending" in stats
        assert "agreements_validated" in stats

        # Alert shape
        for alert in data["alerts"]:
            assert "severity" in alert
            assert "message" in alert
            assert alert["severity"] in ("info", "warning", "error")
