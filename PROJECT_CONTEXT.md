# PROJECT CONTEXT — SENTINELAI v1.0

## Mission
Build an IBM Z Datathon prototype that turns authorized CCTV-style video into structured observable events, transparent rule-based risk prioritization, and human-reviewed recommendations.

## Core flow
Video → existing object detector → configured-zone event logic → event API → risk engine → event history → operator dashboard → human review.

## Fixed MVP
1. One authorized prerecorded CCTV-style video.
2. One existing pretrained person detector supported by the selected environment.
3. One configurable zone.
4. `RESTRICTED_ZONE_ENTRY` event generation using documented geometric and temporal criteria.
5. Backend API validates and stores events.
6. Deterministic risk score with explicit reasons.
7. Frontend displays events, score, reasons, recommended human action and status.
8. LinuxONE deployment/integration is implemented only to the extent supported by the actual Datathon environment and rules.
9. A labelled replay fallback is allowed; it must never be presented as live inference.

## Out of scope
- Facial recognition, identity inference, or person re-identification.
- Autonomous enforcement or claims that a person is dangerous.
- Training a custom model from scratch.
- A production-ready national-border surveillance deployment.
- Mobile applications, multi-camera orchestration, complex microservices, or paid API dependencies unless required by official rules and explicitly approved by the lead.
- Unsupported accuracy, latency, or impact claims.

## Team model: five people total
- Overall Lead (user): architecture, API contract, backend/risk engine, merge decisions, end-to-end integration, final verification and submission.
- Lead 1 — Frontend: React/Vite dashboard and API consumption.
- Lead 2 — Computer Vision: video input, detector, zone logic and event producer.
- Lead 3 — LinuxONE/Environment: architecture compatibility checks, deployment packaging and deployment verification; Lead 3 must not rewrite the CV or frontend modules.
- Lead 4 — Support: QA checklist, documentation, sample-data hygiene, task tracking and demo preparation. This role is intentionally bounded and should not block the core implementation.

## Technology defaults
- Backend: Python, FastAPI, Uvicorn, SQLite.
- CV: OpenCV and a compatible existing pretrained detector.
- Frontend: React + Vite.
- Integration: HTTP JSON; polling is acceptable.
- Repository: Git/GitHub.
- Deployment: use the actual organizer-provided LinuxONE access method; do not assume a specific cloud, container platform, IDE, or service.

## Correctness and safety
- A detected person is not proof of malicious intent.
- Detector confidence and event risk score are separate concepts.
- Risk score is a deterministic operational-priority heuristic, not a calibrated probability of danger.
- Explain why each score was produced.
- Keep human operators responsible for decisions.
- Use authorized, minimal sample data and label synthetic/replayed events.
- Never fabricate test results or IBM integration.

## Official timing and rules
Use organizer announcements as the source of truth for the implementation window, allowed AI tools, reusable assets, model licenses, external APIs, deployment access and submission criteria. Preparation documents do not authorize prohibited pre-event coding.
