# IBM LinuxONE Deployment Guide

## Purpose
Deploy and verify the SentinelAI components on the actual IBM LinuxONE environment made available by the Datathon. This guide does not assume SSH, a particular cloud service, Kubernetes, Docker, Podman, a browser IDE, or a specific language runtime is available.

## Gate 1 — Confirm access and rules
Before deployment, obtain from the organizers:
- access method and host details;
- permitted runtime/container/build tools;
- allowed network ports and inbound access;
- approved image registry or package sources;
- whether all components or only a meaningful service must run on LinuxONE;
- how deployment evidence must be captured.

Do not put credentials in GitHub or paste them into public AI chats.

## Gate 2 — Inspect architecture
On the target host, if shell access is provided:
```bash
uname -m
cat /etc/os-release
python3 --version
node --version
```
Use available commands only. Expect `s390x` on many LinuxONE Linux environments, but verify instead of assuming.

## Gate 3 — Verify each dependency
Create a compatibility table in `docs/linuxone-compatibility.md`:
| Component | Version | Target architecture | Verified? | Fallback |
|---|---|---|---|---|
| Python backend | actual pinned version | actual output | yes/no | compatible runtime |
| SQLite driver | actual package | actual output | yes/no | supported system package |
| Node/frontend build | actual version | actual output | yes/no | build assets on compatible machine if allowed |
| OpenCV | actual version | actual output | yes/no | run inference elsewhere |
| ML runtime/model | actual version/format | actual output | yes/no | approved separate inference host or labelled replay |

Check wheels and native library support before installation. For containers, verify the image manifest supports `linux/s390x`; an `amd64`-only image will not run natively on s390x without an explicitly supported emulation setup, which should not be assumed.

## Deployment pattern
Preferred only if allowed and verified:
1. Run the video/CV producer on a machine where the chosen detector is supported.
2. Send structured event JSON over an approved network path to the backend hosted on LinuxONE.
3. Run the API, rule-based risk engine and event store on LinuxONE.
4. Serve the frontend from an approved reachable location and configure its API URL.
5. Restrict network exposure and use approved authentication/security controls if externally reachable.

If CV dependencies are verified on LinuxONE, the CV service may run there too. Do not force all components onto one machine if that makes the MVP unreliable or violates the environment's constraints.

## Deployment steps
1. Clone the official shared repository using the authorized method.
2. Check out the reviewed commit/tag.
3. Configure environment variables outside Git.
4. Install only the dependencies verified for the target architecture.
5. Start the backend with the approved process manager or organizer-provided runtime.
6. Build/serve the frontend using the approved method.
7. Start the CV producer on the selected supported host.
8. Run the health endpoint and end-to-end event test.
9. Record actual deployment evidence and commit hash.
10. Document any component not deployed.

Example backend command (only if Python/FastAPI/Uvicorn are available and approved):
```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Binding to `0.0.0.0` exposes the service on interfaces; use only when permitted and protect the service with the controls required by the environment.

## Verification
```bash
curl -fsS http://<approved-host>:8000/api/health
```
Then POST the sample event from `API_CONTRACT.md` using the approved endpoint. Confirm it appears in the dashboard. Replace placeholders with real authorized host/port values.

## Troubleshooting
- `Exec format error`: architecture mismatch; inspect executable/image architecture.
- package install failure: check s390x wheel support and Python version; choose verified alternatives.
- port inaccessible: confirm bind address, firewall, allowed ports and routing with organizers.
- frontend points to localhost: set the browser-facing API URL to the actual reachable host.
- model unavailable: separate inference from the backend if permitted or use labelled replay.
- deployment permission denied: contact the event administrator; do not bypass controls.

## Reporting
State clearly what ran on LinuxONE, what ran elsewhere, what was tested, and what remains proposed. Do not claim production readiness.
