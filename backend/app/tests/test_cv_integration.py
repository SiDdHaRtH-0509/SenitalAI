"""End-to-End Integration Tests: Computer Vision Engine & FastAPI Backend.

Verifies:
1. Complete CVPipeline execution against FastAPI backend (TestClient & live DB).
2. Detection, zone incursion, and event generation producing valid SecurityEvent payloads.
3. Event persistence in SQLite and verification via GET /api/events and GET /api/events/{id}.
4. Automated risk scoring and risk level calculation on CV events.
5. Idempotent duplicate event submission returning HTTP 409 and preventing duplicate DB rows.
6. Database persistence across session/engine reload (restart simulation).
7. Pipeline fault tolerance when backend is unreachable or returns server errors.
8. Event submission suppression when events_enabled=False.
"""

import os
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Ensure cv-engine/src is resolvable if present in workspace
for parent in Path(__file__).resolve().parents:
    candidate = parent / "cv-engine" / "src"
    if candidate.is_dir():
        if str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))
        break

try:
    from sentinel_cv.config import CVConfig
    from sentinel_cv.models import BoundingBox, Detection, FrameMetadata, SecurityEvent
    from sentinel_cv.pipeline import CVPipeline
    from sentinel_cv.backend_client import BackendClient
    HAS_SENTINEL_CV = True
except ImportError:
    HAS_SENTINEL_CV = False

from app.database import Base, get_db
from app.models.event import EventModel
from app.main import app
from app.core.security import ROLE_ADMIN, create_access_token

if not HAS_SENTINEL_CV:
    pytestmark = pytest.mark.skip(
        reason="cv-engine is an edge component and not present inside standalone backend container"
    )


def make_testclient_transport(test_client: TestClient):
    """Create a transport function routing BackendClient urllib requests to FastAPI TestClient."""
    def transport(req: urllib.request.Request, timeout: float):
        url = req.full_url
        # Extract relative path from URL (e.g., http://localhost:8000/api/events -> /api/events)
        if "://" in url:
            path = "/" + url.split("://", 1)[1].split("/", 1)[1]
        else:
            path = url

        method = req.get_method()
        headers = {k: v for k, v in req.headers.items()}
        data = req.data

        response = test_client.request(
            method=method,
            url=path,
            content=data,
            headers=headers,
        )
        return response.status_code, response.content, dict(response.headers)

    return transport


class TestCVBackendIntegration:
    """End-to-end integration test suite connecting CV pipeline with FastAPI backend."""

    def test_e2e_pipeline_stream_to_backend(self, client: TestClient, test_db_session: Session) -> None:
        """Verify CVPipeline stream in replay mode triggers zone incursion, submits to backend,

        and verifies persistence, risk scoring, and API retrieval.
        """
        # Configure pipeline in deterministic replay mode with TestClient transport
        transport = make_testclient_transport(client)
        config = CVConfig(
            input_source_type="replay",
            model_type="replay",
            camera_id="cam-north-01",
            zone_id="zone-restricted-01",
            replay_mode=True,
            events_enabled=True,
            temporal_confirmation_frames=1,
            deduplication_cooldown_sec=5.0,
            backend_url="http://testserver",
        )

        pipeline = CVPipeline.from_config(config=config, auto_init=True)
        # Wire custom transport to backend client
        pipeline.backend_client._transport = transport

        # Process 5 frames: frame 0 and 1 are outside zone, frame 2 enters zone and triggers event
        results = list(pipeline.process_stream(max_frames=5))

        assert len(results) == 5
        # Verify events emitted
        total_events = sum(len(r.events) for r in results)
        assert total_events >= 1

        # Check event submission results
        all_submissions = [sub for r in results for sub in r.event_submissions]
        assert len(all_submissions) >= 1
        first_sub = all_submissions[0]
        assert first_sub.success is True
        assert first_sub.status_code == 201
        assert first_sub.event_id is not None

        # Verify event in SQLite backend via TestClient GET /api/events
        resp = client.get("/api/events")
        assert resp.status_code == 200
        events_data = resp.json()
        assert len(events_data) == 1

        db_event = events_data[0]
        assert db_event["event_id"] == first_sub.event_id
        assert db_event["camera_id"] == "cam-north-01"
        assert db_event["zone_id"] == "zone-restricted-01"
        assert db_event["event_type"] == "RESTRICTED_ZONE_ENTRY"
        assert db_event["severity"] == "HIGH"
        assert db_event["status"] == "NEW"
        assert db_event["confidence"] >= 0.85

        # Verify backend risk scoring computation
        assert db_event["risk_score"] == 80  # 60 (HIGH) + 10 (zone breach) + 10 (conf >= 0.85)
        assert db_event["risk_level"] == "HIGH"
        assert len(db_event["reasons"]) == 3
        assert "recommended_action" in db_event

        # Verify GET /api/events/{event_id}
        single_resp = client.get(f"/api/events/{first_sub.event_id}")
        assert single_resp.status_code == 200
        assert single_resp.json()["event_id"] == first_sub.event_id

        # Verify GET /api/stats reflects the new event
        stats_resp = client.get("/api/stats")
        assert stats_resp.status_code == 200
        stats = stats_resp.json()
        assert stats["total_events"] == 1
        assert stats["by_risk_level"]["HIGH"] == 1

    def test_e2e_duplicate_event_prevention(self, client: TestClient, test_db_session: Session) -> None:
        """Verify submitting the exact same event produces HTTP 409 Conflict, is handled

        idempotently by BackendClient, and prevents duplicate records in the database.
        """
        transport = make_testclient_transport(client)
        backend_client = BackendClient(base_url="http://testserver", transport=transport)

        event = SecurityEvent(
            event_id="evt-dup-test-001",
            camera_id="cam-north-01",
            event_type="RESTRICTED_ZONE_ENTRY",
            timestamp="2026-10-17T12:00:00Z",
            severity="HIGH",
            confidence=0.91,
            zone_id="zone-restricted-01",
            description="Person entering zone",
            evidence={"frame_number": 42},
        )

        # 1. First submission -> HTTP 201 Created
        res1 = backend_client.submit_event(event)
        assert res1.success is True
        assert res1.status_code == 201
        assert res1.idempotent_duplicate is False

        # Verify 1 record exists in DB
        db_count = test_db_session.query(EventModel).count()
        assert db_count == 1

        # 2. Second submission of exact same event -> HTTP 409 Handled idempotently
        res2 = backend_client.submit_event(event)
        assert res2.success is True
        assert res2.status_code == 409
        assert res2.idempotent_duplicate is True
        assert res2.response_data.get("message") == "Duplicate event ID acknowledged"

        # Verify still exactly 1 record in DB (no duplicates created)
        db_count_after = test_db_session.query(EventModel).count()
        assert db_count_after == 1

    def test_e2e_persistence_survives_restart(self, test_db_path: str) -> None:
        """Verify that security events stored in the SQLite file survive closing the session

        and recreating the database engine (simulating a backend server restart).
        """
        # Session 1: Create table, start app, insert event
        engine1 = create_engine(f"sqlite:///{test_db_path}", connect_args={"check_same_thread": False})
        Session1 = sessionmaker(autocommit=False, autoflush=False, bind=engine1)
        Base.metadata.create_all(bind=engine1)

        db1 = Session1()
        def override_db1():
            try:
                yield db1
            finally:
                pass

        app.dependency_overrides[get_db] = override_db1
        with TestClient(app) as client1:
            transport1 = make_testclient_transport(client1)
            bclient = BackendClient(base_url="http://testserver", transport=transport1)

            event = SecurityEvent(
                event_id="evt-persist-test-777",
                camera_id="cam-south-02",
                event_type="RESTRICTED_ZONE_ENTRY",
                timestamp="2026-10-17T14:15:00Z",
                severity="CRITICAL",
                confidence=0.96,
                zone_id="zone-restricted-02",
                description="Person in restricted buffer zone",
                evidence={"frame_number": 108, "sensor": "optical"},
            )
            res = bclient.submit_event(event)
            assert res.success is True
            assert res.status_code == 201

        # Clean shutdown of Session 1 and engine 1
        db1.close()
        engine1.dispose()
        app.dependency_overrides.clear()

        # Session 2: "Restart" - create fresh engine pointing to existing SQLite file
        engine2 = create_engine(f"sqlite:///{test_db_path}", connect_args={"check_same_thread": False})
        Session2 = sessionmaker(autocommit=False, autoflush=False, bind=engine2)
        db2 = Session2()

        def override_db2():
            try:
                yield db2
            finally:
                pass

        app.dependency_overrides[get_db] = override_db2
        admin_token = create_access_token(subject="admin", role=ROLE_ADMIN)
        try:
            with TestClient(app) as client2:
                client2.headers["Authorization"] = f"Bearer {admin_token}"
                # Query the event created prior to restart
                resp = client2.get("/api/events/evt-persist-test-777")
                assert resp.status_code == 200
                data = resp.json()
                assert data["event_id"] == "evt-persist-test-777"
                assert data["camera_id"] == "cam-south-02"
                assert data["severity"] == "CRITICAL"
                assert data["risk_score"] == 100  # 80 (CRITICAL) + 10 + 10 = 100 max
                assert data["risk_level"] == "CRITICAL"
                assert data["evidence"]["frame_number"] == 108
                assert data["evidence"]["sensor"] == "optical"
        finally:
            db2.close()
            engine2.dispose()
            app.dependency_overrides.clear()

    def test_e2e_pipeline_backend_failure_resilience(self) -> None:
        """Verify pipeline handles network errors without crashing video stream processing."""
        def failing_transport(req: urllib.request.Request, timeout: float):
            import urllib.error
            raise urllib.error.URLError("Connection refused: backend service down")

        config = CVConfig(
            input_source_type="replay",
            model_type="replay",
            camera_id="cam-north-01",
            zone_id="zone-restricted-01",
            replay_mode=True,
            events_enabled=True,
            temporal_confirmation_frames=1,
            deduplication_cooldown_sec=5.0,
            api_max_retries=1,
        )

        pipeline = CVPipeline.from_config(config=config, auto_init=True)
        pipeline.backend_client._transport = failing_transport
        pipeline.backend_client.retry_backoff_seconds = 0.01

        # Process frames: Should complete normally without throwing unhandled exceptions
        results = list(pipeline.process_stream(max_frames=4))
        assert len(results) == 4

        # Verify event was generated on frame 2
        events_emitted = [ev for r in results for ev in r.events]
        assert len(events_emitted) >= 1

        # Verify submission failed gracefully
        submissions = [sub for r in results for sub in r.event_submissions]
        assert len(submissions) >= 1
        assert submissions[0].success is False
        assert "Connection refused" in submissions[0].error_message

    def test_e2e_pipeline_events_disabled_flag(self, client: TestClient, test_db_session: Session) -> None:
        """Verify that when events_enabled=False, pipeline does not submit events to backend."""
        transport = make_testclient_transport(client)
        config = CVConfig(
            input_source_type="replay",
            model_type="replay",
            camera_id="cam-north-01",
            zone_id="zone-restricted-01",
            replay_mode=True,
            events_enabled=False,
            temporal_confirmation_frames=1,
            deduplication_cooldown_sec=5.0,
            backend_url="http://testserver",
        )

        pipeline = CVPipeline.from_config(config=config, auto_init=True)
        pipeline.backend_client._transport = transport

        results = list(pipeline.process_stream(max_frames=4))
        # Events were generated by event generator
        events_emitted = [ev for r in results for ev in r.events]
        assert len(events_emitted) >= 1

        # But submission returned disabled result and nothing in DB
        submissions = [sub for r in results for sub in r.event_submissions]
        assert len(submissions) >= 1
        assert submissions[0].success is True
        assert submissions[0].status_code == 0
        assert "disabled by configuration" in submissions[0].error_message

        # DB has 0 records
        assert test_db_session.query(EventModel).count() == 0

    def test_real_yolo_stream_pipeline_to_backend(self, client: TestClient, test_db_session: Session) -> None:
        """Verify real YOLO pipeline processes actual video frames, detects real persons,

        evaluates zone incursions, and submits structured events to the FastAPI backend.
        """
        repo_root = Path(__file__).resolve().parents[3]
        weights = None
        for cand in (
            repo_root / "yolov8n.pt",
            repo_root / "cv-engine" / "yolov8n.pt",
            Path("yolov8n.pt").resolve(),
        ):
            if cand.exists():
                weights = str(cand)
                break
        video_path = repo_root / "cv-engine" / "sample-data" / "real_person_stream.mp4"
        if not weights or not video_path.exists():
            pytest.skip("YOLO weights or test video not available.")

        transport = make_testclient_transport(client)
        config = CVConfig(
            input_source_type="file",
            video_source=str(video_path),
            model_type="yolo",
            model_path=weights,
            camera_id="cam-north-01",
            zone_id="zone-restricted-01",
            replay_mode=False,
            events_enabled=True,
            temporal_confirmation_frames=1,
            deduplication_cooldown_sec=5.0,
            backend_url="http://testserver",
        )

        pipeline = CVPipeline.from_config(config=config, auto_init=True)
        pipeline.backend_client._transport = transport

        # Process 3 frames
        results = list(pipeline.process_stream(max_frames=3))
        assert len(results) == 3

        # Check real YOLO detections
        total_detections = sum(len(r.detections) for r in results)
        assert total_detections >= 1, "Real YOLO must detect persons in the test video"

        # Check that events were emitted and submitted
        all_submissions = [sub for r in results for sub in r.event_submissions]
        assert len(all_submissions) >= 1
        first_sub = all_submissions[0]
        assert first_sub.success is True
        assert first_sub.status_code == 201

        # Verify event in SQLite backend via TestClient
        resp = client.get(f"/api/events/{first_sub.event_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["event_id"] == first_sub.event_id
        assert data["camera_id"] == "cam-north-01"
        assert data["event_type"] == "RESTRICTED_ZONE_ENTRY"
        assert data["severity"] == "HIGH"
        assert data["confidence"] >= 0.50
        assert data["evidence"]["class_name"] == "person"
        assert "bounding_box" in data["evidence"]
        assert "reference_point" in data["evidence"]
        assert data["risk_score"] >= 60

    def test_real_yolo_empty_video_submits_zero_events(self, client: TestClient, test_db_session: Session) -> None:
        """Verify real YOLO on blank/text video produces 0 detections and submits 0 events to backend."""
        repo_root = Path(__file__).resolve().parents[3]
        weights = None
        for cand in (
            repo_root / "yolov8n.pt",
            repo_root / "cv-engine" / "yolov8n.pt",
            Path("yolov8n.pt").resolve(),
        ):
            if cand.exists():
                weights = str(cand)
                break
        video_path = repo_root / "cv-engine" / "sample-data" / "synthetic_border_test.mp4"
        if not weights or not video_path.exists():
            pytest.skip("YOLO weights or test video not available.")

        transport = make_testclient_transport(client)
        config = CVConfig(
            input_source_type="file",
            video_source=str(video_path),
            model_type="yolo",
            model_path=weights,
            camera_id="cam-north-01",
            zone_id="zone-restricted-01",
            replay_mode=False,
            events_enabled=True,
            temporal_confirmation_frames=1,
            deduplication_cooldown_sec=5.0,
            backend_url="http://testserver",
        )

        pipeline = CVPipeline.from_config(config=config, auto_init=True)
        pipeline.backend_client._transport = transport

        results = list(pipeline.process_stream(max_frames=3))
        assert len(results) == 3

        # Must have 0 detections and 0 events
        total_detections = sum(len(r.detections) for r in results)
        assert total_detections == 0
        total_events = sum(len(r.events) for r in results)
        assert total_events == 0
        assert test_db_session.query(EventModel).count() == 0


