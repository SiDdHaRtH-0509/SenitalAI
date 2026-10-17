"""Tests for Application Startup and Health Check endpoint."""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Verify application startup and root metadata response."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "SentinelAI Backend API"
    assert data["health"] == "/api/health"
    assert data["documentation"] == "/docs"


def test_health_endpoint(client: TestClient):
    """Verify GET /api/health returns operational status 'ok' per API_CONTRACT.md."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "sentinel-api"
