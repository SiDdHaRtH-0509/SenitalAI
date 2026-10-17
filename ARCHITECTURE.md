# SentinelAI Architecture

## High-level flow
```text
Authorized CCTV-style video
          |
          v
OpenCV reader + existing detector
          |
          v
Zone intersection + temporal confirmation
          |
          v
Structured event producer
          | HTTP JSON
          v
FastAPI event API (Overall Lead)
          |
          +--> validation + idempotency
          +--> deterministic risk rules
          +--> SQLite event history
          |
          v
React/Vite dashboard (Lead 1)
          |
          v
Human review / acknowledgement
```

LinuxONE is a deployment target, not an assumed dependency for every component. Depending on the actual environment, the backend/API or other compatible services may run on LinuxONE while video inference runs on an approved developer machine. Document the real deployment and data flow.

## Ownership and boundaries
- `backend/`: Overall Lead only. API schemas, risk engine, storage, backend tests.
- `frontend/`: Lead 1 only. Dashboard, API client, frontend types/components.
- `cv-engine/`: Lead 2 only. Video reader, detector adapter, zone logic, event producer.
- `deploy/` and deployment docs: Lead 3. Environment inspection, deployment scripts/configuration, architecture-specific compatibility notes. Do not duplicate application logic.
- `leads/lead-4-support/`, root docs and test coordination: Lead 4 maintains support materials; owners retain responsibility for code in their modules.
- Overall Lead approves contract changes and merges PRs.

## Required design choices
- One video and one zone first.
- HTTP POST for event ingestion; polling for dashboard refresh.
- SQLite for the small prototype unless LinuxONE environment constraints require a documented alternative.
- Existing pretrained detector only; no custom training.
- Human-in-the-loop response.
- Replay fallback must be labelled.

## LinuxONE compatibility
Check the actual machine architecture with `uname -m`; LinuxONE systems commonly report `s390x`. Native dependencies and ML runtime availability may differ from x86-64. See `ENVIRONMENT_SETUP.md`. Do not promise that a chosen model/runtime will work until tested on the actual environment.

## Failure strategy
- Detector fails: use a clearly labelled deterministic replay through the same API.
- Model package unavailable on s390x: run approved inference on a compatible separate machine and send only structured events to the LinuxONE service, if network access and competition rules allow.
- Frontend/backend integration late: use the shared JSON fixture and API contract, cut optional UI features.
- Deployment unavailable: preserve a reproducible local demo and accurately report the IBM component as proposed/not deployed, unless official rules require actual deployment—in that case escalate immediately to organizers.
