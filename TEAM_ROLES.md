# Team Roles and File Ownership

There are five people total: the Overall Project Lead (you) plus Lead 1, Lead 2, Lead 3, and Lead 4.

## Overall Project Lead — architecture, backend and integration
Owns:
- `PROJECT_CONTEXT.md`, `ARCHITECTURE.md`, `API_CONTRACT.md`
- `backend/`
- merge approvals and release checkpoints
- integration testing coordination and final submission
- verification of actual IBM/competition requirements

Completion: API, storage and risk engine work; contract is stable; all modules integrated and tested; claims in submission match evidence.

## Lead 1 — Frontend
Owns:
- `frontend/`
- `leads/lead-1-frontend/`

Completion: dashboard consumes real API data; loading/error/empty states work; no independent risk calculations or fake live metrics.

## Lead 2 — Computer Vision
Owns:
- `cv-engine/`
- `leads/lead-2-computer-vision/`

Completion: sample video produces valid zone-entry events via the shared API; cooldown/deduplication and fallback documented.

## Lead 3 — LinuxONE / Environment / Deployment
Owns:
- `deploy/` (create only when needed)
- `ENVIRONMENT_SETUP.md`, `LINUXONE_DEPLOYMENT.md`, compatibility notes
- `leads/lead-3-linuxone/`

Completion: actual environment/architecture verified; chosen components checked on target; deployment steps and evidence recorded; no false claim of deployment.

## Lead 4 — Support / QA / Demo
Owns:
- `leads/lead-4-support/`
- QA checklists, task board updates, demo script/recording, setup verification and documentation review.
- May create isolated test fixtures/utilities only with owner approval.

Completion: clean setup checked, test results accurately recorded, demo rehearsed and backup ready. Lead 4 does not own a critical runtime dependency.

## Git rules

- Repository: `sentinel-ai`; default branch: `main`.
- Branch naming: `lead-1/frontend`, `lead-2/cv-engine`, `lead-3/linuxone`, `lead-4/support`; Overall Project Lead uses `lead/backend-integration`.
- Branches: `lead/backend-integration`, `lead-1/frontend`, `lead-2/cv-engine`, `lead-3/linuxone`, `lead-4/support`.
- Never work directly on `main` during parallel development.
- One module owner per folder; ask before editing another person's module.
- Small commits with clear messages; push early; open PRs.
- Overall Lead reviews integration and contract changes.
- If a conflict occurs, stop and coordinate; do not blindly accept “ours/theirs” or let an AI overwrite both versions.
