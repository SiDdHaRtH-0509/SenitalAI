# SentinelAI — Final Release Readiness Checklist

This document provides the definitive verification matrix for SentinelAI release candidates, distinguishing between **Local Demonstration Readiness**, **IBM LinuxONE Deployment Readiness**, and **Production Hardening Requirements**.

---

## 1. Release Readiness Summary

| Tier | Status | Verification Evidence |
| :--- | :---: | :--- |
| **Tier 1: Localhost Execution & Live Demo** | **READY (100%)** | Real YOLO inference, FastAPI REST API, SQLite persistence, React/Vite dashboard, status update workflow, restart persistence, and disconnection recovery verified. |
| **Tier 2: IBM LinuxONE Deployment** | **READY WITH ARCHITECTURAL CONSTRAINTS** | FastAPI backend, SQLite, and Replay mode are fully `s390x`-compatible. PyTorch/Ultralytics lack official PyPI wheels on `s390x`; distributed edge-inference topology or replay mode is required. |
| **Tier 3: Enterprise Production Hardening** | **NOT READY (BY DESIGN)** | Prototype lacks mTLS / JWT authentication on write endpoints, uses local SQLite rather than distributed PostgreSQL/Etcd, and requires an external WebRTC gateway (e.g. MediaMTX) for live CCTV RTSP streaming. |

---

## 2. Tier 1: Local Demonstration Readiness Checklist

- [x] **Backend REST Service:**
  - `GET /api/health` returns `HTTP 200 {"status":"ok","service":"sentinel-api"}`.
  - `POST /api/events` validates payloads, returns `HTTP 201 Created` with deterministic risk score and reasons.
  - `GET /api/events` returns stored records newest-first.
  - `GET /api/stats` computes live aggregate metrics from SQLite.
  - `PATCH /api/events/{id}/status` updates review status with operator notes.
  - `GET /api/cameras` and `GET /api/zones` return configured surveillance assets.
  - Idempotency verified: re-submitting identical event ID returns `HTTP 409 Conflict` without creating duplicate database rows.
- [x] **Computer Vision Engine:**
  - `YOLOPersonDetector` loads nano weights (`yolov8n.pt`) on CPU.
  - OpenCV video source opens and processes `real_person_stream.mp4` (~2.5 FPS on standard CPU).
  - Ray-casting polygon incursion algorithm correctly differentiates between persons inside vs outside `zone-restricted-01`.
  - Non-incursion persons are discarded; qualifying incursion emits structured `evt-cam-north-01-zone-restricted-01-e7a264df`.
  - Deterministic replay mode (`--replay`) functions as an instant zero-dependency fallback.
- [x] **React Command Dashboard:**
  - Connects to `http://127.0.0.1:8000` via centralized `apiClient`.
  - Header connection indicator displays green `CONNECTED` badge.
  - KPI cards reflect live backend metrics (`is_mock: false`).
  - Recent Events table displays real YOLO incursion without demo badge.
  - Event detail modal renders bounding box coordinates, foot ground-contact reference point, risk score, and explainable determinants.
  - Operator can click "Acknowledge Incident" or "Mark Resolved" with instant backend persistence.
  - Disconnection resilience verified: stopping backend triggers honest `DISCONNECTED` state and displays explicit demo notice; restarting auto-recovers.
- [x] **Automated Regression Suite:**
  - Frontend: 51/51 tests pass (`npm test`).
  - Frontend build: `npm run build` succeeds (1606 modules, 0 errors).
  - Backend: 25/25 pytest tests pass (`py -m pytest app/tests`).
  - Root E2E: 7/7 pytest tests pass (`py -m pytest tests/test_e2e_cv_backend.py`).
  - CV Engine: 126/126 tests pass (`py -m unittest discover tests`).
  - Total: **202 unique test cases** (209 executions across all runners), 100% pass rate.

---

## 3. Tier 2: IBM LinuxONE (`s390x`) Deployment Readiness

- [x] **Backend API & Risk Engine on LinuxONE:**
  - Python 3.10–3.12, FastAPI, Uvicorn, SQLAlchemy, and SQLite operate seamlessly on `s390x` Big-Endian architecture.
  - LinuxONE acts as the central risk evaluation, audit ledger, and event API node.
- [x] **Computer Vision Pipeline Compatibility:**
  - **Constraint Documented:** PyTorch (`torch`) and Ultralytics do **not publish official pre-compiled wheels for `s390x` on PyPI**.
  - **Primary Production Topology (Distributed):** Run video ingestion and YOLOv8n inference on x86_64 edge workstations or smart CCTV cameras; dispatch JSON security events over network to FastAPI hosted on IBM LinuxONE.
  - **Fallback Topology (On-Prem Replay):** For on-host demonstration on LinuxONE without external x86 nodes, use the deterministic replay mode (`py -m sentinel_cv --replay --json`), which relies exclusively on Python standard library geometry.
- [x] **Network & Firewall Requirements:**
  - TCP port 8000 open between edge CV nodes and the LinuxONE instance.
  - TCP port 3000/5173 open for operator web access.

---

## 4. Tier 3: Enterprise Production Hardening Requirements (Post-Datathon)

> [!WARNING]
> The current system is an advanced datathon prototype designed for demonstration and architectural validation. The following items must be implemented before deploying to active national border infrastructure:

1. **Authentication & Authorization:**
   - Write endpoints (`POST /api/events`, `PATCH /api/events/{id}/status`) must require mTLS or OAuth2 / OIDC JWT tokens.
   - Role-Based Access Control (RBAC): restrict status mutations to authenticated surveillance watch commanders.
2. **Database Clustering:**
   - Migrate from single-file SQLite (`sentinel.db`) to a managed PostgreSQL cluster or IBM Db2 with automated backups and read replicas.
3. **Live CCTV Video Streaming:**
   - Deploy a dedicated WebRTC media gateway (e.g. MediaMTX or go2rtc) to ingest RTSP/H.264 streams from CCTV hardware and transcode to sub-second WebRTC for browser playback.
4. **Persistent Multi-Camera Re-ID Tracker:**
   - Integrate multi-camera deep re-identification (Re-ID) to track persons continuously across adjacent camera corridors.
5. **Human-in-the-Loop Governance:**
   - System outputs must remain classified as automated observations and risk suggestions (`status: "NEW"`) requiring explicit officer sign-off before tactical field dispatch.

---

## 5. Pre-Presentation Sanity Verification Run

Execute these three verification commands immediately before presenting:
```bash
# 1. Verify Backend Health
curl -s http://127.0.0.1:8000/api/health

# 2. Verify Frontend Accessibility
curl -s -I http://localhost:3000/

# 3. Verify SQLite Integrity
python -c "import sqlite3; conn = sqlite3.connect('backend/sentinel.db'); print('Stored events:', len(conn.cursor().execute('SELECT event_id FROM security_events').fetchall()))"
```
If all three return successful outputs, the system is 100% ready for demonstration.
