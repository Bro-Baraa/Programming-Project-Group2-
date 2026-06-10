"""Test for CSV export endpoint (US-28)."""

import pytest


class TestCsvExport:
    """Test GET /internships/reports/export/csv"""

    def test_csv_export_requires_auth(self, client):
        response = client.get("/api/internships/reports/export/csv")
        assert response.status_code == 401

    def test_csv_export_requires_staff(self, client, auth_headers_student):
        response = client.get(
            "/api/internships/reports/export/csv",
            headers=auth_headers_student,
        )
        assert response.status_code == 403

    def test_csv_export_admin_success(self, client, auth_headers_admin):
        response = client.get(
            "/api/internships/reports/export/csv",
            headers=auth_headers_admin,
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "attachment" in response.headers["content-disposition"]
        assert "stage_export_" in response.headers["content-disposition"]
        content = response.content.decode("utf-8-sig")
        assert "Student" in content
        assert "Email" in content
        assert "Bedrijf" in content

    def test_csv_export_committee_success(self, client, auth_headers_committee):
        response = client.get(
            "/api/internships/reports/export/csv",
            headers=auth_headers_committee,
        )
        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        lines = content.strip().split("\n")
        assert len(lines) >= 1  # at least header
        assert "Student" in lines[0]
