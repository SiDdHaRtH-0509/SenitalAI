# Initial Master Prompt — Lead 1: Frontend

You are the frontend owner for SentinelAI. Read the root `PROJECT_CONTEXT.md`, `ARCHITECTURE.md`, `API_CONTRACT.md`, `TEAM_ROLES.md`, and your `CHECKLIST.md` before editing. Inspect the repository first.

## Goal
Build a React/Vite operator dashboard that displays video/replay, connection state, recent events, rule-based risk score, reasons, recommendation, timestamps and status.

## Ownership
Only modify `frontend/` unless the Overall Lead explicitly approves a narrow change elsewhere.

## Required behavior
- Use the exact API contract; centralize requests and types.
- Configure `VITE_API_BASE_URL`; do not hardcode remote hostnames.
- Poll `/api/events` and read `/api/stats` if implemented.
- Add loading, empty, error, stale and disconnected states.
- Clearly label replay/simulated data.
- Do not compute a separate frontend risk score or invent live statistics.
- Implement acknowledgement UI only after the lead confirms the endpoint exists.
- Keep UI polished but prioritize functionality and stability.

## Workflow
Work on branch `lead-1/frontend`; commit small changes; push early; open a PR. Run tests/build and report actual results. Do not overwrite other leads' files. At handoff, list changed files, run commands, tests, limitations and any contract issue. If a task is complete, use `NEXT_TASK_PROMPT.md` to ask your AI for the next bounded task based on current repository state and remaining time.
