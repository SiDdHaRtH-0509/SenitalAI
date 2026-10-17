# Execution Plan — 24-Hour Official Build Window

Confirm exact start/end times with organizers. This plan assumes implementation begins only when permitted by the official rules.

## Phase 0 — Initial setup (hours 0–2)
- Overall Lead: verify rules, freeze contracts, start backend skeleton.
- Lead 1: start dashboard shell and API client shape.
- Lead 2: verify video/model feasibility and send a sample event.
- Lead 3: inspect target LinuxONE architecture/access and dependency risks.
- Lead 4: setup checklist, test plan, task board, sample-data permissions.

Exit gate: each person can run or test their component; event schema is frozen.

## Phase 1 — Core build (hours 2–6)
- Backend: health, create/list events, persistence, risk rules.
- Frontend: event list and risk detail using fixture data.
- CV: video reader, detector, zone configuration.
- LinuxONE: environment facts and package/image compatibility matrix.
- Support: verify setup steps, log blockers.

Exit gate: backend accepts a sample; frontend displays a fixture; CV reads video.

## Phase 2 — First integration (hours 6–10)
- CV posts a structured event to backend.
- Frontend polls and displays backend events.
- Validate timestamps, confidence, risk reasons and status.
- Start target deployment test if environment access is available.

Exit gate: one video event is visible in dashboard.

## Phase 3 — End-to-end MVP (hours 10–12)
- Fix schema/connection bugs only.
- Use labelled replay fallback if model inference is blocked.
- No optional feature expansion.

Exit gate: video/replay → event API → risk → dashboard works.

## Phase 4 — Reliability and target deployment (hours 12–18)
- Add duplicate suppression, error handling and tests.
- Verify SQLite persistence and restart behavior.
- Deploy the compatible services to LinuxONE if required/available.
- Document any component that must remain on another approved machine.

Exit gate: clean restart and reproducible demo.

## Phase 5 — Freeze and submission (hours 18–24)
- Freeze features.
- Run `INTEGRATION_TESTING.md`.
- Confirm LinuxONE evidence and accurate claims.
- Rehearse 90-second demo and backup.
- Check README, repository status, secrets, submission format.

## Contingencies
- Model unavailable on s390x: run approved inference on a compatible machine and send structured events to LinuxONE if permitted; otherwise labelled replay.
- Python/native dependency unsupported: remove optional dependency, use pure-Python/compatible alternative, or separate inference from API.
- Container image lacks s390x manifest: build from a compatible base if allowed or use organizer-provided runtime; never pull an x86-only image and assume it will run.
- Integration behind hour 10: freeze interfaces and use shared fixture; remove optional features.
- LinuxONE access fails: escalate to organizers immediately. If deployment is mandatory, prioritize access resolution; do not misrepresent local execution as LinuxONE deployment.
- Time overrun: one video, one zone, one event type, polling, SQLite, no optional acknowledgement unless already working.


## Lead-specific prompt workflow
Each lead starts with the relevant `leads/lead-N-*/PROMPT.md`. After completing a task, use that folder’s `NEXT_TASK_PROMPT.md` to ask the AI to inspect current files and generate the next bounded prompt. The AI must check task status and ownership before suggesting work; do not blindly execute generated prompts.
