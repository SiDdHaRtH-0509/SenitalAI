# Lead 1 Checklist — Frontend

Work in order. Check boxes only after the criterion is met.

## Primary tasks
- [x] Read root project context, architecture and API contract. **Done when:** can explain the API fields and ownership boundaries.
- [x] Inspect current `frontend/` state and report existing files. **Done when:** no files are blindly overwritten.
- [x] Create/verify React + Vite app. **Done when:** `npm run dev` starts and page loads.
- [x] Create shared event types and one API service. **Done when:** requests and types follow `API_CONTRACT.md`.
- [x] Build dashboard shell and connection indicator. **Done when:** layout renders on the target browser.
- [x] Build event timeline/table. **Done when:** fixture events display timestamp, event type, severity and status.
- [x] Build risk detail panel. **Done when:** score, reasons and recommendation are read from event response.
- [x] Add video/replay panel. **Done when:** replay is clearly labelled and does not pretend to be live inference.
- [ ] Connect to `/api/events` and `/api/stats` where implemented. **Done when:** a backend event appears without manual page editing (Backend service implementation pending by Overall Lead).
- [x] Add loading, empty, disconnected, stale and error states. **Done when:** disconnecting backend does not crash the UI.
- [x] Configure API URL with `VITE_API_BASE_URL`. **Done when:** no deployment host is hardcoded.
- [x] Run build/lint/tests available in repo. **Done when:** results and failures are recorded honestly.
- [x] Commit and open PR. **Done when:** lead can review a small, scoped diff.

## Secondary tasks
- [x] Add accessible labels and readable severity styles.
- [x] Ensure small-screen layout remains usable if time permits.
- [ ] Add acknowledgement UI only if the backend endpoint is agreed and implemented.
- [ ] Capture screenshot of the actual working dashboard.

## Tertiary / optional (only after MVP)
- [ ] Add a small risk trend chart based on real stored events.
- [ ] Add WebSockets only if polling is stable and there is spare time.

## Completion criteria
Dashboard displays real backend events, shows explanations from backend, handles connection failures, labels replay data, and builds from documented instructions.
