"""Tests for company endpoints."""

import pytest
from app.models import Company


class TestListCompanies:
    """Test GET /companies"""

    @pytest.fixture
    def sample_companies(self, db):
        """Create sample companies."""
        companies = [
            Company(
                name="Acme Corp",
                address="123 Main St",
                sector="IT",
                contact_person="John",
                contact_email="john@acme.com",
            ),
            Company(
                name="Beta Inc",
                address="456 Oak Ave",
                sector="Finance",
                contact_person="Jane",
                contact_email="jane@beta.com",
            ),
        ]
        for c in companies:
            db.add(c)
        db.commit()
        return companies

    def test_list_companies(self, client, auth_headers_student, sample_companies):
        """Any authenticated user can list companies."""
        response = client.get("/api/companies", headers=auth_headers_student)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Acme Corp"
        assert data[1]["name"] == "Beta Inc"

    def test_list_companies_empty(self, client, auth_headers_student):
        """Empty list when no companies exist."""
        response = client.get("/api/companies", headers=auth_headers_student)
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_list_companies_no_auth(self, client):
        """Unauthenticated requests are rejected."""
        response = client.get("/api/companies")
        assert response.status_code == 401


class TestCreateCompany:
    """Test POST /companies"""

    def test_create_company(self, client, auth_headers_teacher):
        """Staff can create a company."""
        data = {
            "name": "New Corp",
            "address": "789 Elm St",
            "sector": "Healthcare",
            "contact_person": "Bob",
            "contact_email": "bob@newcorp.com",
        }
        response = client.post("/api/companies", json=data, headers=auth_headers_teacher)
        assert response.status_code == 201
        result = response.json()
        assert result["name"] == "New Corp"
        assert result["sector"] == "Healthcare"
        assert result["contact_email"] == "bob@newcorp.com"

    def test_create_company_with_mentor(
        self, client, auth_headers_teacher, test_mentor
    ):
        """Staff can create a company with a mentor."""
        data = {
            "name": "Mentor Corp",
            "contact_person": "Mentor Contact",
            "contact_email": "mentor@corp.com",
            "mentor_id": test_mentor.id,
        }
        response = client.post("/api/companies", json=data, headers=auth_headers_teacher)
        assert response.status_code == 201
        result = response.json()
        assert result["mentor_id"] == test_mentor.id

    def test_create_company_invalid_mentor(self, client, auth_headers_teacher):
        """Invalid mentor_id returns 404."""
        data = {
            "name": "Bad Corp",
            "contact_person": "Bad",
            "contact_email": "bad@corp.com",
            "mentor_id": 99999,
        }
        response = client.post("/api/companies", json=data, headers=auth_headers_teacher)
        assert response.status_code == 404
        assert "Mentor not found" in response.json()["detail"]

    def test_create_company_non_mentor_role(
        self, client, auth_headers_teacher, test_student
    ):
        """Non-mentor user rejected as mentor."""
        data = {
            "name": "Bad Corp",
            "contact_person": "Bad",
            "contact_email": "bad@corp.com",
            "mentor_id": test_student.id,
        }
        response = client.post("/api/companies", json=data, headers=auth_headers_teacher)
        assert response.status_code == 400
        assert "User is not a mentor" in response.json()["detail"]

    def test_student_cannot_create_company(self, client, auth_headers_student):
        """Students cannot create companies."""
        data = {
            "name": "Student Corp",
            "contact_person": "Student",
            "contact_email": "student@corp.com",
        }
        response = client.post(
            "/api/companies", json=data, headers=auth_headers_student
        )
        assert response.status_code == 403

    def test_create_company_no_auth(self, client):
        """Unauthenticated requests are rejected."""
        response = client.post("/api/companies", json={"name": "Test"})
        assert response.status_code == 401


class TestGetCompany:
    """Test GET /companies/{id}"""

    def test_get_company(self, client, auth_headers_student, db):
        """Any authenticated user can get a company."""
        company = Company(
            name="Detail Corp",
            contact_person="Detail",
            contact_email="detail@corp.com",
        )
        db.add(company)
        db.commit()
        db.refresh(company)

        response = client.get(
            f"/api/companies/{company.id}", headers=auth_headers_student
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Detail Corp"

    def test_get_company_not_found(self, client, auth_headers_student):
        """404 for non-existent company."""
        response = client.get("/api/companies/99999", headers=auth_headers_student)
        assert response.status_code == 404
        assert "Company not found" in response.json()["detail"]


class TestUpdateCompany:
    """Test PATCH /companies/{id}"""

    @pytest.fixture
    def existing_company(self, db):
        company = Company(
            name="Old Corp",
            address="Old St",
            sector="Old",
            contact_person="Old",
            contact_email="old@corp.com",
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        return company

    def test_update_company(self, client, auth_headers_teacher, existing_company):
        """Staff can update a company."""
        response = client.patch(
            f"/api/companies/{existing_company.id}",
            json={"name": "Updated Corp", "sector": "New"},
            headers=auth_headers_teacher,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Corp"
        assert data["sector"] == "New"
        assert data["address"] == "Old St"

    def test_update_company_mentor(
        self, client, auth_headers_teacher, existing_company, test_mentor
    ):
        """Staff can assign a mentor to a company."""
        response = client.patch(
            f"/api/companies/{existing_company.id}",
            json={"mentor_id": test_mentor.id},
            headers=auth_headers_teacher,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["mentor_id"] == test_mentor.id

    def test_update_company_invalid_mentor(
        self, client, auth_headers_teacher, existing_company
    ):
        """Invalid mentor_id returns 404."""
        response = client.patch(
            f"/api/companies/{existing_company.id}",
            json={"mentor_id": 99999},
            headers=auth_headers_teacher,
        )
        assert response.status_code == 404
        assert "Mentor not found" in response.json()["detail"]

    def test_update_company_non_mentor(
        self, client, auth_headers_teacher, existing_company, test_student
    ):
        """Non-mentor user rejected as mentor."""
        response = client.patch(
            f"/api/companies/{existing_company.id}",
            json={"mentor_id": test_student.id},
            headers=auth_headers_teacher,
        )
        assert response.status_code == 400
        assert "User is not a mentor" in response.json()["detail"]

    def test_update_company_not_found(self, client, auth_headers_teacher):
        """404 for non-existent company."""
        response = client.patch(
            "/api/companies/99999",
            json={"name": "Test"},
            headers=auth_headers_teacher,
        )
        assert response.status_code == 404

    def test_student_cannot_update_company(
        self, client, auth_headers_student, existing_company
    ):
        """Students cannot update companies."""
        response = client.patch(
            f"/api/companies/{existing_company.id}",
            json={"name": "Hacked"},
            headers=auth_headers_student,
        )
        assert response.status_code == 403


class TestDeleteCompany:
    """Test DELETE /companies/{id}"""

    def test_delete_company(self, client, auth_headers_admin, db):
        """Admin can delete a company without internships."""
        company = Company(
            name="Delete Corp",
            contact_person="Delete",
            contact_email="delete@corp.com",
        )
        db.add(company)
        db.commit()
        db.refresh(company)

        response = client.delete(
            f"/api/companies/{company.id}", headers=auth_headers_admin
        )
        assert response.status_code == 204

    def test_delete_company_with_internships(
        self, client, auth_headers_admin, db, sample_internship
    ):
        """Cannot delete company with associated internships."""
        company = sample_internship.company
        response = client.delete(
            f"/api/companies/{company.id}", headers=auth_headers_admin
        )
        assert response.status_code == 400
        assert "associated internships" in response.json()["detail"]

    def test_delete_company_not_found(self, client, auth_headers_admin):
        """404 for non-existent company."""
        response = client.delete(
            "/api/companies/99999", headers=auth_headers_admin
        )
        assert response.status_code == 404

    def test_teacher_cannot_delete_company(
        self, client, auth_headers_teacher, db
    ):
        """Teachers cannot delete companies (admin only)."""
        company = Company(
            name="Protected Corp",
            contact_person="Protected",
            contact_email="protected@corp.com",
        )
        db.add(company)
        db.commit()
        db.refresh(company)

        response = client.delete(
            f"/api/companies/{company.id}", headers=auth_headers_teacher
        )
        assert response.status_code == 403
