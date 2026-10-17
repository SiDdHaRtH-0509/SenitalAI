"""Tests for GET /api/stats endpoint."""

from fastapi.testclient import TestClient


def test_stats_empty_database(client: TestClient):
    """Verify statistics when no events exist in the database."""
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_events"] == 0
    assert "by_risk_level" in data
    assert data["by_risk_level"]["CRITICAL"] == 0
    assert data["by_risk_level"]["HIGH"] == 0
    assert data["by_risk_level"]["MEDIUM"] == 0
    assert data["by_risk_level"]["LOW"] == 0


def test_stats_derived_from_persisted_events(client: TestClient):
    """Verify statistics dynamically calculate counts directly from stored records."""
    # Insert events across different risk levels
    events = [
        {
            "event_id": "evt-stat-01",
            "camera_id": "cam-north-01",
            "timestamp": "2026-10-17T10:00:00Z",
            "severity": "CRITICAL",
            "confidence": 0.95,
            "zone_id": "zone-restricted-01",
        },
        {
            "event_id": "evt-stat-02",
            "camera_id": "cam-north-01",
            "timestamp": "2026-10-17T10:05:00Z",
            "severity": "HIGH",
            "confidence": 0.90,
            "zone_id": "zone-restricted-01",
        },
        {
            "event_id": "evt-stat-03",
            "camera_id": "cam-east-02",
            "timestamp": "2026-10-17T10:10:00Z",
            "severity": "LOW",
            "confidence": 0.50,
            "zone_id": None,
        },
    ]

    for evt in events:
        res = client.post("/api/events", json=evt)
        assert res.status_code == 201

    stats_res = client.get("/api/stats")
    assert stats_res.status_code == 200
    data = stats_res.json()
    assert data["total_events"] == 3
    assert data["by_risk_level"]["CRITICAL"] >= 1
    assert data["by_risk_level"]["LOW"] >= 1
