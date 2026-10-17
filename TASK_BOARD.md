# Task Board

Statuses: `TODO`, `IN PROGRESS`, `BLOCKED`, `DONE`. Update only based on real work.

## Overall Lead
- [x] Confirm official rules, time window, AI assistance and IBM environment.
- [x] Freeze event schema and risk semantics (canonical status enum, ISO-8601 timestamps, explainable reasons).
- [x] Implement FastAPI health/event/list/stats/cameras/zones endpoints.
- [x] Implement SQLite storage, transaction sessions, and duplicate idempotency.
- [x] Implement deterministic risk engine with explanation reasons and recommended actions.
- [x] Run CV engine and FastAPI end-to-end integration tests (28 automated tests passing across backend and root suites).
- [x] Verify submission claims and package final deliverables.

## Lead 1 — Frontend
- [x] Read project context and API contract.
- [x] Create React/Vite dashboard shell.
- [x] Add centralized API client and typed event models.
- [x] Display video/replay panel and explicit status label.
- [x] Display event timeline, risk score, reasons and recommendation.
- [x] Add loading, empty, stale, disconnected and error states.
- [x] Add acknowledgement only if backend endpoint is agreed and implemented (PATCH /api/events/{id}/status wired with contract handling and offline simulation).
- [x] Test with real API and document setup (12 contract and integration tests passing; live API verified in offline fallback pending backend deployment).
- [x] Implement decoupled real-time event stream service (EventStreamService & PollingEventStreamService).
- [x] Implement global connection status indicator and notification center with deduplication and local read tracking.
- [x] Implement operator incident inspection and status workflow with integration pending notice.
- [x] Implement 20 Phase 4 real-time monitoring and event update tests (32 total frontend tests passing).
- [x] Complete Phase 5 final QA audit, crash-resilience formatters (`formatUtcTimestamp`, `safeLower`, `formatConfidencePercent`), and universal `ErrorBoundary`.
- [x] Implement WCAG keyboard accessibility, skip-to-content anchor, and universal focus indicators.
- [x] Achieve 51 passing automated tests across contract, real-time, and QA suites (0 failures).
- [x] Produce comprehensive demonstration script, technical handover guide (`leads/lead-1-frontend/HANDOVER.md`), and updated documentation.
- [x] Complete Phase 4 real frontend-backend integration: connect React dashboard to live FastAPI backend at `http://127.0.0.1:8000`, verify real YOLO event display (`evt-cam-north-01-zone-restricted-01-e7a264df`), live KPI stats binding, dual bounding-box evidence rendering, operator review status update via `PATCH /api/events/{id}/status` from `NEW` to `ACKNOWLEDGED`, SQLite persistence across server restart, and offline fallback recovery.

## Lead 2 — Computer Vision
- [x] Establish CV engine foundation (config, models, interfaces, logging, unit tests).
- [x] Confirm sample video authorization and format (synthetic and real sample streams verified).
- [x] Test OpenCV and selected pretrained detector in available environment (YOLOv8n CPU verified with real person detections).
- [x] Implement video reader and configured zone.
- [x] Implement documented zone-entry logic and temporal confirmation.
- [x] Add event ID, timestamp, cooldown and deduplication.
- [x] Send exact payload to backend (Live HTTP submission verified against FastAPI server; both replay and genuine YOLO events produce HTTP 201 created, HTTP 409 duplicate handling).
- [x] Test failure/replay fallback and document limitations.

## Lead 3 — LinuxONE / Environment
- [ ] Obtain official environment access and deployment requirements.
- [ ] Record `uname -m`, OS, Python, Node, Docker/Podman availability as applicable.
- [x] Check architecture compatibility for all native dependencies and model runtimes (s390x PyTorch/Ultralytics wheel blocker identified; distributed edge-inference architecture documented).
- [ ] Verify target registry images support `s390x` or use documented alternative.
- [ ] Prepare minimal deployment/run procedure based on actual access method.
- [ ] Deploy or test the required component on LinuxONE.
- [ ] Capture real logs/screenshots and document rollback/troubleshooting.

## Lead 4 — Support / QA / Demo
- [x] Read shared contracts and role instructions.
- [x] Verify README commands from a clean clone where possible.
- [x] Prepare test checklist and record pass/fail/not-tested (`INTEGRATION_TESTING.md` & `RELEASE_CHECKLIST.md`).
- [x] Check secrets and sample-data hygiene (zero keys, credentials, or model weights in Git).
- [x] Report blockers with reproduction steps (LinuxONE PyTorch wheel blocker documented).
- [x] Prepare demo script and backup recording (`DEMO_GUIDE.md` & `DEMO_SCRIPT.md`).
- [x] Review final claims and ensure replay is labelled.

## Integration checkpoints
- Hour 2: roles, environment, contracts confirmed.
- Hour 6: backend accepts sample event; frontend renders fixture; CV reads video.
- Hour 10: CV can post event and frontend can retrieve it.
- Hour 12: end-to-end minimum demo.
- Hour 16: persistence/risk reasons/deployment path checked.
- Hour 20: feature freeze and deployment validation.
- Final 4 hours: test, rehearse, package, submit.

## Blocker template
`BLOCKED — [module] — [exact error] — [commands/trials] — [help needed]`

Optional features must not delay the core video/event/risk/dashboard workflow.
