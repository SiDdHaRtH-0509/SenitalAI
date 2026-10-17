# Environment Setup and Compatibility

This document is intentionally architecture-aware. Verify actual organizer instructions before installing or deploying anything.

## 1. Inspect the environment
Run on the machine that will host each component:
```bash
uname -a
uname -m
python3 --version
node --version
npm --version
git --version
```
If containers are available:
```bash
docker --version
docker buildx version
podman --version
```
Commands may be unavailable depending on the provided environment. Record actual output. LinuxONE Linux systems commonly report `s390x`; local Windows laptops commonly use x86-64.

## 2. Python backend environment
Linux/macOS:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```
Windows PowerShell:
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```
If `requirements.txt` does not yet exist, the backend owner must create it; do not install a guessed package set.

## 3. Frontend environment
Check that the official Node.js distribution/package is supported on the target OS and architecture.
```bash
cd frontend
npm install
npm run dev
```
Use the exact Node version agreed by the team. If the target deployment needs a production build:
```bash
npm run build
```
The resulting static assets can be served by an approved web server if permitted. Do not assume the development server is suitable for production.

## 4. Computer vision environment
OpenCV and ML runtimes may have architecture-dependent wheels/native libraries. Test on the actual target before choosing the final deployment location.
```bash
cd cv-engine
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python video_processor.py --help
```
If the script or requirements do not yet exist, the CV owner creates them. Do not assume Ultralytics, PyTorch, ONNX Runtime, OpenCV GUI libraries, or model weights are available for every Python version/architecture.

## 5. Architecture-sensitive dependency audit
For every dependency, record:
- package and pinned version;
- whether a compatible `s390x` wheel/package exists;
- native libraries required;
- whether model inference was actually tested;
- license and model/data use restrictions;
- fallback if unsupported.

Practical options when inference is unsupported on LinuxONE:
1. Run CV inference on an approved compatible laptop or host, then send structured events to the LinuxONE-hosted API if allowed by network rules.
2. Use an approved inference runtime/model format that is verified on `s390x`.
3. Use a labelled deterministic replay fallback through the same event API.
Never claim fallback replay is live inference.

## 6. Environment variables
Copy `.env.example` to a local `.env` only if the app needs it. Never commit `.env`. Configure `VITE_API_BASE_URL` for the browser-visible backend address; `localhost` in a browser means the user's own machine, not a remote LinuxONE host.

## 7. Common issues
- `No matching distribution found`: check Python version, architecture, package pin and wheel availability.
- `Exec format error`: likely wrong architecture image/binary; inspect architecture and image manifest.
- Frontend cannot reach API: verify host, port, firewall, CORS, and that browser-facing URL is reachable.
- Model file missing: verify authorized download path and checksum; do not commit large weights without approval.
- Permission denied: use organizer-approved account and deployment method; do not attempt privilege escalation outside permission.
- Port already in use: choose an approved free port and update configuration consistently.
