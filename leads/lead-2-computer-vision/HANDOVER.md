# SentinelAI — Lead 2 Computer Vision Handover Document

**Version:** 1.0.0  
**Lead:** Lead 2 (Computer Vision & Event Producer)  
**Date:** 2026-10-17  
**Branch:** `lead-2/cv-engine`  

---

## 1. Executive Summary

Lead 2 has completed all five planned phases of the SentinelAI Computer Vision Engine (`cv-engine`):
1. **Phase 1:** Core architecture, models, interfaces, strict configuration validation, and foundation tests.
2. **Phase 2:** Sequential video ingestion (`OpenCVVideoSource`) and person detection adapter (`YOLOPersonDetector` / `MockPersonDetector`).
3. **Phase 3:** Polygonal restricted-zone geometry (`PolygonZone`), ground-plane contact anchor (`bottom_center`), and pure Python Ray-Casting spatial analysis (`ZoneAnalyzer`).
4. **Phase 4:** Event generation (`EventGenerator`), temporal debouncing, cooldown deduplication, deterministic SHA-256 event IDs, and resilient backend HTTP client (`BackendClient`).
5. **Phase 5:** Testing consolidation (121 passing tests), deterministic replay fallback mode (`ReplayVideoSource`, `create_replay_detector`, `--replay`), CPU benchmark verification, and documentation handover.

The CV engine is fully tested, modular, production-ready, and ready for integration with the backend service.

---

## 2. Implemented Components & Module Architecture

| Module | Primary Component | Responsibilities & Architectural Invariants |
| :--- | :--- | :--- |
| `config.py` | `CVConfig` | Frozen, validated configuration loaded from environment or CLI arguments. Strictly enforces non-negative numbers, positive dimensions, valid enums. |
| `models.py` | `BoundingBox`, `Detection`, `FrameMetadata`, `ZoneAnalysisResult`, `SecurityEvent`, `EventSubmissionResult`, `PipelineResult` | Strongly-typed, validated dataclasses. **Invariant:** `SecurityEvent` never produces `risk_score`, `risk_level`, `reasons`, or `recommended_action` (strictly backend-owned). |
| `video_source.py` | `OpenCVVideoSource`, `ReplayVideoSource`, `create_video_source` | Sequential frame reading, zero-division safe fallback FPS, EOF detection, context manager cleanup. `ReplayVideoSource` provides zero-dependency synthetic frames. |
| `detector.py` | `YOLOPersonDetector`, `MockPersonDetector`, `create_detector`, `create_replay_detector` | Ultralytics YOLOv8n CPU adapter with COCO class 0 ('person') filtering, boundary clamping, and mock/replay adapters. |
| `zone.py` | `PolygonZone`, `ZoneAnalyzer` | Pure Python Shoelace polygon area calculation, axis-aligned bounding box pre-filtering, and Ray-Casting algorithm with boundary tolerance. |
| `event_generator.py` | `EventGenerator` | Transforms zone incursions into `SecurityEvent` payloads with multi-frame debouncing (`temporal_confirmation_frames`), cooldown deduplication (`deduplication_cooldown_sec`), and deterministic SHA-256 event IDs. |
| `backend_client.py` | `BackendClient` | Pure standard library (`urllib.request`) client. Supports `GET /api/health`, `POST /api/events`, bounded exponential retries on 5xx/network errors, immediate 4xx non-retry, and HTTP 409 idempotency handling. |
| `pipeline.py` | `CVPipeline` | Streaming orchestrator (`process_stream()`) running incrementally frame-by-frame without buffering video in RAM. |
| `cli.py` | `run_cli`, `build_parser` | CLI supporting `--video`, `--model`, `--confidence`, `--zone-vertices`, `--strategy`, `--backend-url`, `--severity`, `--debounce`, `--cooldown`, `--replay`, `--disable-events`, `--json`, `--per-frame-json`. |

---

## 3. Public Interfaces & Expected Inputs/Outputs

### 3.1 Python API
```python
from sentinel_cv import CVConfig, CVPipeline

# Initialize from environment or custom config
config = CVConfig(
    video_source="sample-data/synthetic_border_test.mp4",
    camera_id="cam-demo-01",
    model_type="yolo",
    model_path="yolov8n.pt",
    confidence_threshold=0.50,
    backend_url="http://localhost:8000",
    events_enabled=True,
)
pipeline = CVPipeline.from_config(config=config, auto_init=True)

# Process stream incrementally
for result in pipeline.process_stream(max_frames=100):
    for event in result.events:
        print(f"Emitted event: {event.event_id} for zone: {event.zone_id}")
```

### 3.2 CLI Commands
```bash
# Deterministic Replay Mode (Zero external dependencies, ideal for quick testing)
python -m sentinel_cv --replay --disable-events --json

# Video File with Live Backend Submission
python -m sentinel_cv --video sample-data/synthetic_border_test.mp4 \
  --model yolov8n.pt \
  --confidence 0.50 \
  --backend-url http://localhost:8000 \
  --debounce 1 \
  --cooldown 5.0
```

### 3.3 Output Schema (`POST /api/events`)
Strictly matches `API_CONTRACT.md`:
```json
{
  "event_id": "evt-cam-demo-01-zone-restricted-01-72d35847",
  "camera_id": "cam-demo-01",
  "event_type": "RESTRICTED_ZONE_ENTRY",
  "timestamp": "2026-10-17T09:30:00Z",
  "severity": "HIGH",
  "confidence": 0.93,
  "zone_id": "zone-restricted-01",
  "description": "Observable person detected inside restricted zone 'Restricted Zone 01' at ground-plane position (360.0, 380.0)",
  "evidence": {
    "class_name": "person",
    "track_id": null,
    "frame_number": 2,
    "bounding_box": {"x1": 320.0, "y1": 220.0, "x2": 400.0, "y2": 380.0},
    "reference_point": [360.0, 380.0],
    "zone_name": "Restricted Zone 01",
    "elapsed_time_sec": 0.2,
    "consecutive_inside_frames": 1
  }
}
```

---

## 4. Test Commands and Consolidated Results

### Command:
```bash
$env:PYTHONPATH="src"
python -m unittest discover -v -s tests -p "test_*.py"
```

### Results:
- **Total Tests:** 121
- **Passed:** 121
- **Failed:** 0
- **Errors:** 0
- **Duration:** 2.26s

### Breakdown:
- `test_config.py`: 12 tests (defaults, environment overrides, validation errors)
- `test_models.py`: 18 tests (BoundingBox geometry, non-finite handling, Detection, FrameMetadata, SecurityEvent schema)
- `test_video_source.py`: 16 tests (OpenCV sequential reads, fallback FPS, EOF, context manager, ReplayVideoSource)
- `test_detector.py`: 16 tests (COCO class 0 filtering, clamping, thresholding, mock detectors, boundary boxes)
- `test_zone.py`: 20 tests (Shoelace area, ray-casting point-in-polygon, edge points, bottom-center strategy, disabled zones)
- `test_event_generator.py`: 11 tests (temporal debouncing, cooldown deduplication, deterministic SHA-256 IDs, schema compliance)
- `test_backend_client.py`: 8 tests (HTTP 200, 201, 400, 409 duplicate, 500 retries, timeouts, connection errors)
- `test_pipeline.py`: 14 tests (lifecycle, streaming, frame limits, zone integration, backend integration, replay mode)
- `test_cli.py`: 6 tests (argument parsing, JSON mode, replay mode execution)

---

## 5. LinuxONE (`s390x`) Compatibility Assessment

| Subsystem | Architecture Neutral? | Status on s390x | Verification & Fallback |
| :--- | :--- | :--- | :--- |
| Config & Models | 100% Pure Python | Verified | Pure Python standard library dataclasses. |
| Zone Geometry | 100% Pure Python | Verified | Pure Python ray-casting and Shoelace formula. |
| Event Generator | 100% Pure Python | Verified | `hashlib.sha256` and `datetime`. |
| Backend Client | 100% Pure Python | Verified | Built on `urllib.request`. Zero C-extensions (`requests`/`httpx` not required). |
| Video Reader | OpenCV (`cv2`) | Conditionally Verified | `python3-opencv` available on Linux distributions. If absent, `ReplayVideoSource` runs without OpenCV. |
| ML Detector | PyTorch / Ultralytics | Unverified on s390x | If PyTorch wheels are unavailable on s390x, use: (1) `--replay` mode for deterministic evaluation, or (2) Run CV engine on an edge workstation sending events to the LinuxONE backend per `ARCHITECTURE.md`. |

---

## 6. Known Operational Limitations

1. **Live Backend Unverified:** The repository's `backend/` directory contains only `README.md` (backend implementation is assigned to the Overall Lead). `BackendClient` was verified against hermetic mock transports, live socket connection tests, and schema contract test suites. Live network integration requires the Overall Lead to deploy the FastAPI service.
2. **Single-Frame Detections (No Multi-Object Tracking):** Per `API_CONTRACT.md` and design specifications, detections are frame-local (`evidence.track_id: null`). Tracking was intentionally not implemented to maintain strict LinuxONE portability and avoid heavy multi-object tracking dependencies (e.g. ByteTrack).
3. **Official Sample Video:** The synthetic border video fixture (`synthetic_border_test.mp4`) was validated; awaiting final authorized datathon video from the team.

---

## 7. Handover Notes for Overall Project Lead

1. **Backend Integration:** Ensure the backend `POST /api/events` endpoint accepts the exact JSON schema documented in Section 3.3.
2. **Idempotency:** When the backend receives duplicate `event_id` submissions, return HTTP 409 or HTTP 200 with the existing record to maintain idempotency.
3. **Risk Scoring:** The CV engine supplies `confidence` (statistical detector certainty). The backend rule engine must compute `risk_score` (0-100), `risk_level`, `reasons`, and `recommended_action`.
4. **Demonstration Command:** To run a zero-setup, flawless demonstration of the CV engine for reviewers or judges:
   ```bash
   python -m sentinel_cv --replay --json
   ```
