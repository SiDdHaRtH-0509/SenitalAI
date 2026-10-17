"""Tests for Event Review Status Workflow and Transitions."""

from fastapi.testclient import TestClient


def test_status_update_workflow(client: TestClient):
    """Verify standard status transitions (NEW -> ACKNOWLEDGED -> RESOLVED)."""
    # 1. Create initial event in NEW state
    payload = {
        "event_id": "evt-status-01",
        "camera_id": "cam-01",
        "timestamp": "2026-10-17T14:00:00Z",
        "confidence": 0.88,
        "severity": "HIGH",
    }
    create_res = client.post("/api/events", json=payload)
    assert create_res.status_code == 201
    assert create_res.json()["status"] == "NEW"

    # 2. Operator acknowledges incident
    ack_res = client.patch(
        "/api/events/evt-status-01/status",
        json={"status": "ACKNOWLEDGED", "notes": "Patrol Alpha dispatched to investigate."},
    )
    assert ack_res.status_code == 200
    ack_data = ack_res.json()
    assert ack_data["status"] == "ACKNOWLEDGED"
    assert "Patrol Alpha dispatched" in ack_data["operator_notes"]

    # 3. Operator resolves incident
    res_res = client.patch(
        "/api/events/evt-status-01/status",
        json={"status": "RESOLVED", "notes": "Authorized maintenance crew confirmed."},
    )
    assert res_res.status_code == 200
    res_data = res_res.json()
    assert res_data["status"] == "RESOLVED"
    assert "Authorized maintenance crew" in res_data["operator_notes"]


def test_status_aliases_backward_compatibility(client: TestClient):
    """Verify legacy/draft status aliases normalize cleanly to canonical values."""
    payload = {
        "event_id": "evt-status-02",
        "camera_id": "cam-01",
        "timestamp": "2026-10-17T14:10:00Z",
        "confidence": 0.85,
    }
    client.post("/api/events", json=payload)

    # UNREVIEWED -> NEW
    r1 = client.patch("/api/events/evt-status-02/status", json={"status": "UNREVIEWED"})
    assert r1.status_code == 200
    assert r1.json()["status"] == "NEW"

    # INVESTIGATING -> ACKNOWLEDGED
    r2 = client.patch("/api/events/evt-status-02/status", json={"status": "INVESTIGATING"})
    assert r2.status_code == 200
    assert r2.json()["status"] == "ACKNOWLEDGED"

    # FALSE_POSITIVE -> RESOLVED
    r3 = client.patch("/api/events/evt-status-02/status", json={"status": "FALSE_POSITIVE"})
    assert r3.status_code == 200
    assert r3.json()["status"] == "RESOLVED"


def test_invalid_status_rejected(client: TestClient):
    """Verify unsupported status strings are rejected with 422."""
    payload = {
        "event_id": "evt-status-03",
        "camera_id": "cam-01",
        "timestamp": "2026-10-17T14:15:00Z",
        "confidence": 0.85,
    }
    client.post("/api/events", json=payload)

    res = client.patch(
        "/api/events/evt-status-03/status",
        json={"status": "COMPLETELY_INVALID_STATUS"},
    )
    assert res.status_code == 422


def test_update_status_nonexistent_event_404(client: TestClient):
    """Verify attempting to update status on unknown event returns 404."""
    res = client.patch(
        "/api/events/evt-missing-999/status",
        json={"status": "RESOLVED"},
    )
    assert res.status_code == 404
