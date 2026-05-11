import pytest


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_login_success(self, client, test_admin):
        """Test successful login."""
        response = client.post(
            "/auth/login",
            data={"username": "admin@test.com", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "admin@test.com"
        assert data["user"]["role"] == "admin"

    def test_login_invalid_password(self, client, test_admin):
        """Test login with wrong password."""
        response = client.post(
            "/auth/login",
            data={"username": "admin@test.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_invalid_email(self, client):
        """Test login with non-existent email."""
        response = client.post(
            "/auth/login",
            data={"username": "nonexistent@test.com", "password": "password123"}
        )
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_get_me_success(self, client, auth_headers_admin, test_admin):
        """Test getting current user info."""
        response = client.get("/auth/me", headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@test.com"
        assert data["role"] == "admin"
        assert data["first_name"] == "Admin"
        assert data["last_name"] == "User"

    def test_get_me_no_token(self, client):
        """Test getting current user without token."""
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self, client):
        """Test getting current user with invalid token."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


class TestUserRegistration:
    """Test user registration (admin only)."""

    def test_register_user_as_admin(self, client, auth_headers_admin):
        """Test admin can register new user."""
        user_data = {
            "email": "newuser@test.com",
            "password": "newpass123",
            "first_name": "New",
            "last_name": "User",
            "role": "student"
        }
        response = client.post(
            "/auth/register",
            json=user_data,
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["role"] == "student"
        assert data["first_name"] == "New"

    def test_register_user_as_student_fails(self, client, auth_headers_student):
        """Test non-admin cannot register users."""
        user_data = {
            "email": "newuser@test.com",
            "password": "newpass123",
            "first_name": "New",
            "last_name": "User",
            "role": "student"
        }
        response = client.post(
            "/auth/register",
            json=user_data,
            headers=auth_headers_student
        )
        assert response.status_code == 403
        assert "Only admins can register new users" in response.json()["detail"]

    def test_register_duplicate_email(self, client, auth_headers_admin, test_student):
        """Test cannot register with existing email."""
        user_data = {
            "email": "student@test.com",  # Already exists
            "password": "newpass123",
            "first_name": "New",
            "last_name": "User",
            "role": "student"
        }
        response = client.post(
            "/auth/register",
            json=user_data,
            headers=auth_headers_admin
        )
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_register_missing_fields(self, client, auth_headers_admin):
        """Test registration with missing required fields."""
        user_data = {
            "email": "new@test.com",
            "password": "pass123"
            # Missing first_name, last_name, role
        }
        response = client.post(
            "/auth/register",
            json=user_data,
            headers=auth_headers_admin
        )
        assert response.status_code == 422  # Validation error


class TestRoleBasedAccess:
    """Test role-based access control."""

    def test_student_cannot_access_teacher_endpoint(self, client, auth_headers_student):
        """Test students cannot access teacher-only endpoints."""
        # Try to create an evaluation (teacher only)
        response = client.post(
            "/internships/1/evaluations",
            json={"type": "final"},
            headers=auth_headers_student
        )
        assert response.status_code == 403

    def test_teacher_can_access_teacher_endpoint(self, client, auth_headers_teacher):
        """Test teachers can access teacher endpoints (but need internship)."""
        # The endpoint should return 404 (no internship) not 403 (forbidden)
        response = client.post(
            "/internships/999/evaluations",
            json={"type": "final"},
            headers=auth_headers_teacher
        )
        assert response.status_code == 404  # Internship not found, not forbidden