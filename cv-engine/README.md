# SentinelAI — Computer Vision Engine (`cv-engine`)

**Role:** Lead 2 (Computer Vision & Event Producer)  
**Status:** Phase 1 Complete (CV Engine Foundation)

---

## 1. Purpose of the CV Engine

The `cv-engine` is the visual perception module of **SentinelAI**, an AI-based intelligent video analytics platform for border surveillance using existing CCTV infrastructure.

Its responsibilities within the SentinelAI pipeline:
1. Ingest authorized CCTV video streams or prerecorded footage.
2. Detect observable objects (specifically persons and vehicles) using compatible pretrained detector models.
3. Evaluate detections against configured restricted spatial zones (using bottom-center ground contact points).
4. Apply temporal confirmation (to suppress single-frame false positives) and cooldown deduplication.
5. Produce strictly structured, observable events conforming to `API_CONTRACT.md` and transmit them to the backend API via HTTP.

> **Important Architectural Boundary:**  
> The Computer Vision engine only produces observable facts and detector statistical confidence (`confidence` ∈ `[0.0, 1.0]`). It **never** computes threat scores, intent probabilities, or risk levels. Risk scoring and explanation reasons are strictly owned and computed by the backend service.

---

## 2. Current Phase 1 Status

Phase 1 establishes the **architectural foundation** for the CV engine:
- Modular project structure under `src/sentinel_cv/`.
- Strict, validated configuration module supporting environment variables and safe development defaults (`config.py`).
- Idempotent, structured logging configuration preventing sensitive data leaks (`logging_config.py`).
- Validated mathematical and domain data models (`models.py`) for `BoundingBox`, `Detection`, `FrameMetadata`, and `PipelineResult`.
- Extensible abstract component interfaces (`interfaces.py`) defining contracts for video sources, detectors, zone analyzers, and pipeline orchestrators.
- Foundational pipeline lifecycle orchestrator (`pipeline.py`).
- 100% pure-Python test suite with 41 passing automated unit tests (`tests/`).

---

## 3. Module Structure

```text
cv-engine/
├── .env.example              # Safe example environment variables
├── .gitignore                # Git ignore rules for Python, virtualenvs, models, data
├── requirements.txt          # Minimal Phase 1 dependencies
├── README.md                 # This documentation
├── src/
│   └── sentinel_cv/
│       ├── __init__.py       # Package exports and version metadata (v0.1.0)
│       ├── config.py         # CVConfig dataclass with strict validation
│       ├── logging_config.py # Structured logging setup & namespaces
│       ├── models.py         # BoundingBox, Detection, FrameMetadata, PipelineResult
│       ├── interfaces.py     # IVideoSource, IDetector, IZoneAnalyzer, ICVPipeline
│       └── pipeline.py       # CVPipeline lifecycle and frame orchestrator
└── tests/
    ├── __init__.py
    ├── test_config.py        # Config defaults, env loading, validation error tests
    ├── test_models.py        # BoundingBox, Detection, FrameMetadata geometry & boundary tests
    └── test_pipeline.py      # Lifecycle, mock component routing, and exception tests
```

---

## 4. Configuration Variables

Configuration can be set via environment variables (or `.env` locally) or passed directly to `CVConfig`:

| Variable | Type | Default | Description |
|---|---|---|---|
| `CV_INPUT_SOURCE_TYPE` | `string` | `file` | Input source type: `file`, `camera`, `stream`, or `replay`. |
| `CV_VIDEO_SOURCE` | `string` | `sample-data/demo.mp4` | Path to video file or camera index (e.g. `0`). |
| `CV_CAMERA_ID` | `string` | `cam-demo-01` | Camera identifier matching `API_CONTRACT.md`. |
| `CV_TARGET_WIDTH` | `int` | `1280` | Target processing frame width (> 0). |
| `CV_TARGET_HEIGHT` | `int` | `720` | Target processing frame height (> 0). |
| `CV_TARGET_FPS` | `float` | `10.0` | Target processing rate (> 0.0). |
| `CV_LOG_LEVEL` | `string` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). |
| `CV_MODEL_TYPE` | `string` | `placeholder` | Placeholder for Phase 2 detector type (e.g. `mobilenet`, `yolov8n`). |
| `CV_MODEL_PATH` | `string` | `None` | Path to model weights or ONNX file (Phase 2+). |
| `CV_CONFIDENCE_THRESHOLD` | `float` | `0.50` | Detection filter threshold (`0.0 <= threshold <= 1.0`). |
| `CV_ZONE_ID` | `string` | `zone-restricted-01` | Configured restricted zone ID (Phase 3+). |
| `CV_DEDUPLICATION_COOLDOWN_SEC` | `float` | `5.0` | Cooldown period between duplicate events (>= 0.0). |
| `CV_TEMPORAL_CONFIRMATION_FRAMES` | `int` | `3` | Required consecutive frames to confirm zone entry (>= 1). |
| `CV_REPLAY_MODE` | `bool` | `false` | Enable deterministic replay mode fallback. |
| `CV_BACKEND_URL` | `string` | `http://localhost:8000` | Target backend API base URL for event ingestion. |

---

## 5. Dependency Installation

Phase 1 relies strictly on the **Python Standard Library** (`dataclasses`, `typing`, `logging`, `math`, `os`, `abc`, `unittest`).

No heavy machine learning frameworks, native binaries, or GPU packages are required for Phase 1.

### Setup Virtual Environment
```bash
# Linux / macOS / IBM LinuxONE
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Windows PowerShell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

---

## 6. Running Automated Tests

Tests are written using Python's standard `unittest` framework and run deterministically without internet access, video hardware, or model files:

```bash
# From within cv-engine/ directory:
# Linux / macOS
PYTHONPATH=src python3 -m unittest discover -v -s tests -p "test_*.py"

# Windows PowerShell
$env:PYTHONPATH="src"; python -m unittest discover -v -s tests -p "test_*.py"
```

If `pytest` is installed in your development environment:
```bash
pytest -v
```

---

## 7. Data Models Usage

### `BoundingBox`
Represents an axis-aligned bounding box `(x1, y1, x2, y2)`:
```python
from sentinel_cv import BoundingBox

bbox = BoundingBox(x1=100.0, y1=150.0, x2=300.0, y2=450.0)
print(bbox.width)         # 200.0
print(bbox.height)        # 300.0
print(bbox.center)        # (200.0, 300.0)
print(bbox.bottom_center) # (200.0, 450.0) - used for CCTV ground contact zone entry
```
Validation ensures coordinates are finite non-negative numbers with `x2 > x1` and `y2 > y1`.

### `Detection`
Represents a detected object:
```python
from sentinel_cv import BoundingBox, Detection

bbox = BoundingBox(x1=100.0, y1=150.0, x2=300.0, y2=450.0)
det = Detection(class_name="person", confidence=0.89, bbox=bbox, track_id=12)
```
Validation enforces `0.0 <= confidence <= 1.0` and non-empty class names.

### `FrameMetadata`
Represents timing and frame sequencing:
```python
from sentinel_cv import FrameMetadata

meta = FrameMetadata(frame_index=42, timestamp=1.4, width=1920, height=1080, source_id="cam-demo-01")
```

### `PipelineResult`
Standardized container for per-frame pipeline results containing `metadata`, `detections`, `processed`, and `status_message`.

---

## 8. Pipeline Interface & Current Capabilities

`CVPipeline` provides:
- Lifecycle state tracking: `initialize()`, `process_frame()`, `run()`, `stop()`.
- Validates configuration and prepares logging on `initialize()`.
- Validates incoming `FrameMetadata` on `process_frame()`.
- If an `IDetector` is attached, routes frames to it and returns a populated `PipelineResult`.
- If no detector is attached (default Phase 1 state), returns an un-processed `PipelineResult` with 0 detections and an informative status message.
- If executed via `run()` without a video source, cleanly raises `NotImplementedError` indicating that video ingestion is scheduled for Phase 2.

---

## 9. Intentionally Deferred Items (Future Phases)

To maintain disciplined phase boundaries, the following are **not** implemented in Phase 1:
- **Video Decoding:** Actual OpenCV / FFmpeg video file reading is deferred to **Phase 2**.
- **Model Inference:** Person detection model loading and execution are deferred to **Phase 2**.
- **Zone Geometry & Point-in-Polygon:** Spatial zone intersection is deferred to **Phase 3**.
- **Temporal Confirmation & Cooldown:** Deduplication logic is deferred to **Phase 3**.
- **Backend HTTP Client:** Event generation and POST transmission are deferred to **Phase 4**.
- **Biometrics & Facial Recognition:** Strictly prohibited by project scope and ethical rules.

---

## 10. IBM LinuxONE (`s390x`) Compatibility Considerations

SentinelAI targets deployment on IBM LinuxONE / s390x environments.
- **Phase 1 Architecture Neutrality:** All Phase 1 code is 100% pure Python using only the standard library. It executes identically on `x86-64`, `aarch64`, and `s390x` without compiling any C-extensions.
- **Phase 2+ Considerations:** Many pre-compiled OpenCV and PyTorch binary wheels are not available for `s390x`. In Phase 2, the team will evaluate:
  1. Lightweight CPU inference runtimes (e.g., standard ONNX runtime or OpenCV DNN with s390x builds).
  2. Architecture fallback: Running CV inference on an approved workstation and streaming structured events over HTTP to the backend on LinuxONE.
  3. Labeled replay fallback for deterministic offline demonstration if hardware inference is unavailable.

---

## 11. Planned Progression

- **Phase 1 (Complete):** CV Engine Foundation, Configuration, Models, Interfaces, Logging, Tests.
- **Phase 2:** Video Ingestion & Person Detection Adapter (OpenCV reader, pretrained person detector, CPU-friendly fallback).
- **Phase 3:** Configurable Restricted Zone & Temporal Confirmation Logic (ground-contact point-in-polygon, multi-frame debounce, cooldown deduplication).
- **Phase 4:** Event Generation & Backend Ingestion Client (`API_CONTRACT.md` payload formatting, HTTP POST, error handling).
- **Phase 5:** End-to-End Integration, Replay Fallback, Benchmarking & Documentation.
