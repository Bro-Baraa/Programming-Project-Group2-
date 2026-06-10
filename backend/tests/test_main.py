"""Tests for main API endpoints."""


class TestRootEndpoints:
    """Test root and health endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint serves frontend (static files) or health."""
        # Root serves static frontend files; just check it returns 200
        response = client.get("/")
        assert response.status_code == 200

    def test_health_check(self, client):
        """Test health check endpoint at /api/health."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_openapi_docs_disabled(self, client):
        """OpenAPI docs are disabled in production."""
        response = client.get("/docs")
        assert response.status_code == 404

    def test_openapi_json_disabled(self, client):
        """OpenAPI JSON schema is disabled in production."""
        response = client.get("/openapi.json")
        assert response.status_code == 404


class TestCORSMiddleware:
    """Test CORS configuration."""

    def test_cors_headers_present(self, client):
        """Test CORS headers are present on API responses."""
        response = client.get(
            "/api/health", headers={"Origin": "http://localhost:8080"}
        )
        assert response.status_code == 200
        # FastAPI CORS middleware adds these headers
        assert "access-control-allow-origin" in response.headers
        # In test env FRONTEND_ORIGINS is unset, so CORS defaults to '*' (allow any origin)
        assert response.headers["access-control-allow-origin"] == "*"

    def test_cors_preflight(self, client):
        """Test CORS preflight request."""
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:8080",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization",
            },
        )
        # Preflight should succeed
        assert response.status_code == 200


class Test404Handling:
    """Test 404 error handling."""

    def test_nonexistent_endpoint(self, client):
        """Test 404 on non-existent endpoint."""
        response = client.get("/nonexistent/endpoint")
        assert response.status_code == 404

    def test_nonexistent_resource(self, client, auth_headers_admin):
        """Test 404 on non-existent resource."""
        response = client.get("/api/internships/99999", headers=auth_headers_admin)
        assert response.status_code == 404
        assert "Internship not found" in response.json()["detail"]
