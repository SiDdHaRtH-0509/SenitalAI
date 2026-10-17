"""Tests for Camera Registry and Restricted Zones endpoints."""

from fastapi.testclient import TestClient


def test_cameras_lifecycle(client: TestClient):
    """Verify camera registration and inventory retrieval."""
    cam_payload = {
        "camera_id": "cam-test-01",
        "name": "Tower Alpha Overview",
        "location": "North Observation Post",
        "status": "ONLINE",
        "resolution": "1920x1080",
        "fps": 20.0,
        "zone_id": "zone-test-01",
        "stream_uri": "rtsp://camera-01.local:554/live",
    }

    # Register camera
    create_res = client.post("/api/cameras", json=cam_payload)
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["camera_id"] == "cam-test-01"
    assert created["name"] == "Tower Alpha Overview"

    # List cameras
    list_res = client.get("/api/cameras")
    assert list_res.status_code == 200
    cams = list_res.json()
    assert any(c["camera_id"] == "cam-test-01" for c in cams)


def test_zones_lifecycle(client: TestClient):
    """Verify restricted zone registration and boundary retrieval."""
    zone_payload = {
        "zone_id": "zone-test-01",
        "name": "North Fence Perimeter Buffer",
        "camera_id": "cam-test-01",
        "status": "ACTIVE",
        "vertices": [
            [0.2, 0.4],
            [0.8, 0.4],
            [0.8, 0.9],
            [0.2, 0.9],
        ],
        "reference_strategy": "bottom_center",
        "description": "Primary buffer zone along northern sector fence.",
    }

    # Register zone
    create_res = client.post("/api/zones", json=zone_payload)
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["zone_id"] == "zone-test-01"
    assert len(created["vertices"]) == 4

    # List zones
    list_res = client.get("/api/zones")
    assert list_res.status_code == 200
    zones = list_res.json()
    assert any(z["zone_id"] == "zone-test-01" for z in zones)
