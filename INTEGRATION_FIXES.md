# Integration Audit Fixes

This update addresses verified frontend/backend integration messaging and health reporting.

## Changes
- The event ledger no longer labels HTTP 401/403 authorization responses as an offline backend.
- Unauthorized event requests now return an empty live-event result rather than silently displaying synthetic records as if they were real.
- Non-authentication event failures still permit fallback fixtures, but the response and UI label them as synthetic demonstration data.
- The global banner no longer claims the whole backend is offline merely because a live event feed is not verified.
- The System Health page no longer says the backend is undeployed when it can be reached, and it does not infer database health from the API heartbeat.
- The computer-vision bridge is explicitly labelled as pending independent verification.
- Default backend CORS origins now include localhost and loopback port 3001 for the Vite development server.

## Validation
- Python source compilation passed for all 51 backend Python files.
- The frontend build could not be independently re-run in this packaging environment because dependency installation was interrupted and TypeScript declaration packages were left incomplete. The repository's prior IBM LinuxONE audit reported a successful `tsc && vite build` before these edits. Re-run `npm ci && npm run build` in the target frontend directory to validate this exact revision.
- No secrets or `.env` files are included in this archive. Keep the target server's existing `backend/.env` private and unchanged.

## Important deployment note
A passing `/api/health` response verifies API liveness only. It does not prove that the database health probe, camera streams, CV inference, RTSP ingestion, or event generation are operational. Those should be enabled in the UI only after each integration is independently verified.
