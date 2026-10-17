# SentinelAI — Computer Vision Engine (`cv-engine`)

**Role:** Lead 2 (Computer Vision & Event Producer)  
**Current Status:** Phase 5 Complete — Production-Ready Handover (v1.0.0)

---

## 1. Purpose of the CV Engine

The `cv-engine` is the visual processing subsystem of **SentinelAI**, an AI-based intelligent video analytics platform for border surveillance using existing CCTV infrastructure.

Its responsibilities within the SentinelAI architecture:
1. Ingest authorized CCTV video streams, prerecorded footage, or deterministic replay feeds.
2. Extract frame buffers and attach validated sequence and elapsed timing metadata.
3. Detect observable objects (specifically persons) using compatible pretrained detector models (YOLOv8n CPU) or deterministic replay adapters.
4. Evaluate detections against configured restricted spatial zones using pure Python Ray-Casting geometry.
5. Apply temporal confirmation (multi-frame debouncing) and cooldown deduplication.
6. Transmit structured, observable events conforming to `API_CONTRACT.md` to the backend API (`POST /api/events`).
7. Provide a zero-dependency deterministic replay fallback mode (`--replay`) for environments without model weights or camera hardware (such as IBM LinuxONE s390x testing).

> **Architectural Boundary:**  
> The Computer Vision engine only produces observable detections, spatial zone incursions, and detector statistical confidence (`confidence` ∈ `[0.0, 1.0]`). It **never** computes threat scores, intent probabilities, or risk levels. Risk scoring, risk levels, and explanation reasons are strictly owned and computed by the backend service.

---

## 2. Capabilities & Architecture Summary

The completed CV engine implements:
- **API Contract Compliance:** Structured `SecurityEvent` model strictly adhering to `API_CONTRACT.md` (`POST /api/events`), including required fields: `event_id`, `camera_id`, `event_type`, `timestamp`, `severity`, `confidence`, `zone_id`, `description`, `evidence`.
- **Occupancy & Zone-Entry Policy:** In the absence of a multi-object tracker, detections are frame-local (`evidence.track_id: null`). Events represent qualifying zone occupancy episodes rather than unverified identity tracks.
- **Temporal Confirmation (Debounce):** Configurable multi-frame persistence requirement (`temporal_confirmation_frames >= 1`) prevents false positive triggers caused by single-frame detector flutter.
- **Cooldown Deduplication:** Time-windowed cooldown (`deduplication_cooldown_sec`) suppresses redundant alerts while a subject remains continuously inside a restricted zone.
- **Deterministic Event Identifiers:** Generates stable, reproducible event IDs (`evt-{camera_id}-{zone_id}-{sha_suffix}`) derived from observation attributes via SHA-256 without relying on random UUIDs or Python's built-in `hash()`.
- **Resilient Backend Client:** Built on Python's standard library `urllib.request` (zero native C-dependencies), with explicit connection and read timeouts, bounded exponential backoff retries for transient 5xx errors, immediate rejection of 4xx client errors, and contract-compliant HTTP 409 idempotent duplicate handling.
- **Deterministic Replay Fallback Mode:** Pre-scripted synthetic video stream (`ReplayVideoSource`) and trajectory detector (`create_replay_detector`) allowing end-to-end simulation of video processing, incursion detection, and event emission without external video files, GPUs, or model downloads.
- **Comprehensive Automated Test Suite:** 121 passing automated unit and integration tests across all five phases with 0 failures and 0 errors.

---

## 3. Module Structure

```text
cv-engine/
├── .env.example              # Safe example environment variables
├── .gitignore                # Git ignore rules for Python, virtualenvs, models, data
├── requirements.txt          # Video processing & detection dependencies
├── README.md                 # Complete CV engine documentation
├── src/
│   └── sentinel_cv/
│       ├── __init__.py       # Package exports and version metadata (v1.0.0)
│       ├── __main__.py       # Executable module entry point
│       ├── backend_client.py # HTTP client with bounded retries & timeout controls
│       ├── cli.py            # CLI entry point (arguments, summaries, JSON output, --replay)
│       ├── config.py         # CVConfig dataclass with strict validation
│       ├── detector.py       # YOLOPersonDetector, MockPersonDetector, create_replay_detector
│       ├── event_generator.py# Temporal debouncing, cooldown, SecurityEvent builder
│       ├── interfaces.py     # IVideoSource, IDetector, IZoneAnalyzer, IEventGenerator, IBackendClient
│       ├── logging_config.py # Structured logging setup & namespaces
│       ├── models.py         # BoundingBox, Detection, FrameMetadata, SecurityEvent, PipelineResult
│       ├── pipeline.py       # CVPipeline streaming orchestrator
│       ├── video_source.py   # OpenCVVideoSource & ReplayVideoSource
│       └── zone.py           # PolygonZone, ZoneAnalyzer, ray-casting point-in-polygon
└── tests/
    ├── __init__.py
    ├── test_backend_client.py # HTTP client success, 4xx, 5xx, timeout, retry tests
    ├── test_cli.py           # CLI argument, JSON mode, and replay execution tests
    ├── test_config.py        # Config defaults, env loading, validation error tests
    ├── test_detector.py      # YOLO class filtering, confidence bounds, boundary tests
    ├── test_event_generator.py# Event schema, debounce, cooldown, deterministic ID tests
    ├── test_models.py        # Geometry, detection, metadata, security event tests
    ├── test_pipeline.py      # Streaming, replay mode, end-to-end integration tests
    ├── test_video_source.py  # OpenCV & ReplayVideoSource sequential reads, fallback FPS, EOF
    └── test_zone.py          # Polygon geometry, boundary tolerance, ray-casting, strategies
```

---

## 4. Video Source Usage

`OpenCVVideoSource` reads video files or camera streams:

```python
from sentinel_cv.video_source import OpenCVVideoSource

# Using context manager for automatic resource release
with OpenCVVideoSource("sample-data/demo.mp4", fallback_fps=25.0) as source:
    while source.is_opened():
        success, frame, metadata = source.read_frame()
        if not success or frame is None:
            break
        print(f"Frame #{metadata.frame_index} at {metadata.timestamp:.2f}s ({metadata.width}x{metadata.height})")
```

Key features:
- **Elapsed Video Time:** `metadata.timestamp` calculates `frame_index / fps` in seconds from the video container.
- **Safe Fallback FPS:** If the video container reports 0, negative, or NaN FPS, it falls back to `fallback_fps` (preventing division by zero).
- **Resource Cleanup:** Calls `.release()` on the underlying capture object upon exit.

---

## 5. Person Detector Configuration

`YOLOPersonDetector` loads pretrained YOLO weights (defaulting to `yolov8n.pt` on CPU) and strictly filters detections:

```python
from sentinel_cv.detector import YOLOPersonDetector
from sentinel_cv.models import FrameMetadata

detector = YOLOPersonDetector(
    model_name_or_path="yolov8n.pt",
    confidence_threshold=0.50,
    device="cpu",
)

# Run detection on a video frame
detections = detector.detect(frame, metadata)
for det in detections:
    print(f"Detected: {det.class_name} | Confidence: {det.confidence:.2f} | BBox: {det.bbox.as_dict()}")
```

- **Class Filtering:** Only detections where `class_name == "person"` (COCO class ID 0) are accepted. All other objects are discarded.
- **Coordinate Clamping:** Bounding box coordinates are clamped to `[0, width]` and `[0, height]` to avoid subpixel boundary errors.
- **Model Caching:** Model weights are loaded once upon initialization and reused across all subsequent frames.

---

## 6. Restricted-Zone Geometry & Spatial Analysis

Phase 3 introduces polygon-based restricted-zone spatial analysis via `PolygonZone` and `ZoneAnalyzer`:

```python
from sentinel_cv.models import BoundingBox, Detection
from sentinel_cv.zone import PolygonZone, ZoneAnalyzer

# 1. Define polygonal zone vertices (clock-wise or counter-clockwise)
zone = PolygonZone(
    zone_id="zone-perimeter-north",
    name="North Perimeter Buffer",
    vertices=[(100.0, 200.0), (500.0, 200.0), (500.0, 600.0), (100.0, 600.0)],
)

# 2. Initialize analyzer with Ground-Plane Anchor (bottom_center foot contact)
analyzer = ZoneAnalyzer(zones=[zone], reference_point_strategy="bottom_center")

# 3. Evaluate detected persons
detection = Detection(
    class_name="person",
    confidence=0.88,
    bbox=BoundingBox(x1=200.0, y1=300.0, x2=280.0, y2=550.0),
)
results = analyzer.evaluate([detection])

for res in results:
    print(f"Zone: {res.zone_id} | Incursion: {res.is_inside} | Foot Contact: {res.reference_point}")
```

### Key Geometric Algorithms & Principles:
- **Zero-Dependency Ray-Casting:** Point-in-polygon evaluation uses a pure Python Jordan curve / ray-casting algorithm. Points on boundary edges or vertices are explicitly included (`is_inside=True`) via collinear cross-product segment checking. Zero external native C-dependencies (no GEOS or Shapely required).
- **Ground-Plane Reference Point (Foot Contact Anchor):** The default strategy (`bottom_center`) evaluates `(x1 + w/2, y2)`. In CCTV surveillance, perspective distortion means a person standing outside a zone leaning over the border will have their torso or head inside the polygon, but their feet remain outside. Ground-plane analysis correctly identifies their true physical location and prevents false alerts.
- **Centroid Alternative:** An alternative `center` strategy `(x1 + w/2, y1 + h/2)` is available for aerial or top-down camera views.

---

---

## 7. Security Event Generation & API Contract Compliance

Phase 4 bridges visual analytics to the shared SentinelAI platform via `EventGenerator` and `SecurityEvent`:

```python
from sentinel_cv.event_generator import EventGenerator
from sentinel_cv.models import FrameMetadata

# Initialize generator with debouncing and cooldown policies
generator = EventGenerator(
    camera_id="cam-demo-01",
    severity="HIGH",
    temporal_confirmation_frames=2,   # Require 2 consecutive inside frames
    deduplication_cooldown_sec=5.0,    # Suppress duplicate alerts for 5.0 seconds
    base_timestamp="2026-10-17T09:30:00Z",
)

# Process zone evaluation results
events = generator.process_zone_results(zone_results, metadata)
for ev in events:
    print(f"Emitted: {ev.event_id} | Zone: {ev.zone_id} | Conf: {ev.confidence:.2f}")
```

### Event Contract Schema (`POST /api/events`):
```json
{
  "event_id": "evt-cam-demo-01-zone-restricted-01-a1b2c3d4",
  "camera_id": "cam-demo-01",
  "event_type": "RESTRICTED_ZONE_ENTRY",
  "timestamp": "2026-10-17T09:30:00Z",
  "severity": "HIGH",
  "confidence": 0.91,
  "zone_id": "zone-restricted-01",
  "description": "Observable person detected inside restricted zone 'North Perimeter' at ground-plane position (140.0, 450.0)",
  "evidence": {
    "class_name": "person",
    "track_id": null,
    "frame_number": 420,
    "bounding_box": {"x1": 100.0, "y1": 200.0, "x2": 180.0, "y2": 450.0},
    "reference_point": [140.0, 450.0],
    "zone_name": "North Perimeter",
    "elapsed_time_sec": 14.2,
    "consecutive_inside_frames": 2
  }
}
```

### Reliability & Policy Rules:
- **Occupancy vs. Tracking:** In the absence of a multi-object tracker, detections are frame-local. The policy evaluates zone occupancy rather than identity transitions. The evidence payload explicitly records `track_id: null` per contract.
- **Temporal Debounce:** Single-frame false detections are ignored until occupancy persists for `temporal_confirmation_frames`.
- **Cooldown Window:** Once emitted, redundant alerts for the same zone are suppressed for `deduplication_cooldown_sec` while continuous occupancy lasts.
- **Deterministic Event IDs:** `evt-{camera_id}-{zone_id}-{sha_suffix}` is computed deterministically from `camera_id`, `zone_id`, `frame_index`, elapsed time, and confidence. Reprocessing the same video stream produces the exact same event identifiers without relying on random UUIDs or Python `hash()`.
- **No Fabricated Risk Fields:** The CV engine never includes `risk_score`, `risk_level`, `reasons`, or `recommended_action`; those fields are calculated exclusively by the backend service.

---

## 8. Backend HTTP Client (`BackendClient`)

Transmits events to the backend service via `POST /api/events`:

```python
from sentinel_cv.backend_client import BackendClient

client = BackendClient(
    base_url="http://localhost:8000",
    timeout_seconds=5.0,
    max_retries=2,
    events_enabled=True,
)

# Check health
healthy, msg = client.check_health()

# Submit event
result = client.submit_event(event)
if result.success:
    print(f"Event submitted successfully (HTTP {result.status_code})")
```

### Key Reliability Controls:
- **Zero Third-Party Network Dependencies:** Built entirely with Python's standard library `urllib.request`. Zero native C-extensions or additional dependencies required.
- **Explicit Timeouts:** Configurable connection and read timeouts (`timeout_seconds=5.0`) prevent stalled workers.
- **Bounded Exponential Backoff Retries:** Automatically retries transient 5xx server errors and network drops up to `max_retries` with exponential backoff.
- **Client Error Non-Retry:** HTTP 4xx client errors (bad payload, rejected schema) are never retried.
- **Idempotency Handling:** HTTP 409 responses or acknowledged duplicates are handled gracefully as successful idempotent submissions (`idempotent_duplicate=True`).
- **Graceful Degradation:** Submission failures are logged with descriptive context and returned as `EventSubmissionResult` without crashing the video pipeline.

---

## 9. Command-Line Interface (CLI)

Run person detection, zone analysis, and backend event submission on local video feeds or deterministic replay streams:

```bash
# 1. Deterministic Replay Fallback Mode (CPU-friendly, no camera/model files needed)
python -m sentinel_cv --replay --disable-events --json

# 2. Basic run with local video file and frame limit
python -m sentinel_cv --video sample-data/synthetic_border_test.mp4 --max-frames 100

# 3. Run with custom model, confidence, and restricted zone
python -m sentinel_cv --video sample-data/synthetic_border_test.mp4 \
  --zone-id perimeter_buffer \
  --zone-vertices "[(100,200),(500,200),(500,600),(100,600)]" \
  --strategy bottom_center \
  --confidence 0.65 \
  --max-frames 50

# 4. Run with live backend submission and custom debouncing/cooldown
python -m sentinel_cv --video sample-data/synthetic_border_test.mp4 \
  --backend-url http://localhost:8000 \
  --severity HIGH \
  --debounce 2 \
  --cooldown 10.0

# 5. Output structured per-frame JSON stream for pipeline piping
python -m sentinel_cv --replay --per-frame-json
```

### Example Summary Output:
```text
========================================================
 SENTINELAI CV ENGINE — VIDEO & EVENT SUMMARY
========================================================
 Video Source:            sample-data/synthetic_border_test.mp4
 Camera ID:               cam-demo-01
 Monitored Zone ID:       perimeter_buffer
 Ground Contact Strategy: bottom_center
 Model Type:              yolo (yolov8n.pt)
 Confidence Threshold:    0.5
 Backend URL:             http://localhost:8000
 Events Enabled:          True
 Frames Processed:        100
 Total Person Detections: 42
 Total Zone Incursions:   18
 Total Events Emitted:    3
 Processing Time:         1.84s
 Average Processing FPS:  54.35 FPS
========================================================
```

---

## 10. Running Automated Tests

Run the complete test suite (126 tests) using Python's standard `unittest` runner:

```bash
# Windows PowerShell
$env:PYTHONPATH="src"; python -m unittest discover -v -s tests -p "test_*.py"

# Linux / macOS / IBM LinuxONE
PYTHONPATH=src python3 -m unittest discover -v -s tests -p "test_*.py"
```

All 126 unit and integration tests run deterministically, including genuine YOLO inference tests (`TestRealYOLOInference`) when `ultralytics` and weights are detected.

### Running End-to-End Tests with FastAPI Backend:
To run the cross-module end-to-end integration test suite connecting `sentinel_cv` with the FastAPI backend (covering both deterministic replay and real YOLO inference):

```bash
# Windows PowerShell from repo root
$env:PYTHONPATH="backend;cv-engine/src"; py -m pytest tests/test_e2e_cv_backend.py -v

# Linux / macOS from repo root
PYTHONPATH="backend:cv-engine/src" pytest tests/test_e2e_cv_backend.py -v
```

---

## 11. Performance and Resource Considerations

- **Streaming Generator:** `CVPipeline.process_stream()` yields frame results incrementally without holding video frames in RAM.
- **Bounding Box Caching:** `PolygonZone` caches its axis-aligned bounding box to perform $O(1)$ rejection before executing ray-casting checks.
- **Bounded Backoff:** Transient network failures back off exponentially without stalling the video ingestion thread indefinitely.
- **CPU Inference:** `yolov8n.pt` operates in CPU mode by default, consuming approximately 6.2 MB of model storage.
- **Progress Logging:** Logs progress every 50 frames rather than outputting log messages for every individual frame.
- **Clean Teardown:** Handles interrupts and EOF gracefully, closing video streams and freeing capture buffers.

---

## 12. IBM LinuxONE (`s390x`) Compatibility Status

- **Python Version Tested:** Python 3.14.2 (Windows x86-64 development environment).
- **OpenCV Version Tested:** OpenCV 5.0.0 (`cv2.VideoCapture`).
- **Detection Framework:** `ultralytics` 8.4.178 with PyTorch 2.14.1 (CPU mode).
- **Geometry & Spatial Analysis:** 100% pure Python standard library (`sentinel_cv.zone`). Zero native C-extensions required.
- **Event Generation & HTTP Client:** 100% pure Python standard library (`hashlib`, `datetime`, `urllib.request`). Zero third-party network libraries required.
- **Target Architecture Status (`s390x`):**
  - Pure Python components (`models.py`, `config.py`, `interfaces.py`, `pipeline.py`, `zone.py`, `event_generator.py`, `backend_client.py`, `MockPersonDetector`, `ReplayVideoSource`) are 100% architecture-neutral.
  - On `s390x` LinuxONE systems where PyTorch/Ultralytics wheels may not be pre-compiled, the engine provides:
    1. Deterministic replay mode (`python -m sentinel_cv --replay --json`) for zero-dependency end-to-end verification.
    2. Architecture fallback: Running the CV engine on an authorized workstation and streaming structured events over HTTP to the LinuxONE backend per `ARCHITECTURE.md`.

---

## 13. Roadmap & Phase Completion Status

- **Phase 1 (Complete):** CV Engine Foundation, Configuration, Models, Interfaces, Logging, Foundation Tests.
- **Phase 2 (Complete):** Video Ingestion & Person Detection Adapter (`OpenCVVideoSource`, `YOLOPersonDetector`, streaming pipeline, CLI, unit tests).
- **Phase 3 (Complete):** Configurable Restricted Zone & Person-vs-Zone Spatial Analysis (`PolygonZone`, Ray-Casting algorithm, ground-contact reference point, `ZoneAnalyzer`, unit/integration tests).
- **Phase 4 (Complete):** Event Generation & Backend Ingestion Client (`SecurityEvent` contract schema, temporal debouncing, cooldown deduplication, deterministic IDs, `BackendClient`, unit/integration tests).
- **Phase 5 (Complete):** Final Verification, Deterministic Replay Fallback Mode (`ReplayVideoSource`, `create_replay_detector`), Comprehensive 121-Test Suite, Handover Documentation.

---

## 14. Troubleshooting Common Failures

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| `[WinError 10061]` or connection refused | Backend server is not running on configured port. | Run with `--disable-events` for offline evaluation, or ensure backend is running (`uvicorn app:app --port 8000`). |
| `Video file does not exist` | Invalid path passed to `--video`. | Provide an authorized video file path or use `--replay` for synthetic replay evaluation. |
| `Invalid reference_point_strategy` | Typo in strategy argument. | Use either `bottom_center` (recommended ground-plane anchor) or `center`. |
| `ModelLoadingError: Ultralytics package is not installed` | Missing detection dependency in clean environment. | Run `pip install ultralytics` or pass `--model mock` / `--replay` to run without model dependencies. |
| `HTTP 409 Conflict` | Event ID already submitted to backend. | Expected idempotent behavior; the backend client logs this as an idempotent duplicate and continues without raising an error. |

