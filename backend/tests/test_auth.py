import pytest


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_login_success(self, client, test_admin):
        response = client.post(
            "/api/auth/login",
            data={"username": "admin@test.com", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "admin@test.com"
        assert data["user"]["role"] == "admin"

    def test_login_invalid_password(self, client, test_admin):
        response = client.post(
            "/api/auth/login",
            data={"username": "admin@test.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_invalid_email(self, client):
        response = client.post(
            "/api/auth/login",
            data={"username": "nonexistent@test.com", "password": "password123"}
        )
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_get_me_success(self, client, auth_headers_admin, test_admin):
        response = client.get("/api/auth/me", headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@test.com"
        assert data["role"] == "admin"
        assert data["first_name"] == "Admin"
        assert data["last_name"] == "User"

    def test_get_me_no_token(self, client):
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self, client):
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


class TestUserRegistration:
    """Test user registration (admin only)."""

    def test_register_user_as_admin(self, client, auth_headers_admin):
        user_data = {
            "email": "newuser@test.com",
            "password": "newpass123",
            "first_name": "New",
            "last_name": "User",
            "role": "student"
        }
        response = client.post(
            "/api/auth/register",
            json=user_data,
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["role"] == "student"
        assert data["first_name"] == "New"

    def test_register_user_as_student_fails(self, client, auth_headers_student):
        user_data = {
            "email": "newuser@test.com",
            "password": "newpass123",
            "first_name": "New",
            "last_name": "User",
            "role": "student"
        }
        response = client.post(
            "/api/auth/register",
            json=user_data,
            headers=auth_headers_student
        )
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

    def test_register_duplicate_email(self, client, auth_headers_admin, test_student):
        user_data = {
            "email": "student@test.com",  # Already exists
            "password": "newpass123",
            "first_name": "New",
            "last_name": "User",
            "role": "student"
        }
        response = client.post(
            "/api/auth/register",
            json=user_data,
            headers=auth_headers_admin
        )
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_register_missing_fields(self, client, auth_headers_admin):
        user_data = {
            "email": "new@test.com",
            "password": "pass123"
            # Missing first_name, last_name, role
        }
        response = client.post(
            "/api/auth/register",
            json=user_data,
            headers=auth_headers_admin
        )
        assert response.status_code == 422  # Validation error


class TestRoleBasedAccess:
    """Test role-based access control."""

    def test_student_cannot_access_teacher_endpoint(self, client, auth_headers_student, sample_internship):
        # Try to create a final evaluation as student (should be forbidden)
        response = client.post(
            f"/api/internships/{sample_internship.id}/evaluations",
            json={"eval_type": "final"},
            headers=auth_headers_student
        )
        assert response.status_code == 403

    def test_teacher_can_access_teacher_endpoint(self, client, auth_headers_teacher):
        # The endpoint validates input before checking internship
        response = client.post(
            "/api/internships/999/evaluations",
            json={"eval_type": "final"},
            headers=auth_headers_teacher
        )
        # Should get 404 for non-existent internship (after passing auth and validation)
        assert response.status_code in [404, 422]  # Depends on validation order