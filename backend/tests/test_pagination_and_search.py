"""Tests for pagination, search, and filter on list endpoints."""

import pytest


class TestInternshipPagination:
    """Test GET /internships with pagination."""

    def test_default_pagination(self, client, auth_headers_admin, db, test_admin):
        """Default limit is 50, skip is 0."""
        from datetime import date, timedelta
        from app.models import Internship, Company, Proposal

        # Create 3 internships
        for i in range(3):
            company = Company(
                name=f"Co{i}", contact_person="J", contact_email="j@test.com"
            )
            db.add(company)
            db.flush()
            intern = Internship(
                student_id=test_admin.id,
                company_id=company.id,
                start_date=date.today(),
                end_date=date.today() + timedelta(days=30),
                status="Ingediend",
            )
            db.add(intern)
            db.flush()
            db.add(
                Proposal(internship_id=intern.id, description="D", status="Ingediend")
            )
        db.commit()

        response = client.get("/api/internships", headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert response.headers.get("X-Total-Count") == "3"

    def test_skip_and_limit(self, client, auth_headers_admin, db, test_admin):
        """skip and limit params work correctly."""
        from datetime import date, timedelta
        from app.models import Internship, Company, Proposal

        for i in range(5):
            company = Company(
                name=f"Co{i}", contact_person="J", contact_email="j@test.com"
            )
            db.add(company)
            db.flush()
            intern = Internship(
                student_id=test_admin.id,
                company_id=company.id,
                start_date=date.today(),
                end_date=date.today() + timedelta(days=30),
                status="Ingediend",
            )
            db.add(intern)
            db.flush()
            db.add(
                Proposal(internship_id=intern.id, description="D", status="Ingediend")
            )
        db.commit()

        # Page 1: first 2
        response = client.get(
            "/api/internships?skip=0&limit=2", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert response.headers.get("X-Total-Count") == "5"

        # Page 2: next 2
        response = client.get(
            "/api/internships?skip=2&limit=2", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Page 3: last 1
        response = client.get(
            "/api/internships?skip=4&limit=2", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_limit_max_200(self, client, auth_headers_admin):
        """Limit cannot exceed 200."""
        response = client.get("/api/internships?limit=500", headers=auth_headers_admin)
        assert response.status_code == 422  # FastAPI validation error

    def test_skip_must_be_non_negative(self, client, auth_headers_admin):
        """Skip must be >= 0."""
        response = client.get("/api/internships?skip=-1", headers=auth_headers_admin)
        assert response.status_code == 422


class TestInternshipSearch:
    """Test GET /internships?search= keyword search."""

    def test_search_by_student_name(
        self, client, auth_headers_admin, db, test_student, test_teacher
    ):
        """Search matches student first or last name."""
        from datetime import date, timedelta
        from app.models import Internship, Company, Proposal

        company = Company(
            name="Test Co", contact_person="J", contact_email="j@test.com"
        )
        db.add(company)
        db.flush()

        intern = Internship(
            student_id=test_student.id,
            teacher_id=test_teacher.id,
            company_id=company.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status="Ingediend",
        )
        db.add(intern)
        db.flush()
        db.add(Proposal(internship_id=intern.id, description="D", status="Ingediend"))
        db.commit()

        # Search by student first name
        response = client.get(
            f"/api/internships?search=Student", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["student"]["first_name"] == "Student"

        # Search by student last name
        response = client.get(
            f"/api/internships?search=User", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_search_by_company_name(self, client, auth_headers_admin, db, test_student):
        """Search matches company name."""
        from datetime import date, timedelta
        from app.models import Internship, Company, Proposal

        company = Company(
            name="Acme Corp", contact_person="J", contact_email="j@test.com"
        )
        db.add(company)
        db.flush()

        intern = Internship(
            student_id=test_student.id,
            company_id=company.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status="Ingediend",
        )
        db.add(intern)
        db.flush()
        db.add(Proposal(internship_id=intern.id, description="D", status="Ingediend"))
        db.commit()

        response = client.get(
            "/api/internships?search=Acme", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["company"]["name"] == "Acme Corp"

    def test_search_no_results(self, client, auth_headers_admin):
        """Search with no matches returns empty list with count 0."""
        response = client.get(
            "/api/internships?search=NONEXISTENT", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data == []
        assert response.headers.get("X-Total-Count") == "0"

    def test_search_case_insensitive(
        self, client, auth_headers_admin, db, test_student
    ):
        """Search is case-insensitive."""
        from datetime import date, timedelta
        from app.models import Internship, Company, Proposal

        company = Company(
            name="BigCorp", contact_person="J", contact_email="j@test.com"
        )
        db.add(company)
        db.flush()

        intern = Internship(
            student_id=test_student.id,
            company_id=company.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status="Ingediend",
        )
        db.add(intern)
        db.flush()
        db.add(Proposal(internship_id=intern.id, description="D", status="Ingediend"))
        db.commit()

        response = client.get(
            "/api/internships?search=bigcorp", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1


class TestInternshipMultiStatus:
    """Test GET /internships?status= with multiple values."""

    def test_single_status(self, client, auth_headers_admin, db, test_student):
        """Single status filter works."""
        from datetime import date, timedelta
        from app.models import Internship, Company, Proposal

        company = Company(name="Co", contact_person="J", contact_email="j@test.com")
        db.add(company)
        db.flush()

        intern = Internship(
            student_id=test_student.id,
            company_id=company.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status="Ingediend",
        )
        db.add(intern)
        db.flush()
        db.add(Proposal(internship_id=intern.id, description="D", status="Ingediend"))
        db.commit()

        response = client.get(
            "/api/internships?status=Ingediend", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_multi_status(self, client, auth_headers_admin, db, test_student):
        """Comma-separated status filter returns multiple statuses."""
        from datetime import date, timedelta
        from app.models import Internship, Company, Proposal

        company1 = Company(name="Co1", contact_person="J", contact_email="j@test.com")
        company2 = Company(name="Co2", contact_person="J", contact_email="j@test.com")
        db.add(company1)
        db.add(company2)
        db.flush()

        intern1 = Internship(
            student_id=test_student.id,
            company_id=company1.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status="Ingediend",
        )
        intern2 = Internship(
            student_id=test_student.id,
            company_id=company2.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status="Goedgekeurd",
        )
        db.add(intern1)
        db.add(intern2)
        db.flush()
        db.add(Proposal(internship_id=intern1.id, description="D", status="Ingediend"))
        db.add(
            Proposal(internship_id=intern2.id, description="D", status="Goedgekeurd")
        )
        db.commit()

        response = client.get(
            "/api/internships?status=Ingediend,Goedgekeurd", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        statuses = {i["status"] for i in data}
        assert statuses == {"Ingediend", "Goedgekeurd"}

    def test_invalid_status(self, client, auth_headers_admin):
        """Invalid status returns 400 with clear error."""
        response = client.get(
            "/api/internships?status=InvalidStatus", headers=auth_headers_admin
        )
        assert response.status_code == 400
        assert "Invalid status" in response.json()["detail"]

    def test_invalid_multi_status(self, client, auth_headers_admin):
        """If any status in comma-list is invalid, return 400."""
        response = client.get(
            "/api/internships?status=Ingediend,Invalid", headers=auth_headers_admin
        )
        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"]


class TestInternshipDateFilter:
    """Test GET /internships?start_date_from=&start_date_to= date range."""

    def test_date_range_filter(self, client, auth_headers_admin, db, test_student):
        """Filter internships by start date range."""
        from datetime import date, timedelta
        from app.models import Internship, Company, Proposal

        company1 = Company(name="Early", contact_person="J", contact_email="j@test.com")
        company2 = Company(name="Late", contact_person="J", contact_email="j@test.com")
        db.add(company1)
        db.add(company2)
        db.flush()

        intern1 = Internship(
            student_id=test_student.id,
            company_id=company1.id,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 6, 1),
            status="Ingediend",
        )
        intern2 = Internship(
            student_id=test_student.id,
            company_id=company2.id,
            start_date=date(2025, 9, 1),
            end_date=date(2026, 1, 1),
            status="Ingediend",
        )
        db.add(intern1)
        db.add(intern2)
        db.flush()
        db.add(Proposal(internship_id=intern1.id, description="D", status="Ingediend"))
        db.add(Proposal(internship_id=intern2.id, description="D", status="Ingediend"))
        db.commit()

        response = client.get(
            "/api/internships?start_date_from=2025-08-01", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["company"]["name"] == "Late"

        response = client.get(
            "/api/internships?start_date_to=2025-06-01", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["company"]["name"] == "Early"

        response = client.get(
            "/api/internships?start_date_from=2025-01-01&start_date_to=2025-12-31",
            headers=auth_headers_admin,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


class TestInternshipSorting:
    """Test GET /internships?sort= ordering."""

    def test_sort_by_created_at_desc(
        self, client, auth_headers_admin, db, test_student
    ):
        """Default sort is created_at descending."""
        from datetime import date, timedelta
        from app.models import Internship, Company, Proposal

        for i in range(3):
            company = Company(
                name=f"Co{i}", contact_person="J", contact_email="j@test.com"
            )
            db.add(company)
            db.flush()
            intern = Internship(
                student_id=test_student.id,
                company_id=company.id,
                start_date=date.today(),
                end_date=date.today() + timedelta(days=30),
                status="Ingediend",
            )
            db.add(intern)
            db.flush()
            db.add(
                Proposal(internship_id=intern.id, description="D", status="Ingediend")
            )
        db.commit()

        response = client.get(
            "/api/internships?sort=-created_at", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        # Should be newest first
        assert len(data) == 3

    def test_sort_by_status(self, client, auth_headers_admin, db, test_student):
        """Sort by status ascending."""
        from datetime import date, timedelta
        from app.models import Internship, Company, Proposal

        company1 = Company(name="A", contact_person="J", contact_email="j@test.com")
        company2 = Company(name="B", contact_person="J", contact_email="j@test.com")
        db.add(company1)
        db.add(company2)
        db.flush()

        intern1 = Internship(
            student_id=test_student.id,
            company_id=company1.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status="Goedgekeurd",
        )
        intern2 = Internship(
            student_id=test_student.id,
            company_id=company2.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status="Ingediend",
        )
        db.add(intern1)
        db.add(intern2)
        db.flush()
        db.add(
            Proposal(internship_id=intern1.id, description="D", status="Goedgekeurd")
        )
        db.add(Proposal(internship_id=intern2.id, description="D", status="Ingediend"))
        db.commit()

        response = client.get(
            "/api/internships?sort=status", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data[0]["status"] == "Goedgekeurd"
        assert data[1]["status"] == "Ingediend"


class TestUserPagination:
    """Test GET /users pagination."""

    def test_users_pagination(
        self, client, auth_headers_admin, test_admin, test_student, test_teacher
    ):
        """Users list supports skip/limit and X-Total-Count."""
        response = client.get("/api/users?skip=0&limit=2", headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert response.headers.get("X-Total-Count") == "3"

    def test_users_search(self, client, auth_headers_admin, test_student):
        """Search users by name or email."""
        response = client.get("/api/users?search=Student", headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["email"] == "student@test.com"

        response = client.get(
            "/api/users?search=student@test", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1


class TestCompetencyPagination:
    """Test GET /competencies pagination."""

    def test_competencies_pagination(
        self, client, auth_headers_admin, sample_competencies
    ):
        """Competencies list supports pagination."""
        response = client.get(
            "/api/competencies?skip=0&limit=2", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert response.headers.get("X-Total-Count") == "4"

    def test_competencies_search(self, client, auth_headers_admin, sample_competencies):
        """Search competencies by name."""
        response = client.get(
            "/api/competencies?search=Technical", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Technical Skills"
