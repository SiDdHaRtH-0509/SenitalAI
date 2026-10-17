# Integration Testing Checklist

Mark a box only after the test is actually performed. Record commit hash, environment, result, and a brief log in the team notes.

## A. Repository and environment
- [x] Fresh clone succeeds for all active developers.
- [x] Each branch contains only its owner's intended changes.
- [x] No `.env`, keys, passwords, private footage or large model weights are committed.
- [x] Python/Node/runtime versions and machine architecture are recorded (Python 3.14.2, Node v22.14.0, Windows x86_64).
- [ ] LinuxONE compatibility has been checked for native packages and images.

## B. Backend
- [x] `GET /api/health` returns a healthy response (`HTTP 200 {"status":"ok","service":"sentinel-api"}`).
- [x] Valid event POST returns stored event and risk result (`HTTP 201 Created` with risk score and level).
- [x] Invalid confidence/timestamp/payload is rejected with a useful 4xx (`HTTP 422 Unprocessable Content`).
- [x] Duplicate `event_id` does not create duplicate records (`HTTP 409 Conflict` with idempotent acknowledgement).
- [x] `GET /api/events` returns stored events newest first.
- [x] `GET /api/stats` matches stored records.
- [x] Risk score includes reasons and does not claim threat probability.
- [x] Database survives the expected restart, if persistence is required (SQLite file persists across uvicorn restarts).

## C. Computer vision
- [x] Authorized video opens and frames are read (OpenCV & ReplayVideoSource verified).
- [x] Detector/model is loaded successfully in the declared environment.
- [x] Zone geometry is visible and configured correctly (Ray-casting polygon incursion).
- [x] Confirmed zone entry creates the expected event (`evt-cam-north-01-zone-restricted-01-ac0aebae`).
- [x] Continuous presence does not flood the API due to missing cooldown (`deduplication_cooldown_sec=5.0`).
- [x] Timestamp and confidence semantics match the contract (`confidence: 0.93`, ISO-8601 UTC timestamp).
- [x] Missing model/invalid video/backend outage produces a clear error (URLError/connection retry with graceful reporting).
- [x] Replay fallback is visibly labelled and uses the same API contract.

## D. Frontend
- [x] Dashboard loads without console-breaking errors.
- [x] Real backend events appear after refresh/poll.
- [x] Risk score, reasons, status and timestamps match API data.
- [x] Empty/loading/error/disconnected states work.
- [x] Browser-facing API URL is configured correctly (`http://localhost:8000`).
- [x] Acknowledgement control is shown only if the endpoint exists (`PATCH /api/events/{id}/status`).
- [x] Simulated/replay data is labelled.

## E. End-to-end
- [x] Start all required components from documented commands.
- [x] Trigger or replay one event (`py -m sentinel_cv.cli --replay --backend-url http://127.0.0.1:8000`).
- [x] Verify event reaches API and is stored (`POST /api/events` returns HTTP 201, retrievable via `GET /api/events`).
- [x] Verify risk reasons and score appear in the dashboard (computed by backend: score 80, level HIGH).
- [x] Restart the application and repeat (Killed PID 50076, restarted uvicorn, verified event retrieval intact).
- [x] Capture a reproducible run log and screenshots.

## F. LinuxONE
- [ ] Actual target architecture and OS are recorded.
- [ ] Required service runs on the intended target.
- [ ] Architecture-compatible package/image use is verified.
- [ ] Approved network path works.
- [ ] Health check and event POST succeed against the deployed service.
- [ ] Actual deployment evidence is saved without credentials.
- [ ] Components running elsewhere are explicitly identified.

## G. Submission
- [x] README commands match the tested build.
- [ ] Demo has been rehearsed at least twice.
- [x] Backup recording/fixtures are ready.
- [x] Claims are supported by logs or observable behavior.
- [x] Limitations and human-in-the-loop design are explained.
- [ ] Official submission requirements are checked.

## Result log template
| Test | Environment/commit | Result (PASS/FAIL/NOT RUN) | Evidence/notes |
|---|---|---|---|
| Backend Health & Event REST API | Localhost / Python 3.14.2 / branch `integration/cv-backend-e2e` | PASS | 18 unit/contract tests passing; `GET /api/health` returns HTTP 200. |
| CV Engine Video Ingestion & Incursion | Localhost / Python 3.14.2 / branch `integration/cv-backend-e2e` | PASS | 122 tests passing; pure Python ray-casting polygon incursion detection. |
| CV -> FastAPI Live Stream E2E | Localhost (127.0.0.1:8000) / branch `integration/cv-backend-e2e` | PASS | CLI replay stream submitted event `evt-cam-north-01-zone-restricted-01-ac0aebae` over live HTTP, received HTTP 201. |
| Duplicate Event Prevention (Idempotency) | Localhost (127.0.0.1:8000) / branch `integration/cv-backend-e2e` | PASS | Re-submitting identical event returns HTTP 409 Conflict, acknowledged by BackendClient without creating duplicate DB rows. |
| Persistence Across Backend Restart | Localhost (SQLite `sentinel.db`) / branch `integration/cv-backend-e2e` | PASS | Uvicorn process terminated, restarted; `GET /api/events/evt-cam-north-01-zone-restricted-01-ac0aebae` returned 200 with full integrity. |
| Frontend Contract & Real-Time Polling | Node v22.14.0 / React + Vite / branch `integration/cv-backend-e2e` | PASS | 51 automated frontend tests passing; polling and offline state fallback verified. |
| Cross-Module Automated Integration Suite | Pytest / Python 3.14.2 (`tests/test_e2e_cv_backend.py`) | PASS | 5/5 automated integration tests pass in 0.54s covering live pipeline, duplicate prevention, restart, failure resilience, and disabled flags. |
