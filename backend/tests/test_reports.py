"""Tests for reporting endpoints: final report, agreements report, PDF export."""

import pytest
from datetime import date, timedelta
from app.models import (
    Company,
    Internship,
    Proposal,
    Agreement,
    Logbook,
    Evaluation,
    EvaluationRule,
    Notification,
)


@pytest.fixture
def completed_internship(db, test_student, test_teacher, sample_competencies):
    """Create a completed internship with all data for final report."""
    company = Company(
        name="Final Corp", contact_person="Final", contact_email="final@corp.com"
    )
    db.add(company)
    db.flush()

    internship = Internship(
        student_id=test_student.id,
        teacher_id=test_teacher.id,
        company_id=company.id,
        start_date=date.today() - timedelta(days=90),
        end_date=date.today() - timedelta(days=10),
        status="Afgerond",
    )
    db.add(internship)
    db.flush()

    proposal = Proposal(
        internship_id=internship.id,
        description="Final proposal",
        status="Goedgekeurd",
    )
    db.add(proposal)
    db.flush()

    agreement = Agreement(
        internship_id=internship.id,
        file_path="/uploads/agreement.pdf",
        status="Gevalideerd",
    )
    db.add(agreement)
    db.flush()

    # Create some logbooks
    for week in range(1, 5):
        lb = Logbook(
            internship_id=internship.id,
            week_number=week,
            tasks=f"Week {week} tasks",
            status="submitted",
        )
        db.add(lb)
    db.flush()

    # Create finalized final evaluation
    evaluation = Evaluation(
        internship_id=internship.id,
        evaluator_id=test_teacher.id,
        eval_type="final",
        status="afgerond",
        finalized=True,
        finalized_at=date.today(),
    )
    db.add(evaluation)
    db.flush()

    # Score all rules
    for comp in sample_competencies:
        rule = EvaluationRule(
            evaluation_id=evaluation.id,
            competency_id=comp.id,
            score=4,
            weight_snapshot=comp.weight,
        )
        db.add(rule)

    db.commit()
    db.refresh(internship)
    return internship


class TestFinalReportJson:
    """Test GET /internships/{id}/final-report"""

    def test_get_final_report(self, client, auth_headers_teacher, completed_internship):
        """Teacher can get final report for assigned internship."""
        response = client.get(
            f"/api/internships/{completed_internship.id}/final-report",
            headers=auth_headers_teacher,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["internship_id"] == completed_internship.id
        assert data["student"]["email"] == "student@test.com"
        assert data["company_name"] == "Final Corp"
        assert data["proposal_status"] == "Goedgekeurd"
        assert data["agreement_status"] == "Gevalideerd"
        assert data["total_weeks"] == 12
        assert data["submitted_logbooks"] == 4
        assert data["missing_logbooks"] == 8
        assert data["final_evaluation"] is not None
        assert data["weighted_final_score"] is not None
        assert data["weighted_final_score"] > 0

    def test_get_final_report_student_own(
        self, client, auth_headers_student, completed_internship
    ):
        """Student can get their own final report."""
        response = client.get(
            f"/api/internships/{completed_internship.id}/final-report",
            headers=auth_headers_student,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["student"]["id"] == completed_internship.student_id

    def test_get_final_report_not_found(self, client, auth_headers_teacher):
        """404 for non-existent internship."""
        response = client.get(
            "/api/internships/99999/final-report", headers=auth_headers_teacher
        )
        assert response.status_code == 404

    def test_get_final_report_unauthorized(
        self, client, db, auth_headers_teacher, test_student
    ):
        """Teacher cannot get final report for another teacher's internship."""
        # Create another teacher
        from app.auth import get_password_hash
        from app.models import User

        other_teacher = User(
            email="other_teacher@test.com",
            password_hash=get_password_hash("teacher123"),
            first_name="Other",
            last_name="Teacher",
            role="teacher",
            is_active=True,
        )
        db.add(other_teacher)
        db.flush()

        company = Company(
            name="Other Corp",
            contact_person="Other",
            contact_email="other@corp.com",
        )
        db.add(company)
        db.flush()

        internship = Internship(
            student_id=test_student.id,
            teacher_id=other_teacher.id,
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

        response = client.get(
            f"/api/internships/{internship.id}/final-report",
            headers=auth_headers_teacher,
        )
        assert response.status_code == 403

    def test_get_final_report_no_evaluation(
        self, client, db, auth_headers_teacher, sample_internship
    ):
        """Final report works even without a finalized evaluation."""
        response = client.get(
            f"/api/internships/{sample_internship.id}/final-report",
            headers=auth_headers_teacher,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["final_evaluation"] is None
        assert data["weighted_final_score"] is None


class TestFinalReportPdf:
    """Test GET /internships/{id}/final-report/pdf"""

    def test_get_final_report_pdf(
        self, client, auth_headers_teacher, completed_internship
    ):
        """Teacher can download final report PDF."""
        response = client.get(
            f"/api/internships/{completed_internship.id}/final-report/pdf",
            headers=auth_headers_teacher,
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert "eindrapport_" in response.headers["content-disposition"]
        assert len(response.content) > 0

    def test_get_final_report_pdf_student(
        self, client, auth_headers_student, completed_internship
    ):
        """Student can download their own final report PDF."""
        response = client.get(
            f"/api/internships/{completed_internship.id}/final-report/pdf",
            headers=auth_headers_student,
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_get_final_report_pdf_not_found(self, client, auth_headers_teacher):
        """404 for non-existent internship."""
        response = client.get(
            "/api/internships/99999/final-report/pdf", headers=auth_headers_teacher
        )
        assert response.status_code == 404


class TestAgreementStatusReport:
    """Test GET /internships/reports/agreements"""

    @pytest.fixture
    def internships_with_agreements(self, db, test_student, test_teacher):
        """Create internships with various agreement statuses."""
        configs = [
            {"status": "Goedgekeurd", "agreement": None},
            {"status": "Overeenkomst Ingediend", "agreement": "Ingediend"},
            {"status": "Lopend", "agreement": "Gevalideerd"},
            {"status": "Afgerond", "agreement": "Gevalideerd"},
        ]
        created = []
        for i, config in enumerate(configs):
            company = Company(
                name=f"Agree Corp {i}",
                contact_person=f"Agree {i}",
                contact_email=f"agree{i}@corp.com",
            )
            db.add(company)
            db.flush()

            internship = Internship(
                student_id=test_student.id,
                teacher_id=test_teacher.id,
                company_id=company.id,
                start_date=date.today(),
                end_date=date.today() + timedelta(days=30),
                status=config["status"],
            )
            db.add(internship)
            db.flush()

            proposal = Proposal(
                internship_id=internship.id,
                description=f"Desc {i}",
                status="Goedgekeurd",
            )
            db.add(proposal)
            db.flush()

            if config["agreement"]:
                agreement = Agreement(
                    internship_id=internship.id,
                    file_path="/uploads/agreement.pdf",
                    status=config["agreement"],
                )
                db.add(agreement)
                db.flush()

            created.append(internship)

        db.commit()
        return created

    def test_agreement_status_report(
        self, client, auth_headers_committee, internships_with_agreements
    ):
        """Committee can get agreement status report."""
        response = client.get(
            "/api/internships/reports/agreements", headers=auth_headers_committee
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4
        # Check that all items have required fields
        for item in data:
            assert "internship_id" in item
            assert "student" in item
            assert "status" in item
            assert "agreement_status" in item

    def test_agreement_status_report_teacher(
        self, client, auth_headers_teacher, internships_with_agreements
    ):
        """Teacher can get agreement status report for their internships."""
        response = client.get(
            "/api/internships/reports/agreements", headers=auth_headers_teacher
        )
        assert response.status_code == 200
        data = response.json()
        # Teacher only sees their own internships
        assert len(data) == 4
        assert all(item["student"]["email"] == "student@test.com" for item in data)

    def test_agreement_status_report_student_rejected(
        self, client, auth_headers_student
    ):
        """Students cannot access agreement status report."""
        response = client.get(
            "/api/internships/reports/agreements", headers=auth_headers_student
        )
        assert response.status_code == 403

    def test_agreement_status_report_no_auth(self, client):
        """Unauthenticated requests are rejected."""
        response = client.get("/api/internships/reports/agreements")
        assert response.status_code == 401
