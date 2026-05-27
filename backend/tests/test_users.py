"""Tests for user listing and lookup endpoints."""

import pytest


class TestListUsers:
    """Test GET /users endpoint."""

    def test_list_users_unauthorized(self, client):
        """Must be authenticated to list users."""
        response = client.get("/users")
        assert response.status_code == 401

    def test_list_all_users(self, client, auth_headers_student, test_student, test_teacher, test_mentor):
        """Authenticated user can list all active users."""
        response = client.get("/users", headers=auth_headers_student)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        emails = {u["email"] for u in data}
        assert "student@test.com" in emails
        assert "teacher@test.com" in emails
        assert "mentor@test.com" in emails

    def test_list_users_filter_by_role(self, client, auth_headers_student, test_student, test_teacher, test_mentor):
        """Filter users by role."""
        response = client.get("/users?role=teacher", headers=auth_headers_student)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["email"] == "teacher@test.com"
        assert data[0]["role"] == "teacher"

    def test_list_users_filter_by_role_mentor(self, client, auth_headers_student, test_mentor):
        """Filter users by mentor role."""
        response = client.get("/users?role=mentor", headers=auth_headers_student)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["email"] == "mentor@test.com"

    def test_list_users_invalid_role(self, client, auth_headers_student):
        """Invalid role returns 400."""
        response = client.get("/users?role=superhero", headers=auth_headers_student)
        assert response.status_code == 400
        assert "Invalid role" in response.json()["detail"]

    def test_list_users_includes_all_roles(self, client, auth_headers_admin, test_admin, test_student, test_teacher, test_committee, test_mentor):
        """Admin can see all user roles."""
        response = client.get("/users", headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        roles = {u["role"] for u in data}
        assert roles == {"admin", "student", "teacher", "committee", "mentor"}

    def test_list_users_sorted_by_name(self, client, auth_headers_student, test_student, test_teacher, test_mentor):
        """Users are sorted by last_name, first_name."""
        response = client.get("/users", headers=auth_headers_student)
        assert response.status_code == 200
        data = response.json()
        # All have last_name "User", so sorted by first_name
        first_names = [u["first_name"] for u in data]
        assert first_names == sorted(first_names)

    def test_list_users_response_does_not_include_password(self, client, auth_headers_student):
        """Password hash must never be exposed."""
        response = client.get("/users", headers=auth_headers_student)
        assert response.status_code == 200
        for user in response.json():
            assert "password_hash" not in user
            assert "password" not in user


class TestGetUser:
    """Test GET /users/{id} endpoint."""

    def test_get_user_by_id(self, client, auth_headers_student, test_teacher):
        """Get a specific user by ID."""
        response = client.get(f"/users/{test_teacher.id}", headers=auth_headers_student)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_teacher.id
        assert data["email"] == "teacher@test.com"
        assert data["first_name"] == "Teacher"
        assert data["last_name"] == "User"
        assert data["role"] == "teacher"

    def test_get_user_not_found(self, client, auth_headers_student):
        """Non-existent user returns 404."""
        response = client.get("/users/99999", headers=auth_headers_student)
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    def test_get_user_unauthorized(self, client, test_student):
        """Must be authenticated."""
        response = client.get(f"/users/{test_student.id}")
        assert response.status_code == 401

    def test_get_user_no_password_exposure(self, client, auth_headers_student, test_teacher):
        """Password hash must never be exposed."""
        response = client.get(f"/users/{test_teacher.id}", headers=auth_headers_student)
        assert response.status_code == 200
        data = response.json()
        assert "password_hash" not in data
        assert "password" not in data