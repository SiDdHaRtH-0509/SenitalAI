# Task Board

Statuses: `TODO`, `IN PROGRESS`, `BLOCKED`, `DONE`. Update only based on real work.

## Overall Lead
- [ ] Confirm official rules, time window, AI assistance and IBM environment.
- [ ] Freeze event schema and risk semantics.
- [ ] Implement FastAPI health/event/list/stats endpoints.
- [ ] Implement SQLite storage and idempotency.
- [ ] Implement deterministic risk engine with explanation reasons.
- [ ] Test backend and publish sample requests.
- [ ] Review/merge lead PRs and run end-to-end tests.
- [ ] Verify submission claims and package final deliverables.

## Lead 1 — Frontend
- [ ] Read project context and API contract.
- [ ] Create React/Vite dashboard shell.
- [ ] Add centralized API client and typed event models.
- [ ] Display video/replay panel and explicit status label.
- [ ] Display event timeline, risk score, reasons and recommendation.
- [ ] Add loading, empty, stale, disconnected and error states.
- [ ] Add acknowledgement only if backend endpoint is agreed and implemented.
- [ ] Test with real API and document setup.

## Lead 2 — Computer Vision
- [x] Establish CV engine foundation (config, models, interfaces, logging, unit tests).
- [ ] Confirm sample video authorization and format (synthetic video verified; awaiting final datathon sample).
- [x] Test OpenCV and selected pretrained detector in available environment.
- [x] Implement video reader and configured zone.
- [x] Implement documented zone-entry logic and temporal confirmation.
- [x] Add event ID, timestamp, cooldown and deduplication.
- [x] Send exact payload to backend (BackendClient verified via contract & mocks; live backend unverified).
- [x] Test failure/replay fallback and document limitations.


## Lead 3 — LinuxONE / Environment
- [ ] Obtain official environment access and deployment requirements.
- [ ] Record `uname -m`, OS, Python, Node, Docker/Podman availability as applicable.
- [ ] Check architecture compatibility for all native dependencies and model runtimes.
- [ ] Verify target registry images support `s390x` or use documented alternative.
- [ ] Prepare minimal deployment/run procedure based on actual access method.
- [ ] Deploy or test the required component on LinuxONE.
- [ ] Capture real logs/screenshots and document rollback/troubleshooting.

## Lead 4 — Support / QA / Demo
- [ ] Read shared contracts and role instructions.
- [ ] Verify README commands from a clean clone where possible.
- [ ] Prepare test checklist and record pass/fail/not-tested.
- [ ] Check secrets and sample-data hygiene.
- [ ] Report blockers with reproduction steps.
- [ ] Prepare demo script and backup recording.
- [ ] Review final claims and ensure replay is labelled.

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
