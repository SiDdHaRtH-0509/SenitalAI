# SentinelAI Example Surveillance Video Suite for Judges

This directory contains a lightweight collection of three verified example surveillance video clips designed specifically for **IBM Datathon judges, reviewers, and evaluators** to demonstrate and test SentinelAI's end-to-end computer vision and intelligent video analytics pipeline.

All clips are encoded in standard **H.264 / MP4** (`yuv420p`, `+faststart`), ensuring native playback in modern web browsers, desktop media players, and direct OpenCV ingestion without external codecs or Git LFS dependencies. The combined size of all three videos is **~3.27 MB**, keeping the repository footprint minimal.

---

## Video Catalog & Evaluation Scenarios

| File | Scenario | Duration | Resolution | FPS | Size | Expected Observation |
|---|---|---|---|---|---|---|
| `normal_patrol.mp4` | Normal Open-Area Patrol | 15.0s (150 frames) | 768x576 | 10.0 | 1.05 MB | Continuous person detection, **0 zone incursions**, 0 false alerts. |
| `restricted_zone_entry.mp4` | Restricted Zone Incursion | 15.0s (150 frames) | 768x576 | 10.0 | 1.12 MB | Person breaches corridor polygon; **generates security events (HTTP 201)** with risk scoring. |
| `multiple_people.mp4` | High-Density Multi-Target | 15.0s (150 frames) | 768x576 | 10.0 | 1.09 MB | Multi-person detection (**peak 9 simultaneous persons**), 1,000+ person bounding boxes. |

---

## Provenance and Redistribution Licensing

- **Source:** Extracted from the standard surveillance benchmark dataset `vtest.avi` maintained by the OpenCV Foundation.
- **Upstream Repository:** [opencv/opencv](https://github.com/opencv/opencv/tree/master/samples/data)
- **License:** **Apache License 2.0 / 3-Clause BSD License** (OpenCV Foundation).
- **Redistribution Rights:** Publicly licensed for open-source distribution, benchmarking, academic research, and datathon evaluation.
- **Privacy & Compliance:** Contains public surveillance benchmark footage in an open pedestrian plaza with no private, confidential, or sensitive personal data.

---

## Quick-Start Commands for Judges

Ensure the SentinelAI backend is running (optional if testing with `--disable-events`):
```bash
# In backend/ terminal:
py -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Scenario 1: Normal Patrol (Baseline Verification — Zero Incursions)
Evaluates normal pedestrian movement across an open surveillance scene against a neutral off-path buffer zone `[(0, 0), (100, 0), (100, 100), (0, 100)]`.
Verifies that people are detected with high confidence without triggering false perimeter alarms.

**PowerShell (Windows):**
```powershell
cd cv-engine
$env:PYTHONPATH="src"
py -m sentinel_cv --video sample-data/examples/normal_patrol.mp4 --model yolov8n.pt --camera-id cam-patrol-01 --zone-id zone-neutral --zone-vertices "[(0,0),(100,0),(100,100),(0,100)]" --backend-url http://127.0.0.1:8000 --json
```

**Bash (Linux / macOS):**
```bash
cd cv-engine
PYTHONPATH=src python3 -m sentinel_cv --video sample-data/examples/normal_patrol.mp4 --model yolov8n.pt --camera-id cam-patrol-01 --zone-id zone-neutral --zone-vertices "[(0,0),(100,0),(100,100),(0,100)]" --backend-url http://127.0.0.1:8000 --json
```

**Expected Results:**
- `total_person_detections`: ~850+ detections across 150 frames.
- `total_zone_incursions`: `0`.
- `total_events_emitted`: `0`.

---

### Scenario 2: Restricted Zone Entry (Active Incursion & Alert Generation)
Evaluates an individual entering the monitored eastern corridor polygon `[(550, 200), (768, 200), (768, 450), (550, 450)]`.
Verifies ground-plane foot contact ray-casting, event generation, temporal debouncing, deduplication cooldown, and authenticated HTTP submission to the FastAPI backend.

**PowerShell (Windows):**
```powershell
cd cv-engine
$env:PYTHONPATH="src"
py -m sentinel_cv --video sample-data/examples/restricted_zone_entry.mp4 --model yolov8n.pt --camera-id cam-perimeter-02 --zone-id zone-corridor-east --zone-vertices "[(550,200),(768,200),(768,450),(550,450)]" --backend-url http://127.0.0.1:8000 --json
```

**Bash (Linux / macOS):**
```bash
cd cv-engine
PYTHONPATH=src python3 -m sentinel_cv --video sample-data/examples/restricted_zone_entry.mp4 --model yolov8n.pt --camera-id cam-perimeter-02 --zone-id zone-corridor-east --zone-vertices "[(550,200),(768,200),(768,450),(550,450)]" --backend-url http://127.0.0.1:8000 --json
```

**Expected Results:**
- `total_person_detections`: ~800+ detections.
- `total_zone_incursions`: ~250+ incursion frames detected.
- `total_events_emitted`: 1–3 security events (depending on configured temporal confirmation and deduplication cooldown).
- Backend logs show `POST /api/events` returning `HTTP 201 Created` with SHA-256 audit-chain integrity record.

---

### Scenario 3: High-Density Crowd (Multi-Target Detection & Throughput)
Evaluates simultaneous multi-person tracking under crowded conditions (6 to 10 persons simultaneously visible).
Demonstrates detector throughput, bounding box precision, and tracking stability under heavy traffic.

**PowerShell (Windows):**
```powershell
cd cv-engine
$env:PYTHONPATH="src"
py -m sentinel_cv --video sample-data/examples/multiple_people.mp4 --model yolov8n.pt --camera-id cam-plaza-03 --zone-id zone-neutral --zone-vertices "[(0,0),(50,0),(50,50),(0,50)]" --backend-url http://127.0.0.1:8000 --disable-events --json
```

**Bash (Linux / macOS):**
```bash
cd cv-engine
PYTHONPATH=src python3 -m sentinel_cv --video sample-data/examples/multiple_people.mp4 --model yolov8n.pt --camera-id cam-plaza-03 --zone-id zone-neutral --zone-vertices "[(0,0),(50,0),(50,50),(0,50)]" --backend-url http://127.0.0.1:8000 --disable-events --json
```

**Expected Results:**
- `total_person_detections`: Over 1,000+ bounding boxes.
- Peak simultaneous individuals: 9 persons in a single frame.
- Smooth video decode and inference throughput.

---

## What Judges Should Look For

1. **Console Telemetry & Summary:**
   - Review the final JSON output: `frames_processed`, `total_person_detections`, `total_zone_incursions`, `total_events_emitted`, and `average_fps`.
2. **Backend Event Verification:**
   - Query `http://127.0.0.1:8000/api/events` or inspect the API docs at `http://127.0.0.1:8000/docs` to verify that submitted events contain:
     - `camera_id` and `zone_id` matching CLI parameters.
     - Computed `risk_score` (0.0 to 1.0) and backend triage severity.
     - Cryptographic SHA-256 audit log hash chain entry in `audit_logs`.
3. **Frontend Dashboard Visualization:**
   - Open `http://localhost:3000` in your browser.
   - Observe live event feeds, high-risk alert counters, and camera worker status updating in real-time.

---

## Technical Considerations & Operational Limits

- **Foot Contact Approximation:** In 2D video analytics, restricted zone evaluation utilizes the `bottom_center` reference point strategy, approximating where the person's feet contact the ground plane. This prevents false alarms when a person's upper torso or head occludes a zone while standing outside it.
- **Lighting and Environmental Conditions:** The benchmark clips represent standard daylight CCTV surveillance. For night operations or adverse weather, thermal or infrared cameras with model fine-tuning are recommended in operational deployment.
- **Hardware Agnostic:** In environments without GPU acceleration or native PyTorch support (e.g., IBM LinuxONE s390x nodes), SentinelAI provides the deterministic `--replay` mode (`py -m sentinel_cv --replay --json`) which executes the complete event pipeline without PyTorch dependencies.
