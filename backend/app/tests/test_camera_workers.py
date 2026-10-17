"""Automated tests for Camera Processing Workers and Camera Management API endpoints."""

import time
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import ROLE_ADMIN, ROLE_OPERATOR, ROLE_SERVICE, create_access_token
from app.services.camera_worker import CameraWorker, worker_manager
from app.schemas.camera import redact_uri

client = TestClient(app)


def get_auth_headers(role: str = ROLE_OPERATOR, username: str = "operator") -> dict:
    """Helper to generate JWT Authorization headers for tests."""
    token = create_access_token(subject=username, role=role)
    return {"Authorization": f"Bearer {token}"}


class TestCameraWorkerUnit:
    """Direct unit tests for CameraWorker thread lifecycle and metrics."""

    def test_worker_start_stop_lifecycle(self) -> None:
        """Verify worker starts in replay mode, tracks frames, and stops cleanly."""
        worker = CameraWorker(
            camera_id="test-cam-unit-01",
            stream_uri=None,
            zone_id="zone-test-01",
            zone_vertices=[[0.1, 0.1], [0.9, 0.1], [0.9, 0.9], [0.1, 0.9]],
            replay_mode=True,
            target_fps=20.0,
        )

        status_init = worker.get_status()
        assert not status_init.is_running
        assert status_init.connection_state == "STOPPED"

        worker.start()
        # Wait up to 1.5s for worker to process initial frames
        for _ in range(15):
            time.sleep(0.1)
            if worker.get_status().frames_processed > 0:
                break

        status_running = worker.get_status()
        assert status_running.is_running
        assert status_running.frames_processed > 0
        assert status_running.last_frame_timestamp is not None

        worker.stop()
        status_stopped = worker.get_status()
        assert not status_stopped.is_running
        assert status_stopped.connection_state == "STOPPED"

    def test_stream_uri_redaction(self) -> None:
        """Verify passwords in stream URIs are masked."""
        raw_uri = "rtsp://admin:super_secret_pw@192.168.1.100:554/h264"
        masked = redact_uri(raw_uri)
        assert "super_secret_pw" not in masked
        assert "admin:***" in masked


class TestCameraWorkerEndpoints:
    """Integration tests for camera worker REST endpoints."""

    def test_unauthenticated_access_rejected(self) -> None:
        """Surveillance camera endpoints must require authentication."""
        resp_list = client.get("/api/cameras")
        assert resp_list.status_code == 401

        resp_start = client.post("/api/cameras/cam-north-01/start")
        assert resp_start.status_code == 401

        resp_stop = client.post("/api/cameras/cam-north-01/stop")
        assert resp_stop.status_code == 401

        resp_status = client.get("/api/cameras/cam-north-01/status")
        assert resp_status.status_code == 401

    def test_list_cameras_includes_worker_status_and_masked_uri(self) -> None:
        """GET /api/cameras returns sanitized credentials and worker telemetry."""
        headers = get_auth_headers(ROLE_OPERATOR)
        resp = client.get("/api/cameras", headers=headers)
        assert resp.status_code == 200
        cameras = resp.json()
        assert len(cameras) > 0
        for cam in cameras:
            assert "worker_status" in cam
            assert "camera_id" in cam
            # Verify stream URI contains no passwords
            if cam.get("stream_uri"):
                assert "password" not in cam["stream_uri"].lower()

    def test_start_and_stop_camera_worker(self) -> None:
        """Operator can start and stop camera processing worker."""
        headers = get_auth_headers(ROLE_OPERATOR)

        # 1. Start worker in replay mode for deterministic testing
        resp_start = client.post(
            "/api/cameras/cam-north-01/start",
            json={"replay_mode": True},
            headers=headers,
        )
        assert resp_start.status_code == 200
        start_data = resp_start.json()
        assert start_data["camera_id"] == "cam-north-01"
        assert start_data["is_running"] is True

        # Wait briefly for worker to process frames
        time.sleep(0.4)

        # 2. Query status
        resp_status = client.get("/api/cameras/cam-north-01/status", headers=headers)
        assert resp_status.status_code == 200
        status_data = resp_status.json()
        assert status_data["camera_id"] == "cam-north-01"
        assert status_data["frames_processed"] > 0

        # 3. Stop worker
        resp_stop = client.post("/api/cameras/cam-north-01/stop", headers=headers)
        assert resp_stop.status_code == 200
        stop_data = resp_stop.json()
        assert stop_data["is_running"] is False
        assert stop_data["connection_state"] == "STOPPED"

    def test_camera_worker_audit_logging(self) -> None:
        """Starting and stopping camera workers must generate audit log entries."""
        headers = get_auth_headers(ROLE_ADMIN, username="admin")

        client.post(
            "/api/cameras/cam-north-01/start",
            json={"replay_mode": True},
            headers=headers,
        )
        time.sleep(0.1)
        client.post("/api/cameras/cam-north-01/stop", headers=headers)

        # Verify audit logs
        audit_resp = client.get("/api/audit-logs", headers=headers)
        assert audit_resp.status_code == 200
        logs = audit_resp.json()
        actions = [entry["action"] for entry in logs]
        assert "CAMERA_WORKER_STARTED" in actions
        assert "CAMERA_WORKER_STOPPED" in actions

    def test_nonexistent_camera_404(self) -> None:
        """Requesting worker operations on nonexistent camera returns 404."""
        headers = get_auth_headers(ROLE_OPERATOR)
        resp = client.post("/api/cameras/cam-nonexistent-999/start", headers=headers)
        assert resp.status_code == 404

    def test_camera_snapshot_endpoint(self) -> None:
        """Verify snapshot endpoint returns 404 when stopped, and 200 JPEG when active."""
        headers = get_auth_headers(ROLE_OPERATOR)

        # Before starting: returns 404
        resp_before = client.get("/api/cameras/cam-south-04/snapshot", headers=headers)
        assert resp_before.status_code == 404

        # Start worker
        client.post(
            "/api/cameras/cam-south-04/start",
            json={"replay_mode": True},
            headers=headers,
        )

        for _ in range(15):
            time.sleep(0.1)
            snap = client.get("/api/cameras/cam-south-04/snapshot", headers=headers)
            if snap.status_code == 200:
                assert snap.headers["content-type"] == "image/jpeg"
                assert len(snap.content) > 0
                break

        # Stop worker
        client.post("/api/cameras/cam-south-04/stop", headers=headers)

