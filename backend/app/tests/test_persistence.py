"""Tests for Database Persistence across application restarts."""

import os
import tempfile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app


def test_database_persistence_across_restarts():
    """Verify that stored events and statuses persist across application restarts.

    Simulates:
    1. First application run: Submit event, update status, verify persistence.
    2. Shutdown: Close all connections and dispose engine.
    3. Second application run: Create new engine & session on same SQLite file.
    4. Verify: All records remain intact and recoverable.
    """
    temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_file.close()
    db_file = temp_file.name

    db_url = f"sqlite:///{db_file}"
    event_id = "evt-restart-persistence-001"

    try:
        # Phase 1: First application run
        engine1 = create_engine(db_url, connect_args={"check_same_thread": False})
        Session1 = sessionmaker(autocommit=False, autoflush=False, bind=engine1)
        Base.metadata.create_all(bind=engine1)

        def override_get_db1():
            db = Session1()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db1

        with TestClient(app) as client1:
            # 1. Post event
            post_res = client1.post(
                "/api/events",
                json={
                    "event_id": event_id,
                    "camera_id": "cam-north-01",
                    "timestamp": "2026-10-17T15:00:00Z",
                    "severity": "CRITICAL",
                    "confidence": 0.94,
                    "zone_id": "zone-restricted-01",
                    "description": "Perimeter breach test before restart",
                },
            )
            assert post_res.status_code == 201
            assert post_res.json()["status"] == "NEW"

            # 2. Update status to ACKNOWLEDGED with note
            patch_res = client1.patch(
                f"/api/events/{event_id}/status",
                json={"status": "ACKNOWLEDGED", "notes": "Acknowledged prior to server reboot."},
            )
            assert patch_res.status_code == 200
            assert patch_res.json()["status"] == "ACKNOWLEDGED"

        # Phase 2: Full shutdown simulation
        app.dependency_overrides.clear()
        engine1.dispose()

        # Phase 3: Reboot - New engine and session on same physical SQLite file
        engine2 = create_engine(db_url, connect_args={"check_same_thread": False})
        Session2 = sessionmaker(autocommit=False, autoflush=False, bind=engine2)

        def override_get_db2():
            db = Session2()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db2

        with TestClient(app) as client2:
            # Verify event survived restart
            get_res = client2.get(f"/api/events/{event_id}")
            assert get_res.status_code == 200
            persisted = get_res.json()
            assert persisted["event_id"] == event_id
            assert persisted["status"] == "ACKNOWLEDGED"
            assert "Acknowledged prior to server reboot" in persisted["operator_notes"]
            assert persisted["severity"] == "CRITICAL"
            assert persisted["confidence"] == 0.94

        app.dependency_overrides.clear()
        engine2.dispose()

    finally:
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
            except OSError:
                pass
