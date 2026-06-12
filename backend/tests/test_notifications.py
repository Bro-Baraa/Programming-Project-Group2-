"""Tests for notification endpoints."""

import pytest
from datetime import datetime, UTC
from app.models import Notification


class TestGetNotifications:
    """Test GET /notifications"""

    @pytest.fixture
    def sample_notifications(self, db, test_student):
        """Create sample notifications for a student."""
        notifications = [
            Notification(
                user_id=test_student.id,
                message="Je stagevoorstel is goedgekeurd.",
                internship_id=1,
                link_view="voorstellen",
                is_read=False,
            ),
            Notification(
                user_id=test_student.id,
                message="Logboek week 1 ingediend.",
                internship_id=1,
                link_view="logboek",
                is_read=True,
            ),
        ]
        for n in notifications:
            db.add(n)
        db.commit()
        return notifications

    def test_get_notifications(
        self, client, auth_headers_student, sample_notifications
    ):
        """User can list their own notifications."""
        response = client.get("/api/notifications", headers=auth_headers_student)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        messages = [n["message"] for n in data]
        assert "Logboek week 1 ingediend." in messages
        assert "Je stagevoorstel is goedgekeurd." in messages
        read_states = [n["is_read"] for n in data]
        assert True in read_states
        assert False in read_states

    def test_get_notifications_empty(self, client, auth_headers_student):
        """Empty list when user has no notifications."""
        response = client.get("/api/notifications", headers=auth_headers_student)
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_notifications_no_auth(self, client):
        """Unauthenticated requests are rejected."""
        response = client.get("/api/notifications")
        assert response.status_code == 401

    def test_get_notifications_only_own(
        self, client, db, auth_headers_student, test_teacher
    ):
        """User only sees their own notifications."""
        # Create notification for teacher
        n = Notification(
            user_id=test_teacher.id,
            message="Docent notificatie",
            is_read=False,
        )
        db.add(n)
        db.commit()

        response = client.get("/api/notifications", headers=auth_headers_student)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestMarkAsRead:
    """Test PATCH /notifications/{id}/read"""

    @pytest.fixture
    def unread_notification(self, db, test_student):
        """Create an unread notification."""
        n = Notification(
            user_id=test_student.id,
            message="Test notificatie",
            is_read=False,
        )
        db.add(n)
        db.commit()
        db.refresh(n)
        return n

    def test_mark_single_read(self, client, auth_headers_student, unread_notification):
        """User can mark their own notification as read."""
        response = client.patch(
            f"/api/notifications/{unread_notification.id}/read",
            headers=auth_headers_student,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_read"] is True

    def test_mark_read_not_found(self, client, auth_headers_student):
        """404 for non-existent notification."""
        response = client.patch(
            "/api/notifications/99999/read", headers=auth_headers_student
        )
        assert response.status_code == 404
        assert "Notificatie niet gevonden" in response.json()["detail"]

    def test_mark_read_other_users_notification(
        self, client, db, auth_headers_student, test_teacher
    ):
        """User cannot mark another user's notification as read."""
        n = Notification(
            user_id=test_teacher.id,
            message="Ander notificatie",
            is_read=False,
        )
        db.add(n)
        db.commit()
        db.refresh(n)

        response = client.patch(
            f"/api/notifications/{n.id}/read", headers=auth_headers_student
        )
        assert response.status_code == 403
        assert "Niet toegestaan" in response.json()["detail"]

    def test_mark_read_no_auth(self, client, unread_notification):
        """Unauthenticated requests are rejected."""
        response = client.patch(f"/api/notifications/{unread_notification.id}/read")
        assert response.status_code == 401


class TestMarkAllAsRead:
    """Test PATCH /notifications/read-all"""

    @pytest.fixture
    def mixed_notifications(self, db, test_student):
        """Create mix of read and unread notifications."""
        notifications = [
            Notification(
                user_id=test_student.id,
                message="Ongelezen 1",
                is_read=False,
            ),
            Notification(
                user_id=test_student.id,
                message="Ongelezen 2",
                is_read=False,
            ),
            Notification(
                user_id=test_student.id,
                message="Gelezen",
                is_read=True,
            ),
        ]
        for n in notifications:
            db.add(n)
        db.commit()
        return notifications

    def test_mark_all_read(self, client, auth_headers_student, mixed_notifications):
        """User can mark all unread notifications as read at once."""
        response = client.patch(
            "/api/notifications/read-all", headers=auth_headers_student
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(n["is_read"] is True for n in data)

    def test_mark_all_read_no_auth(self, client):
        """Unauthenticated requests are rejected."""
        response = client.patch("/api/notifications/read-all")
        assert response.status_code == 401
