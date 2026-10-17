# SentinelAI — Phase 2: Live CCTV Ingestion & Continuous Video Analytics Report

**Project:** SentinelAI — Intelligent Video Analytics Platform for Border Surveillance  
**Phase:** Phase 2: Live CCTV Ingestion & Continuous Video Analytics  
**Date:** October 17, 2026  
**Status:** Verification Complete — 257/257 Automated Tests Passing (100% Success Rate)  

---

## 1. Executive Summary

Phase 2 extends SentinelAI from static/replay video processing into a resilient, continuous live CCTV analytics platform. The system now ingests live RTSP camera streams, performs real-time YOLOv8n object detection and restricted-zone polygon incursion analysis, delivers live camera worker telemetry, serves triage snapshots to the operator dashboard, and enforces security hardening across all newly added lifecycle endpoints.

All implementations strictly adhere to the non-negotiable principles established in Phase 1:
- **Zero Regressions:** All 241 existing tests continue to pass; 16 new automated tests were added, bringing the verified test matrix to **257/257 tests passing**.
- **Security Integrity:** RTSP credentials embedded in stream URIs are masked before logging, storage, or API serialization. All camera worker controls require authenticated `OPERATOR` or `ADMIN` roles, enforce CSRF double-cookie validation, and log to the SHA-256 hash-chained audit log.
- **Architectural Separation:** Live video ingestion for AI inference is strictly decoupled from browser video rendering.
- **Fault-Tolerant Concurrency:** Frame acquisition and inference run on decoupled worker threads with bounded drop-oldest queues, preventing memory leaks, buffer bloat, and application freezes.

---

## 2. Ingestion vs. Live Playback Separation

A fundamental architectural distinction in surveillance platforms is the separation between **AI Video Ingestion** and **Operator Browser Playback**:

```
+-----------------------------------------------------------------------------------+
|                              CCTV CAMERA (RTSP Stream)                             |
|                           rtsp://camera.border:554/live                           |
+-----------------------------------------+-----------------------------------------+
                                          |
                    +---------------------+---------------------+
                    |                                           |
                    v                                           v
    [ AI Ingestion Pipeline ]                   [ Browser Playback Gateway ]
    Backend Python Worker (OpenCV / TCP)        External Media Gateway (MediaMTX / go2rtc)
    - Decoupled frame grabber                   - RTSP demuxing & remuxing
    - Drop-oldest bounded queue                 - WebRTC (sub-500ms latency)
    - YOLOv8n person detection                  - Low-Latency HLS (LL-HLS)
    - Polygonal zone incursion ray-casting      - Browser HTML5 <video> / canvas
    - Temporal confirmation & cooldown          - Operator situational awareness
    - HTTP event submission to FastAPI
                    |
                    v
    [ Operator Triage Snapshots ]
    GET /api/cameras/{id}/snapshot
    - Zero external dependencies
    - On-demand JPEG frame with bounding boxes
    - Polled by dashboard triage modal
```

### Why Browsers Cannot Play RTSP Directly
Modern web browsers (Chrome, Firefox, Safari, Edge) do not natively support the RTSP/RTP/RTCP protocols or raw H.264/H.265 transport streams via standard `<video>` tags. RTSP relies on stateful control channels (DESCRIBE, SETUP, PLAY) typically negotiated over UDP or interleaved TCP, which browser JavaScript sandbox environments cannot directly open without proxy mediation.

### Production Streaming Gateway Options
For full-motion 30 FPS video display in the browser, the recommended deployment architecture incorporates an edge media proxy:
1. **MediaMTX (formerly rtsp-simple-server):**
   - Single static Go binary with zero external dependencies.
   - Ingests RTSP from IP cameras and restream to WebRTC (sub-500ms latency), LL-HLS (2–3s latency), or WHEP.
   - Low CPU overhead when remuxing H.264 streams without transcoding.
2. **go2rtc:**
   - Ultra-lightweight streaming server with native WebRTC, MSE (Media Source Extensions), and MJPEG support.
   - Built-in two-way audio support for perimeter talkdown speakers.

### Built-in SentinelAI Snapshot Triage
To provide immediate visual verification without requiring third-party gateway binaries during testing or initial deployment, SentinelAI provides a native snapshot delivery mechanism:
- Endpoint: `GET /api/cameras/{camera_id}/snapshot`
- Returns: Latest processed JPEG frame (`image/jpeg`) with `Cache-Control: no-cache, no-store, must-revalidate`.
- Performance: Generated on the fly from the camera worker's active memory buffer without disk I/O.

---

## 3. RTSP Video Source & Fault Tolerance

The `RTSPVideoSource` class (`cv-engine/src/sentinel_cv/rtsp_source.py`) implements the standardized `IVideoSource` interface with enterprise fault tolerance:

### Technical Specifications
- **Transport Protocol:** Forced TCP (`OPENCV_FFMPEG_CAPTURE_OPTIONS = "rtsp_transport;tcp"`). Prevents UDP packet loss, frame shearing, and macroblocking over lossy long-distance border network links.
- **Credential Masking:** Regex-based URI sanitizer (`redact_stream_url()`) masks embedded basic auth credentials (`rtsp://user:***@host:port/path`) before any log entry or exception message is generated.
- **Connection State Machine:**
  ```
  DISCONNECTED -> CONNECTING -> CONNECTED -> (frame drop / disconnect) -> RECONNECTING -> CONNECTED
                                      |
                                      +-> (max retries exceeded) -> FAILED
  ```
- **Exponential Backoff:** Configurable initial backoff (default 1.0s), backoff multiplier (2.0x), and maximum backoff cap (30.0s).
- **Bounded Read Timeouts:** Monitors frame arrival intervals. If no frame arrives within `read_timeout_seconds` (default 5.0s), the source declares a stream stall and triggers automatic reconnection.
- **Clean Release:** Comprehensive context manager (`__enter__`, `__exit__`) and `release()` method guaranteeing OpenCV capture handles are closed and FFMPEG worker threads terminated.

---

## 4. Concurrency Architecture & Queueing Policy

To process high-resolution video streams in real time without unbounded memory growth or latency drift, `CameraWorker` (`backend/app/services/camera_worker.py`) implements a decoupled threading model:

```
[ Camera Feed ] ---> [ Capture Thread ]
                            |
                     (queue.Queue(maxsize=2))
                     [ Frame Drop Policy ]
                     If full: drop oldest frame (get_nowait)
                     Put newest frame (put_nowait)
                            |
                            v
                     [ Inference Thread ]
                            |
                     [ YOLOv8n Detection ]
                            |
                     [ Zone Incursion Analysis ]
                            |
                     [ Event Generator (Cooldown/Dedupe) ]
                            |
                     [ HTTP Client / FastAPI ]
```

### Frame Dropping Rationale
Camera streams continuously produce frames at fixed rates (e.g., 25–30 FPS). If the computer vision inference pipeline operates at 10–15 FPS on CPU, a standard FIFO queue would accumulate an ever-growing backlog of unanalyzed frames. Within minutes:
- Memory consumption would increase linearly until an Out-Of-Memory (OOM) crash occurs.
- Security events would suffer from severe latency drift (e.g., detecting an incursion 45 seconds after the intruder has already left the zone).

By utilizing a bounded `queue.Queue(maxsize=2)` with a drop-oldest policy, SentinelAI guarantees:
1. **Near-Zero Latency:** Inference always runs on the freshest possible frame captured within the last ~50 milliseconds.
2. **Constant Memory Footprint:** Memory usage remains strictly bounded regardless of stream duration.
3. **Thread Isolation:** Any runtime decoder failure or OpenCV exception is caught inside the worker thread and recorded to telemetry without affecting the FastAPI application.

---

## 5. Continuous Zone Analysis & Deduplication

In a continuous CCTV feed, an intruder walking through a restricted zone remains present across hundreds of consecutive frames. Without temporal logic, this would produce an unmanageable event flood.

SentinelAI enforces a 3-tier filtration pipeline:

1. **Polygon Ray-Casting & Coordinate Normalization:**
   - The database stores zone polygons with normalized coordinates in the range `[0.0, 1.0]`.
   - `CameraWorker` inspects vertex coordinates: if all vertices are $\le 1.0$, they are dynamically scaled to the camera's native pixel resolution (`(x * 1280, y * 720)`).
   - The ray-casting algorithm calculates bottom-center bounding box containment within the zone.

2. **Temporal Incursion Confirmation:**
   - Transient detections (e.g., single-frame motion artifacts or bird shadows) are rejected.
   - An alert requires detection across `min_consecutive_frames` (default: 2 consecutive frames).

3. **Event Cooldown Deduplication:**
   - Once a security event is triggered for a camera/zone pair, a cooldown timer (default: 5.0 seconds) is engaged.
   - Subsequent detections of the same ongoing intrusion within the cooldown window increment telemetry metrics without flooding the database with duplicate events.
   - When the target exits the zone or the cooldown expires, new incursions trigger fresh events.

4. **Database Idempotency:**
   - The backend `POST /api/events` endpoint enforces deterministic event ID uniqueness (`event_id`).
   - Duplicate submissions return `HTTP 409 Conflict` with an idempotent error response, leaving the database state pristine and logging an audit event.

---

## 6. Camera Worker Management API

The backend camera endpoints (`backend/app/api/endpoints/cameras.py`) provide comprehensive lifecycle management:

| Method | Endpoint | Authorization | Description |
|---|---|---|---|
| `GET` | `/api/cameras` | Operator / Admin | Lists cameras with sanitized stream URIs and attached live worker status |
| `POST` | `/api/cameras/{id}/start` | Operator / Admin | Initiates background worker in live RTSP or synthetic replay mode |
| `POST` | `/api/cameras/{id}/stop` | Operator / Admin | Cleanly stops worker thread, drains queue, and releases stream handles |
| `GET` | `/api/cameras/{id}/status` | Operator / Admin | Returns real-time telemetry (FPS, latency, frame count, alert count) |
| `GET` | `/api/cameras/{id}/snapshot` | Operator / Admin | Returns latest processed JPEG frame with no-cache headers |

### Telemetry Schema (`CameraWorkerStatus`)
```json
{
  "camera_id": "cam-north-01",
  "is_running": true,
  "state": "CONNECTED",
  "source_type": "rtsp",
  "stream_uri_masked": "rtsp://admin:***@10.0.0.10:554/ch01",
  "fps": 18.5,
  "latency_ms": 54.2,
  "frames_processed": 1420,
  "events_emitted": 3,
  "reconnect_count": 0,
  "last_frame_timestamp": "2026-10-17T16:30:15.120Z",
  "last_error": null
}
```

---

## 7. Frontend Dashboard Enhancements

The React/Vite dashboard was updated with operator-grade controls for live CCTV feeds:

1. **Camera Registry (`#/cameras`):**
   - **Live Connection Badges:** Visual status pills reflecting real-time state (`AI ACTIVE` [green], `CONNECTING` [amber], `FAULT` [red], `STOPPED` [gray]).
   - **Stream Modality Indicators:** Clear visual distinction between live `RTSP STREAM` feeds and `DEMO REPLAY` streams.
   - **Inline Lifecycle Controls:** Direct "Start Analytics" and "Stop" action buttons with real-time UI feedback.
   - **Telemetry Strip:** Inline display of live FPS, frame processing latency (ms), total processed frames, and emitted security alerts.

2. **Camera Detail Modal (`CameraDetailModal.tsx`):**
   - **Live Snapshot Polling Tab:** Interactive viewport polling `/api/cameras/{id}/snapshot` every 2 seconds when analytics is running.
   - **Telemetry Metrics Grid:** Cards displaying active worker state, frame rate, inference latency, and connection drop counts.
   - **Lifecycle Management:** Start and Stop controls integrated with role-based permission checks and toast notifications.

---

## 8. Controlled RTSP Simulation Environment

To facilitate automated integration testing and demonstrations in environments without physical RTSP hardware, a standalone simulation script was developed:

- **Location:** `scripts/simulate_rtsp_stream.py`
- **Features:**
  - Synthesizes 1280x720 video frames featuring a border perimeter, security fence, camera telemetry OSD, and a moving target walking into a calibrated restricted zone.
  - Automatically submits real security events to the live FastAPI backend via `POST /api/events` using M2M service token authentication.
  - Demonstrates cooldown deduplication and temporal confirmation live against the running backend.
  - Generates verifiable events (`evt-cam-north-01-...`) visible in the React dashboard in real time.

---

## 9. Comprehensive Empirical Test Results

Every automated test across the SentinelAI codebase was executed and verified. The entire test suite achieved a **100% pass rate**:

```
========================================================================================
                          SENTINELAI AUTOMATED TEST MATRIX
========================================================================================
Test Suite                             Category           Tests Run   Passed   Failed
----------------------------------------------------------------------------------------
sentinel_cv (Unit & Ingestion)         Computer Vision       134        134       0
backend (FastAPI / Auth / Workers)     Backend & API          57         57       0
e2e_cv_backend (Cross-Module)          End-to-End              7          7       0
frontend (Vitest / API Client)         Frontend UI            59         59       0
----------------------------------------------------------------------------------------
TOTAL AUTOMATED TESTS                                        257        257       0
========================================================================================
Frontend TypeScript Typecheck (tsc):   PASSED (0 errors)
Frontend Production Build (vite):      PASSED (dist/ built in 2.08s)
```

### Test Suite Execution Breakdown
1. **CV Engine Unit Tests (`134 passed` in 6.51s):**
   - RTSP video source connection, reconnection, and backoff (`test_rtsp_source.py` — 8 tests).
   - Video source adapters, synthetic fallback, and container decoding (`test_video_source.py` — 14 tests).
   - Ray-casting polygon zone math and bottom-center detection (`test_zone.py` — 13 tests).
   - Event generator temporal confirmation and cooldown deduplication (`test_event_generator.py` — 16 tests).
   - YOLO detector integration and bounding box transformation (`test_detector.py` — 12 tests).
   - Pipeline coordination and telemetry tracking (`test_pipeline.py` — 11 tests).
   - CLI parsing and JSON output serialization (`test_cli.py` — 12 tests).
   - Backend client HTTP submission and retry logic (`test_backend_client.py` — 15 tests).
   - Models and configuration validation (`test_models.py`, `test_config.py` — 33 tests).

2. **Backend Pytest Suite (`57 passed` in 28.64s):**
   - Camera worker lifecycle, status, snapshot, and URI masking (`test_camera_workers.py` — 8 tests).
   - JWT authentication, password hashing, and token expiration (`test_auth.py` — 10 tests).
   - Role-based access control (`ADMIN`, `OPERATOR`, `SERVICE`) on all endpoints.
   - CSRF double-cookie validation and exemptions for M2M Bearer tokens.
   - SHA-256 hash-chained audit logging and tampering detection (`test_security_hardening.py`).
   - SQLite WAL persistence and schema validation across server restarts (`test_persistence.py`).
   - Real YOLOv8n video stream pipeline integration (`test_cv_integration.py`).

3. **Root End-to-End Integration Tests (`7 passed` in 5.79s):**
   - Full pipeline stream-to-backend submission.
   - Duplicate event prevention and HTTP 409 idempotency.
   - Real YOLO inference on synthetic person video stream.
   - Backend failure resilience and offline queuing.

4. **Frontend Vitest Suite (`59 passed` in 439ms):**
   - ApiClient contract handling, error translation, and network timeout handling.
   - Cookie-based authentication and CSRF token transmission.
   - Real-time polling, notification deduplication, and unread counters.
   - Crash-resilience against corrupted timestamps, missing fields, and NaN confidence values.

---

## 10. Security Hardening & Secret Protection

All Phase 1.1 / 1.2 security mechanisms remain fully active and enforced across the new Phase 2 features:

1. **RTSP Credential Sanitization:**
   - Any RTSP stream URI configured with embedded credentials (`rtsp://username:password@host:port/path`) is sanitized via regular expression masking before being returned in API responses or written to logs.
   - Database serialization strips cleartext passwords from camera records.

2. **Role-Based Access Control (RBAC):**
   - `/api/cameras/{id}/start` and `/api/cameras/{id}/stop` require active `OPERATOR` or `ADMIN` roles.
   - Unauthenticated requests are rejected with `HTTP 401 Unauthorized`.
   - Operators cannot elevate their permissions or delete audit trails (`HTTP 403 Forbidden`).

3. **CSRF Protection:**
   - Browser-initiated POST requests to camera lifecycle endpoints require matching `X-CSRF-Token` headers corresponding to the `sentinel_csrf` cookie.
   - Direct M2M service requests utilizing `Authorization: Bearer <token>` or `X-API-Key` headers are verified securely and exempted from CSRF requirements.

4. **Cryptographic Audit Chaining:**
   - Every camera worker start, stop, or failure event generates a tamper-evident audit record in `audit_logs`.
   - Each audit record is linked to its predecessor via SHA-256 hash chaining (`previous_hash` $\to$ `record_hash`), enabling cryptographic verification of the complete operational history.

---

## 11. IBM LinuxONE & Architecture Compatibility Analysis

### Architecture Considerations (s390x / IBM LinuxONE)
IBM LinuxONE systems utilize the **s390x** architecture, which is **big-endian** and uses the IBM z/Architecture instruction set:

1. **Endianness:**
   - Python code utilizing raw byte manipulation or C-extensions must account for byte ordering.
   - OpenCV and NumPy handle native endianness transparently for standard RGB/BGR arrays, but raw binary protocol serialization must avoid assuming little-endian integer layouts.

2. **Deep Learning Frameworks (PyTorch / Ultralytics):**
   - Standard PyTorch wheels (`pip install torch`) are compiled for `x86_64` and `aarch64`. Pre-built PyTorch binaries for `s390x` are typically provided via IBM Open Enterprise SDK for Python or IBM Watson Machine Learning for z/OS (WMLz).
   - Alternatively, YOLOv8 models can be exported to **ONNX** format (`yolov8n.onnx`) and executed using ONNX Runtime with OpenBLAS on LinuxONE.

3. **FFMPEG & Video Codecs:**
   - FFMPEG is fully supported on LinuxONE (Red Hat Enterprise Linux / SUSE Linux Enterprise Server on s390x) with hardware-accelerated CPACF cryptographic instructions.
   - Software H.264 decoding is efficient on modern IBM Telum / z16 processors with multi-threading.

4. **Honest Readiness Status:**
   - The SentinelAI codebase is written using standard POSIX-compliant Python, avoids platform-specific system calls, and uses cross-platform path handling.
   - **Verification Caveat:** In accordance with project non-negotiable rules, because the current development and verification environment is Windows 11 / x86_64, **IBM LinuxONE readiness must be characterized as "Architecture Ready / Pending Hardware Test" rather than claiming validated s390x execution**.

---

## 12. Production Readiness Assessment & Operational Limitations

### Production-Ready Capabilities
- Continuous RTSP ingestion with automatic reconnect and exponential backoff.
- Multi-threaded worker management with drop-oldest bounded queueing.
- Temporal confirmation and cooldown deduplication for zone incursions.
- Operator dashboard integration with live telemetry and snapshot triage.
- Complete 257/257 automated test coverage across frontend, backend, and CV engine.
- Enterprise security: JWT auth, RBAC, CSRF protection, and SHA-256 audit logs.

### Operational Limitations & Scalability Roadmap
1. **Database Concurrency:**
   - SentinelAI currently uses SQLite in WAL mode with a 30-second busy timeout.
   - While suitable for 4–8 concurrent cameras, scaling to large border sectors (50+ cameras) requires migrating to PostgreSQL with connection pooling (e.g., PgBouncer) to avoid database lock contention.
2. **Browser Video Streaming:**
   - The current dashboard provides snapshot-based triage (0.5–1 FPS JPEG polling).
   - For continuous 30 FPS video playback in browser tabs, an edge streaming gateway (MediaMTX) should be deployed in front of the CCTV network to provide WebRTC feeds.
3. **Hardware Acceleration:**
   - On CPU-only environments, YOLOv8n achieves ~15–20 FPS per stream. For high-density deployments (>10 concurrent 1080p streams), hardware inference acceleration (NVIDIA TensorRT, Intel OpenVINO, or IBM Telum AI accelerator) should be configured.

---

## 13. Conclusion

Phase 2: Live CCTV Ingestion & Continuous Video Analytics has achieved all engineering and architectural milestones. SentinelAI provides a resilient, secure, and observable surveillance pipeline ready for live demonstrations and field evaluation.
