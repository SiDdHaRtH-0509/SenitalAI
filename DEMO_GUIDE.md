# SentinelAI — Live Demonstration Guide

A concise, step-by-step operator guide for presenting the SentinelAI intelligent video analytics platform live to evaluators and stakeholders.

---

## 1. Quick Startup (3 Terminals)

### Terminal 1: FastAPI Backend
```bash
cd backend
python -m pip install -r requirements.txt
py -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
- **Expected Output:**
  ```text
  INFO:     Started server process [PID]
  INFO:     Application startup complete.
  INFO:     Uvicorn running on http://127.0.0.1:8000
  ```

### Terminal 2: React Command Dashboard
```bash
cd frontend
npm install
npm run dev
```
- **Browser URL:** Open [http://localhost:3000](http://localhost:3000)
- **Expected Output:** Vite server ready in ~1s; application loads with `CONNECTED` green pill in the top header bar.

### Terminal 3: Computer Vision Inference Engine (Real YOLOv8n)
```bash
cd cv-engine
$env:PYTHONPATH="src"
py -m sentinel_cv --video sample-data/real_person_stream.mp4 --model yolov8n.pt --camera-id cam-north-01 --zone-id zone-restricted-01 --backend-url http://127.0.0.1:8000 --max-frames 5 --json
```
- **Expected Output:**
  ```json
  {
    "status": "success",
    "replay_mode": false,
    "model_type": "yolo",
    "model_path": "yolov8n.pt",
    "frames_processed": 5,
    "total_person_detections": 19,
    "total_zone_incursions": 5,
    "total_events_emitted": 1,
    "average_fps": 2.49
  }
  ```

---

## 2. 90-Second Demonstration Script

### Act 1: The Command Center (0–20s)
1. Point to the **Top Header Bar**: Show the green `CONNECTED` status badge connecting to `http://127.0.0.1:8000`.
2. Point to the **KPI Cards**: Note real-time aggregates retrieved from SQLite via `GET /api/stats` (Total Events, Active Cameras, Zone Alerts).
3. Navigate to **Camera Registry (`#/cameras`)** and **Restricted Zones (`#/zones`)**: Show calibrated boundary polygons evaluated by the ray-casting algorithm.

### Act 2: Real Computer Vision Inference (20–50s)
1. Run the command in **Terminal 3**.
2. Explain what is happening:
   - YOLOv8n runs neural network inference on CPU over `real_person_stream.mp4`.
   - COCO class 0 (`"person"`) is filtered with a strict `0.50` confidence threshold.
   - Non-incursion persons are discarded; the person crossing into `zone-restricted-01` (`foot coordinate (449.09, 572.15)`) creates `evt-cam-north-01-zone-restricted-01-e7a264df`.
   - The structured event is dispatched over HTTP `POST /api/events` to FastAPI.

### Act 3: Live Incident Arrival & Evidence Inspection (50–70s)
1. Switch to the **Browser**: The new incident arrives via polling within the configured refresh window without a full page reload.
2. Click on `evt-cam-north-01-zone-restricted-01-e7a264df` in the **Recent Events Table**.
3. In the **Event Detail Modal**, highlight:
   - **Detection Confidence:** `74.3% (YOLOv8n Class 0)`
   - **Assessed Risk Priority:** Score `75/100`, Level `HIGH`
   - **Bounding Box:** `[352.98, 267.83, 545.19, 572.15]`
   - **Ground-Plane Reference Point:** `[449.09, 572.15]`
   - **Deterministic Explanations:**
     - *Base severity set to HIGH (60 pts)*
     - *Restricted-zone boundary breached (zone-restricted-01) (+10 pts)*
     - *Moderate detector certainty (0.74) (+5 pts)*
   - **Recommended Action:** *"Request human verification and alert nearest patrol unit"*

### Act 4: Human-in-the-Loop Triage & Persistence (70–90s)
1. Click **"Acknowledge Incident"** or **"Mark Resolved"**.
2. Notice the instant status update to `ACKNOWLEDGED` or `RESOLVED` backed by `PATCH /api/events/{id}/status`.
3. Press **F5 (Reload)** in the browser: Show that the status survives page reloads because it was persisted in SQLite.

---

## 3. Disconnection & Recovery Demonstration

To demonstrate graceful failure and honest offline labeling:
1. **Stop Backend:** Press `Ctrl+C` in Terminal 1.
2. **Observe UI:**
   - The header connection indicator transitions to `DISCONNECTED` / `INTEGRATION_PENDING`.
   - The Recent Events table displays calibrated demonstration fixtures with an explicit warning banner: `EXPLICIT DEMO DATA`. Zero fake live data is shown.
3. **Restart Backend:** Re-run the command in Terminal 1.
4. **Observe Recovery:** The frontend auto-recovers to `CONNECTED` and resumes live telemetry without crashing.

---

## 4. Fallback Plan (Fast Deterministic Replay)

If CPU inference is slow or PyTorch is unavailable in a constrained environment (e.g., LinuxONE `s390x`):
```bash
cd cv-engine
$env:PYTHONPATH="src"
py -m sentinel_cv --replay --backend-url http://127.0.0.1:8000 --json
```
- **Key Advantages:**
  - Zero external neural weights or PyTorch required (pure Python standard library geometry).
  - Emits pre-scripted ground-truth incursion `evt-cam-north-01-zone-restricted-01-ac0aebae`.
  - Executes in `<0.1s`.
  - Clearly tagged in logs and terminal as `replay_mode: true`.

---

## 5. Troubleshooting Reference

| Symptom | Probable Cause | Immediate Remediation |
| :--- | :--- | :--- |
| **Port 8000 in use** | Stray background Uvicorn process | Run `Get-NetTCPConnection -LocalPort 8000 \| % { Stop-Process -Id $_.OwningProcess -Force }` |
| **Port 3000 in use** | Vite server already running | Vite auto-selects port 5173 or next free port; check terminal log for exact port |
| **`No module named sentinel_cv`** | `PYTHONPATH` not pointing to `src` | Run `$env:PYTHONPATH="src"` (PowerShell) or `export PYTHONPATH=src` (Bash) |
| **Video open error** | Missing sample video file | Confirm `cv-engine/sample-data/real_person_stream.mp4` exists (size: ~202 KB) |
| **Network Refusal in Frontend** | Backend not running on `127.0.0.1:8000` | Start Terminal 1 Uvicorn server before opening dashboard |
| **CORS error in browser console** | Custom port used without updating config | Ensure frontend runs on port 3000 or 5173 (both allowed by default CORS) |
