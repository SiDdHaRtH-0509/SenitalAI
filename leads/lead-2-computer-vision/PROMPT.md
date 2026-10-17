# Initial Master Prompt — Lead 2: Computer Vision

Read root `PROJECT_CONTEXT.md`, `ARCHITECTURE.md`, `API_CONTRACT.md`, `TEAM_ROLES.md`, and your `CHECKLIST.md`. Inspect existing files before editing.

## Goal
Read one authorized CCTV-style video, run a compatible existing pretrained person detector, detect entry into one configured zone, and POST a structured event to the backend.

## Ownership
Only modify `cv-engine/` unless the Overall Lead approves a narrow change.

## Required behavior
- OpenCV video reader and a detector adapter.
- One configurable zone and documented point-in-zone logic.
- Temporal confirmation to avoid one-frame triggers.
- Cooldown/deduplication for continuous presence.
- Unique event ID, timezone-aware timestamp, detector confidence.
- Exact payload from `API_CONTRACT.md`; backend owns risk scoring.
- Clear errors for missing model, invalid video and API outage.
- CPU-friendly fallback and explicitly labelled replay mode.
- No facial recognition, identity inference or threat-intent claims.

Check package/model compatibility in the actual environment. Do not assume ML runtimes work on s390x. Integrate with the backend early. Work on `lead-2/cv-engine`, commit small changes, test and open a PR. Report commands and actual results. Use `NEXT_TASK_PROMPT.md` after each completed task to request the next bounded prompt from your AI.
