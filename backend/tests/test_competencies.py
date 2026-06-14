"""Tests for competency management."""


class TestCompetencyListing:
    """Test competency listing endpoints."""

    def test_list_competencies_default_active(
        self, client, auth_headers_student, sample_competencies
    ):
        """Test listing active competencies by default."""
        response = client.get("/api/competencies", headers=auth_headers_student)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4  # All sample competencies are active
        assert all(c["active"] for c in data)

    def test_list_all_competencies(
        self, client, auth_headers_student, sample_competencies, db
    ):
        """Test listing all competencies including inactive."""
        from app.models import Competency

        profile_id = sample_competencies[0].profile_id
        # Add inactive competency
        inactive = Competency(
            name="Inactive", weight=10.0, active=False, profile_id=profile_id
        )
        db.add(inactive)
        db.commit()

        response = client.get(
            "/api/competencies?active_only=false", headers=auth_headers_student
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5  # 4 active + 1 inactive


class TestCompetencyCreation:
    """Test competency creation (admin only)."""

    def test_admin_create_competency(
        self, client, auth_headers_admin, sample_competencies
    ):
        """Test admin can create competency."""
        profile_id = sample_competencies[0].profile_id
        competency_data = {
            "name": "Leadership",
            "weight": 20.0,
            "profile_id": profile_id,
        }
        response = client.post(
            "/api/competencies", json=competency_data, headers=auth_headers_admin
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Leadership"
        assert data["weight"] == 20.0
        assert data["active"] is True

    def test_student_cannot_create_competency(self, client, auth_headers_student):
        """Test students cannot create competencies."""
        competency_data = {"name": "Hacking", "weight": 50.0}
        response = client.post(
            "/api/competencies", json=competency_data, headers=auth_headers_student
        )
        assert response.status_code == 403

    def test_teacher_cannot_create_competency(self, client, auth_headers_teacher):
        """Test teachers cannot create competencies."""
        competency_data = {"name": "Teaching", "weight": 30.0}
        response = client.post(
            "/api/competencies", json=competency_data, headers=auth_headers_teacher
        )
        assert response.status_code == 403

    def test_duplicate_name_rejected(
        self, client, auth_headers_admin, sample_competencies
    ):
        """Test cannot create competency with duplicate name."""
        profile_id = sample_competencies[0].profile_id
        competency_data = {
            "name": "Technical Skills",  # Already exists
            "weight": 10.0,
            "profile_id": profile_id,
        }
        response = client.post(
            "/api/competencies", json=competency_data, headers=auth_headers_admin
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_repeated_create_request_does_not_duplicate(
        self, client, auth_headers_admin, sample_competencies, db
    ):
        """Repeated submits should leave only one competency per profile/name."""
        from app.models import Competency

        profile_id = sample_competencies[0].profile_id
        competency_data = {
            "name": "  Planning  ",
            "weight": 10.0,
            "profile_id": profile_id,
        }

        first = client.post(
            "/api/competencies", json=competency_data, headers=auth_headers_admin
        )
        second = client.post(
            "/api/competencies", json=competency_data, headers=auth_headers_admin
        )

        assert first.status_code == 201
        assert first.json()["name"] == "Planning"
        assert second.status_code == 400
        assert (
            db.query(Competency)
            .filter(Competency.profile_id == profile_id, Competency.name == "Planning")
            .count()
            == 1
        )


class TestCompetencyUpdate:
    """Test competency updates (admin only)."""

    def test_admin_update_competency(
        self, client, auth_headers_admin, sample_competencies
    ):
        """Test admin can update competency."""
        competency_id = sample_competencies[0].id

        update_data = {"name": "Updated Name", "weight": 30.0, "active": True}
        response = client.patch(
            f"/api/competencies/{competency_id}",
            json=update_data,
            headers=auth_headers_admin,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["weight"] == 30.0

    def test_partial_update(self, client, auth_headers_admin, sample_competencies):
        """Test partial update (only weight)."""
        competency_id = sample_competencies[0].id
        original_name = sample_competencies[0].name

        update_data = {"weight": 35.0}
        response = client.patch(
            f"/api/competencies/{competency_id}",
            json=update_data,
            headers=auth_headers_admin,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == original_name  # Unchanged
        assert data["weight"] == 35.0

    def test_non_admin_cannot_update(
        self, client, auth_headers_teacher, sample_competencies
    ):
        """Test non-admin cannot update competencies."""
        competency_id = sample_competencies[0].id

        update_data = {"weight": 99.0}
        response = client.patch(
            f"/api/competencies/{competency_id}",
            json=update_data,
            headers=auth_headers_teacher,
        )
        assert response.status_code == 403

    def test_update_nonexistent_competency(self, client, auth_headers_admin):
        """Test 404 on updating non-existent competency."""
        update_data = {"weight": 50.0}
        response = client.patch(
            "/api/competencies/99999", json=update_data, headers=auth_headers_admin
        )
        assert response.status_code == 404


class TestCompetencyDeletion:
    """Test competency deletion (soft delete - admin only)."""

    def test_admin_delete_competency(
        self, client, auth_headers_admin, sample_competencies
    ):
        """Test admin can soft-delete (deactivate) competency."""
        competency_id = sample_competencies[0].id

        # The endpoint returns 204 No Content on successful deletion
        response = client.delete(
            f"/api/competencies/{competency_id}", headers=auth_headers_admin
        )
        assert response.status_code == 204

        # Verify it's actually deleted (hard delete when not in use)
        response = client.get(
            f"/api/competencies/{competency_id}", headers=auth_headers_admin
        )
        assert response.status_code == 404

    def test_non_admin_cannot_delete(
        self, client, auth_headers_student, sample_competencies
    ):
        """Test non-admin cannot delete competencies."""
        competency_id = sample_competencies[0].id

        response = client.delete(
            f"/api/competencies/{competency_id}", headers=auth_headers_student
        )
        assert response.status_code == 403


class TestWeightValidation:
    """Test competency weight validation."""

    def test_valid_weights_sum_100(
        self, client, auth_headers_admin, sample_competencies
    ):
        """Test weight check endpoint with valid weights."""
        response = client.get(
            "/api/competencies/check-weights", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_weight"] == 100.0
        assert data["valid"] is True
        assert data["competency_count"] == 4

    def test_invalid_weights_sum(
        self, client, auth_headers_admin, sample_competencies, db
    ):
        """Test weight check with invalid sum."""
        from app.models import Competency

        # Get the profile_id from existing competencies
        profile_id = sample_competencies[0].profile_id

        # Add another competency making total > 100
        extra = Competency(
            name="Extra", weight=10.0, active=True, profile_id=profile_id
        )
        db.add(extra)
        db.commit()

        response = client.get(
            "/api/competencies/check-weights", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_weight"] == 110.0
        assert data["valid"] is False
        assert data["competency_count"] == 5

    def test_weight_check_student_access(
        self, client, auth_headers_student, sample_competencies
    ):
        """Test students can access weight check."""
        response = client.get(
            "/api/competencies/check-weights", headers=auth_headers_student
        )
        assert response.status_code == 200
        assert response.json()["valid"] is True


class TestCompetencyEdgeCases:
    """Test edge cases and error handling."""

    def test_create_competency_negative_weight_rejected(
        self, client, auth_headers_admin, sample_competencies
    ):
        """Test creating competency with negative weight is rejected."""
        profile_id = sample_competencies[0].profile_id
        competency_data = {
            "name": "Negative",
            "weight": -10.0,
            "profile_id": profile_id,
        }
        response = client.post(
            "/api/competencies", json=competency_data, headers=auth_headers_admin
        )
        assert response.status_code == 422  # Validation error for negative weight

    def test_create_competency_zero_weight_rejected(
        self, client, auth_headers_admin, sample_competencies
    ):
        """Test creating competency with zero weight is rejected."""
        profile_id = sample_competencies[0].profile_id
        competency_data = {
            "name": "Zero Weight",
            "weight": 0.0,
            "profile_id": profile_id,
        }
        response = client.post(
            "/api/competencies", json=competency_data, headers=auth_headers_admin
        )
        assert response.status_code == 422  # Validation error for zero weight
