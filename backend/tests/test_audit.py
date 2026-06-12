"""Tests for audit log endpoints."""

import pytest
from datetime import datetime, UTC
from app.models import AuditLog


class TestListAuditLogs:
    """Test GET /audit"""

    @pytest.fixture
    def sample_logs(self, db, test_admin, test_student):
        """Create sample audit logs."""
        logs = [
            AuditLog(
                user_id=test_admin.id,
                user_email="admin@test.com",
                user_role="admin",
                action="user.delete",
                entity_type="user",
                entity_id=2,
                detail="Deleted a user",
            ),
            AuditLog(
                user_id=test_student.id,
                user_email="student@test.com",
                user_role="student",
                action="internship.create",
                entity_type="internship",
                entity_id=1,
                detail="Stage ingediend",
            ),
            AuditLog(
                user_id=test_admin.id,
                user_email="admin@test.com",
                user_role="admin",
                action="proposal.review",
                entity_type="proposal",
                entity_id=1,
                detail="Voorstel goedgekeurd",
            ),
        ]
        for log in logs:
            db.add(log)
        db.commit()
        return logs

    def test_list_audit_logs(self, client, auth_headers_admin, sample_logs):
        """Admin can list all audit logs."""
        response = client.get("/api/audit", headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.json()
        # 3 sample logs + 1 login audit log from fixture login
        assert len(data) == 4
        assert "X-Total-Count" in response.headers
        assert response.headers["X-Total-Count"] == "4"

    def test_filter_by_action(self, client, auth_headers_admin, sample_logs):
        """Filter audit logs by action."""
        response = client.get(
            "/api/audit?action=user.delete", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["action"] == "user.delete"

    def test_filter_by_user_email(self, client, auth_headers_admin, sample_logs):
        """Filter audit logs by user email."""
        response = client.get(
            "/api/audit?user_email=student@test.com", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_email"] == "student@test.com"

    def test_filter_by_entity_type(self, client, auth_headers_admin, sample_logs):
        """Filter audit logs by entity type."""
        response = client.get(
            "/api/audit?entity_type=internship", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["entity_type"] == "internship"

    def test_filter_partial_match(self, client, auth_headers_admin, sample_logs):
        """Action filter supports partial match (ilike)."""
        response = client.get(
            "/api/audit?action=proposal", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "proposal" in data[0]["action"]

    def test_pagination(self, client, auth_headers_admin, sample_logs):
        """Pagination works via skip and limit."""
        response = client.get(
            "/api/audit?skip=1&limit=1", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert response.headers["X-Total-Count"] == "4"

    def test_teacher_cannot_list_audit(self, client, auth_headers_teacher):
        """Teachers cannot list audit logs (admin only)."""
        response = client.get("/api/audit", headers=auth_headers_teacher)
        assert response.status_code == 403

    def test_student_cannot_list_audit(self, client, auth_headers_student):
        """Students cannot list audit logs (admin only)."""
        response = client.get("/api/audit", headers=auth_headers_student)
        assert response.status_code == 403

    def test_list_audit_no_auth(self, client):
        """Unauthenticated requests are rejected."""
        response = client.get("/api/audit")
        assert response.status_code == 401
