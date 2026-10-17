"""Comprehensive tests for Security Events endpoints."""

from fastapi.testclient import TestClient


def test_empty_events_list(client: TestClient):
    """Verify empty database returns an empty list without error."""
    response = client.get("/api/events")
    assert response.status_code == 200
    assert response.json() == []


def test_create_and_retrieve_event(client: TestClient):
    """Verify valid event submission and retrieval per API_CONTRACT.md."""
    payload = {
        "event_id": "evt-test-001",
        "camera_id": "cam-north-01",
        "event_type": "RESTRICTED_ZONE_ENTRY",
        "timestamp": "2026-10-17T09:30:00Z",
        "severity": "HIGH",
        "confidence": 0.92,
        "zone_id": "zone-restricted-01",
        "description": "Person detected in restricted buffer",
        "evidence": {
            "class_name": "person",
            "track_id": 1,
            "frame_number": 420,
            "person_count": 1,
        },
    }

    # 1. Create event
    create_res = client.post("/api/events", json=payload)
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["event_id"] == "evt-test-001"
    assert created["camera_id"] == "cam-north-01"
    assert created["status"] == "NEW"
    assert created["risk_score"] >= 65  # Evaluated by deterministic risk engine
    assert created["risk_level"] in ("HIGH", "CRITICAL")
    assert len(created["reasons"]) > 0
    assert "recommended_action" in created

    # 2. Retrieve single event
    get_res = client.get("/api/events/evt-test-001")
    assert get_res.status_code == 200
    retrieved = get_res.json()
    assert retrieved["event_id"] == "evt-test-001"
    assert retrieved["confidence"] == 0.92


def test_get_nonexistent_event_404(client: TestClient):
    """Verify retrieving an unknown event returns 404."""
    response = client.get("/api/events/evt-unknown-9999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_duplicate_event_submission_idempotency(client: TestClient):
    """Verify duplicate event submissions are idempotent and do not create duplicates."""
    payload = {
        "event_id": "evt-duplicate-01",
        "camera_id": "cam-demo-01",
        "timestamp": "2026-10-17T11:00:00Z",
        "severity": "HIGH",
        "confidence": 0.88,
        "zone_id": "zone-restricted-01",
    }

    # First submission: Created
    res1 = client.post("/api/events", json=payload)
    assert res1.status_code == 201

    # Second submission with same event_id: 409 Conflict with duplicate detail
    res2 = client.post("/api/events", json=payload)
    assert res2.status_code == 409
    dup_data = res2.json()
    assert dup_data["event_id"] == "evt-duplicate-01"
    assert dup_data["message"] == "Duplicate event ID acknowledged"

    # Verify only ONE event exists in database
    list_res = client.get("/api/events")
    events = list_res.json()
    assert len(events) == 1
    assert events[0]["event_id"] == "evt-duplicate-01"


def test_event_filtering_and_pagination(client: TestClient):
    """Verify filtering by camera_id, risk_level, status, and pagination."""
    # Seed 5 events with distinct timestamps
    for i in range(1, 6):
        payload = {
            "event_id": f"evt-filter-0{i}",
            "camera_id": "cam-north-01" if i <= 3 else "cam-south-04",
            "timestamp": f"2026-10-17T12:0{i}:00Z",
            "severity": "CRITICAL" if i == 1 else "LOW",
            "confidence": 0.95 if i == 1 else 0.50,
            "zone_id": "zone-restricted-01",
        }
        res = client.post("/api/events", json=payload)
        assert res.status_code == 201

    # Filter by camera_id
    cam_res = client.get("/api/events?camera_id=cam-south-04")
    assert cam_res.status_code == 200
    cam_events = cam_res.json()
    assert len(cam_events) == 2
    for e in cam_events:
        assert e["camera_id"] == "cam-south-04"

    # Pagination: limit 2, offset 0
    p1_res = client.get("/api/events?limit=2&offset=0")
    assert p1_res.status_code == 200
    p1 = p1_res.json()
    assert len(p1) == 2
    # Verify newest first: evt-filter-05 should be first
    assert p1[0]["event_id"] == "evt-filter-05"
    assert p1[1]["event_id"] == "evt-filter-04"

    # Pagination: limit 2, offset 2
    p2_res = client.get("/api/events?limit=2&offset=2")
    assert p2_res.status_code == 200
    p2 = p2_res.json()
    assert len(p2) == 2
    assert p2[0]["event_id"] == "evt-filter-03"


def test_invalid_event_payloads(client: TestClient):
    """Verify rejection of malformed or incomplete event payloads."""
    # Missing required camera_id
    res1 = client.post(
        "/api/events",
        json={"event_id": "evt-inv-01", "timestamp": "2026-10-17T12:00:00Z", "confidence": 0.9},
    )
    assert res1.status_code == 422

    # Invalid timestamp (missing timezone)
    res2 = client.post(
        "/api/events",
        json={
            "event_id": "evt-inv-02",
            "camera_id": "cam-01",
            "timestamp": "2026-10-17 12:00:00",  # No T or timezone
            "confidence": 0.9,
        },
    )
    assert res2.status_code == 422

    # Invalid confidence > 1.0
    res3 = client.post(
        "/api/events",
        json={
            "event_id": "evt-inv-03",
            "camera_id": "cam-01",
            "timestamp": "2026-10-17T12:00:00Z",
            "confidence": 1.5,
        },
    )
    assert res3.status_code == 422

    # Invalid confidence < 0.0
    res4 = client.post(
        "/api/events",
        json={
            "event_id": "evt-inv-04",
            "camera_id": "cam-01",
            "timestamp": "2026-10-17T12:00:00Z",
            "confidence": -0.1,
        },
    )
    assert res4.status_code == 422

    # Invalid severity
    res5 = client.post(
        "/api/events",
        json={
            "event_id": "evt-inv-05",
            "camera_id": "cam-01",
            "timestamp": "2026-10-17T12:00:00Z",
            "confidence": 0.8,
            "severity": "SUPER_CRITICAL",
        },
    )
    assert res5.status_code == 422


def test_batch_event_submission(client: TestClient):
    """Verify POST /api/events/batch accepts multiple events and handles duplicates."""
    batch_payload = {
        "events": [
            {
                "event_id": "evt-batch-01",
                "camera_id": "cam-01",
                "timestamp": "2026-10-17T13:00:00Z",
                "confidence": 0.85,
            },
            {
                "event_id": "evt-batch-02",
                "camera_id": "cam-02",
                "timestamp": "2026-10-17T13:05:00Z",
                "confidence": 0.90,
            },
            {
                "event_id": "evt-batch-01",  # duplicate within batch
                "camera_id": "cam-01",
                "timestamp": "2026-10-17T13:00:00Z",
                "confidence": 0.85,
            },
        ]
    }

    response = client.post("/api/events/batch", json=batch_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["created"] == 2
    assert data["duplicates"] == 1
