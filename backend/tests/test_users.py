"""Tests for user listing and lookup endpoints."""

import pytest


class TestCreateUser:
    """Test POST /users endpoint."""

    def test_admin_can_create_user(self, client, auth_headers_admin):
        """US-27: Admin kan een nieuwe gebruiker aanmaken."""
        new_user = {
            "email": "newuser@test.com",
            "first_name": "Nieuwe",
            "last_name": "Gebruiker",
            "role": "student",
            "password": "securepass123",
        }
        response = client.post("/api/users", json=new_user, headers=auth_headers_admin)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["first_name"] == "Nieuwe"
        assert data["last_name"] == "Gebruiker"
        assert data["role"] == "student"
        assert data["is_active"] is True
        assert "password" not in data
        assert "password_hash" not in data

    def test_non_admin_cannot_create_user(self, client, auth_headers_student):
        """US-27: Niet-admin mag geen gebruiker aanmaken."""
        new_user = {
            "email": "hacker@test.com",
            "first_name": "Hacker",
            "last_name": "User",
            "role": "admin",
            "password": "hackpass123",
        }
        response = client.post(
            "/api/users", json=new_user, headers=auth_headers_student
        )
        assert response.status_code == 403

    def test_cannot_create_user_with_existing_email(
        self, client, auth_headers_admin, test_student
    ):
        """US-27: Geen dubbele email toegestaan."""
        new_user = {
            "email": test_student.email,
            "first_name": "Duplicate",
            "last_name": "User",
            "role": "student",
            "password": "password123",
        }
        response = client.post("/api/users", json=new_user, headers=auth_headers_admin)
        assert response.status_code == 400
        assert (
            "already exists" in response.json()["detail"].lower()
            or "email" in response.json()["detail"].lower()
        )

    def test_unauthorized_cannot_create_user(self, client):
        """US-27: Zonder token mag je geen gebruiker aanmaken."""
        new_user = {
            "email": "anon@test.com",
            "first_name": "Anon",
            "last_name": "User",
            "role": "student",
            "password": "password123",
        }
        response = client.post("/api/users", json=new_user)
        assert response.status_code == 401


class TestUpdateUser:
    """Test PATCH /users/{id} endpoint."""

    def test_admin_can_update_user(self, client, auth_headers_admin, test_student):
        """US-27: Admin kan een gebruiker wijzigen."""
        update_data = {
            "first_name": "Gewijzigd",
            "last_name": "Student",
            "role": "teacher",
        }
        response = client.patch(
            f"/api/users/{test_student.id}",
            json=update_data,
            headers=auth_headers_admin,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Gewijzigd"
        assert data["last_name"] == "Student"
        assert data["role"] == "teacher"

    def test_non_admin_cannot_update_user(
        self, client, auth_headers_student, test_teacher
    ):
        """US-27: Niet-admin mag geen gebruiker wijzigen."""
        update_data = {"first_name": "Hacked"}
        response = client.patch(
            f"/api/users/{test_teacher.id}",
            json=update_data,
            headers=auth_headers_student,
        )
        assert response.status_code == 403

    def test_update_nonexistent_user(self, client, auth_headers_admin):
        """US-27: Wijzigen van niet-bestaande gebruiker geeft 404."""
        update_data = {"first_name": "Ghost"}
        response = client.patch(
            "/api/users/99999", json=update_data, headers=auth_headers_admin
        )
        assert response.status_code == 404


class TestDeleteUser:
    """Test DELETE /users/{id} endpoint."""

    def test_admin_can_delete_user(self, client, auth_headers_admin, db):
        """US-27: Admin kan een gebruiker verwijderen."""
        from app.models import User
        from app.auth import get_password_hash

        user = User(
            email="todelete@test.com",
            password_hash=get_password_hash("delete123"),
            first_name="Delete",
            last_name="Me",
            role="student",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        response = client.delete(f"/api/users/{user.id}", headers=auth_headers_admin)
        assert response.status_code == 204

        # Verify user is gone
        get_response = client.get(f"/api/users/{user.id}", headers=auth_headers_admin)
        assert get_response.status_code == 404

    def test_non_admin_cannot_delete_user(
        self, client, auth_headers_student, test_teacher
    ):
        """US-27: Niet-admin mag geen gebruiker verwijderen."""
        response = client.delete(
            f"/api/users/{test_teacher.id}", headers=auth_headers_student
        )
        assert response.status_code == 403

    def test_delete_nonexistent_user(self, client, auth_headers_admin):
        """US-27: Verwijderen van niet-bestaande gebruiker geeft 404."""
        response = client.delete("/api/users/99999", headers=auth_headers_admin)
        assert response.status_code == 404


class TestListUsers:
    """Test GET /users endpoint."""

    def test_list_users_unauthorized(self, client):
        """Must be authenticated to list users."""
        response = client.get("/api/users")
        assert response.status_code == 401

    def test_list_all_users(
        self, client, auth_headers_student, test_student, test_teacher, test_mentor
    ):
        """Authenticated user can list all active users."""
        response = client.get("/api/users", headers=auth_headers_student)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        emails = {u["email"] for u in data}
        assert "student@test.com" in emails
        assert "teacher@test.com" in emails
        assert "mentor@test.com" in emails

    def test_list_users_filter_by_role(
        self, client, auth_headers_student, test_student, test_teacher, test_mentor
    ):
        """Filter users by role."""
        response = client.get("/api/users?role=teacher", headers=auth_headers_student)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["email"] == "teacher@test.com"
        assert data[0]["role"] == "teacher"

    def test_list_users_filter_by_role_mentor(
        self, client, auth_headers_student, test_mentor
    ):
        """Filter users by mentor role."""
        response = client.get("/api/users?role=mentor", headers=auth_headers_student)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["email"] == "mentor@test.com"

    def test_list_users_invalid_role(self, client, auth_headers_student):
        """Invalid role returns 400."""
        response = client.get("/api/users?role=superhero", headers=auth_headers_student)
        assert response.status_code == 400
        assert "Invalid role" in response.json()["detail"]

    def test_list_users_includes_all_roles(
        self,
        client,
        auth_headers_admin,
        test_admin,
        test_student,
        test_teacher,
        test_committee,
        test_mentor,
    ):
        """Admin can see all user roles."""
        response = client.get("/api/users", headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        roles = {u["role"] for u in data}
        assert roles == {"admin", "student", "teacher", "committee", "mentor"}

    def test_list_users_sorted_by_name(
        self, client, auth_headers_student, test_student, test_teacher, test_mentor
    ):
        """Users are sorted by last_name, first_name."""
        response = client.get("/api/users", headers=auth_headers_student)
        assert response.status_code == 200
        data = response.json()
        # All have last_name "User", so sorted by first_name
        first_names = [u["first_name"] for u in data]
        assert first_names == sorted(first_names)

    def test_list_users_response_does_not_include_password(
        self, client, auth_headers_student
    ):
        """Password hash must never be exposed."""
        response = client.get("/api/users", headers=auth_headers_student)
        assert response.status_code == 200
        for user in response.json():
            assert "password_hash" not in user
            assert "password" not in user


class TestGetUser:
    """Test GET /users/{id} endpoint."""

    def test_get_user_by_id(self, client, auth_headers_student, test_teacher):
        """Get a specific user by ID."""
        response = client.get(
            f"/api/users/{test_teacher.id}", headers=auth_headers_student
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_teacher.id
        assert data["email"] == "teacher@test.com"
        assert data["first_name"] == "Teacher"
        assert data["last_name"] == "User"
        assert data["role"] == "teacher"

    def test_get_user_not_found(self, client, auth_headers_student):
        """Non-existent user returns 404."""
        response = client.get("/api/users/99999", headers=auth_headers_student)
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    def test_get_user_unauthorized(self, client, test_student):
        """Must be authenticated."""
        response = client.get(f"/api/users/{test_student.id}")
        assert response.status_code == 401

    def test_get_user_no_password_exposure(
        self, client, auth_headers_student, test_teacher
    ):
        """Password hash must never be exposed."""
        response = client.get(
            f"/api/users/{test_teacher.id}", headers=auth_headers_student
        )
        assert response.status_code == 200
        data = response.json()
        assert "password_hash" not in data
        assert "password" not in data
