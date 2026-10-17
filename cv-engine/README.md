# SentinelAI — Computer Vision Engine (`cv-engine`)

**Role:** Lead 2 (Computer Vision & Event Producer)  
**Current Status:** Phase 2 Complete (Video Ingestion & Person Detection)

---

## 1. Purpose of the CV Engine

The `cv-engine` is the visual processing subsystem of **SentinelAI**, an AI-based intelligent video analytics platform for border surveillance using existing CCTV infrastructure.

Its responsibilities within the SentinelAI architecture:
1. Ingest authorized CCTV video streams or prerecorded footage sequentially.
2. Extract frame buffers and attach validated sequence and elapsed timing metadata.
3. Detect observable objects (specifically persons) using compatible pretrained detector models.
4. Evaluate detections against configured restricted spatial zones (Phase 3).
5. Apply temporal confirmation (multi-frame debouncing) and cooldown deduplication (Phase 3).
6. Transmit structured, observable events conforming to `API_CONTRACT.md` to the backend API (Phase 4).

> **Architectural Boundary:**  
> The Computer Vision engine only produces observable detections and detector statistical confidence (`confidence` ∈ `[0.0, 1.0]`). It **never** computes threat scores, intent probabilities, or risk levels. Risk scoring and explanation reasons are strictly owned and computed by the backend service.

---

## 2. Phase 2 Capabilities & Current Status

Phase 2 builds upon the Phase 1 foundation by delivering operational video processing and person detection:
- **Video Ingestion:** `OpenCVVideoSource` implementing `IVideoSource`, with context manager support, safe fallback FPS handling (zero-division prevention), sequential frame indexing, and graceful EOF detection.
- **Incremental Streaming:** `CVPipeline.process_stream()` processes frames one by one without buffering full video sequences in memory.
- **Pretrained Person Detector:** `YOLOPersonDetector` using Ultralytics YOLO (default `yolov8n.pt` on CPU), strictly filtering for COCO class 0 (`person`) and discarding non-person classes (cars, animals, objects).
- **Testable Mock Detector:** `MockPersonDetector` enabling 100% deterministic, offline automated unit tests without downloading weights.
- **Command-Line Interface:** `python -m sentinel_cv` CLI for evaluating local video files, supporting `--max-frames`, `--confidence`, `--json`, and `--per-frame-json` outputs.
- **Comprehensive Automated Test Suite:** 68 passing unit tests covering video ingestion, frame metadata, YOLO filtering, boundary clamping, streaming, and CLI.

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
│       ├── __init__.py       # Package exports and version metadata (v0.2.0)
│       ├── __main__.py       # Executable module entry point
│       ├── cli.py            # CLI entry point (arguments, summaries, JSON output)
│       ├── config.py         # CVConfig dataclass with strict validation
│       ├── detector.py       # YOLOPersonDetector, MockPersonDetector, factory
│       ├── interfaces.py     # IVideoSource, IDetector, IZoneAnalyzer, ICVPipeline
│       ├── logging_config.py # Structured logging setup & namespaces
│       ├── models.py         # BoundingBox, Detection, FrameMetadata, PipelineResult
│       ├── pipeline.py       # CVPipeline streaming orchestrator
│       └── video_source.py   # OpenCVVideoSource with zero-division safe FPS
└── tests/
    ├── __init__.py
    ├── test_cli.py           # CLI argument and execution tests
    ├── test_config.py        # Config defaults, env loading, validation error tests
    ├── test_detector.py      # YOLO class filtering, confidence bounds, boundary tests
    ├── test_models.py        # BoundingBox, Detection, FrameMetadata geometry tests
    ├── test_pipeline.py      # Lifecycle, streaming, max_frames, exception tests
    └── test_video_source.py  # Sequential reads, fallback FPS, EOF, context manager
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

## 6. Command-Line Interface (CLI)

Run person detection on an authorized local video file:

```bash
# Basic run with frame limit
python -m sentinel_cv --video sample-data/demo.mp4 --max-frames 100

# Specify custom model and confidence threshold
python -m sentinel_cv --video sample-data/demo.mp4 --model yolov8n.pt --confidence 0.65

# Offline / Synthetic test mode without downloading model weights
python -m sentinel_cv --video sample-data/demo.mp4 --model mock --max-frames 50

# Output final summary as JSON
python -m sentinel_cv --video sample-data/demo.mp4 --max-frames 50 --json

# Output structured per-frame detections (for testing or piping)
python -m sentinel_cv --video sample-data/demo.mp4 --max-frames 10 --per-frame-json
```

### Example Summary Output:
```text
========================================================
 SENTINELAI CV ENGINE — VIDEO PROCESSING SUMMARY
========================================================
 Video Source:            sample-data/demo.mp4
 Camera ID:               cam-demo-01
 Model Type:              yolo (yolov8n.pt)
 Confidence Threshold:    0.5
 Frames Processed:        100
 Total Person Detections: 42
 Processing Time:         1.84s
 Average Processing FPS:  54.35 FPS
========================================================
```

---

## 7. Running Automated Tests

Run the complete test suite (68 tests) using Python's standard `unittest` runner:

```bash
# Windows PowerShell
$env:PYTHONPATH="src"; python -m unittest discover -v -s tests -p "test_*.py"

# Linux / macOS / IBM LinuxONE
PYTHONPATH=src python3 -m unittest discover -v -s tests -p "test_*.py"
```

All unit tests run deterministically without internet access, physical cameras, or external API endpoints.

---

## 8. Performance and Resource Considerations

- **Streaming Generator:** `CVPipeline.process_stream()` yields frame results incrementally without holding all video frames in RAM.
- **CPU Inference:** `yolov8n.pt` operates in CPU mode by default, consuming approximately 6.2 MB of model storage and maintaining low memory overhead.
- **Progress Logging:** Logs progress every 50 frames rather than outputting log messages for every individual frame.
- **Clean Teardown:** Handles interrupts and EOF gracefully, closing video streams and freeing capture buffers.

---

## 9. IBM LinuxONE (`s390x`) Compatibility Status

- **Python Version Tested:** Python 3.14.2 (Windows x86-64 development environment).
- **OpenCV Version Tested:** OpenCV 5.0.0 (`cv2.VideoCapture`).
- **Detection Framework:** `ultralytics` 8.4.178 with PyTorch 2.14.1 (CPU mode).
- **Target Architecture Status (`s390x`):**
  - Pure Python components (`models.py`, `config.py`, `interfaces.py`, `pipeline.py`, `MockPersonDetector`) are 100% architecture-neutral.
  - On `s390x` LinuxONE systems where PyTorch/Ultralytics wheels may not be pre-compiled, the engine provides:
    1. `MockPersonDetector` for offline verification and CI testing.
    2. Architecture fallback: Running the CV engine on an authorized workstation and streaming structured events over HTTP to the LinuxONE backend per `ARCHITECTURE.md`.

---

## 10. Planned Progression

- **Phase 1 (Complete):** CV Engine Foundation, Configuration, Models, Interfaces, Logging, Tests.
- **Phase 2 (Complete):** Video Ingestion & Person Detection Adapter (`OpenCVVideoSource`, `YOLOPersonDetector`, streaming pipeline, CLI, unit tests).
- **Phase 3:** Configurable Restricted Zone & Temporal Confirmation Logic (ground-contact point-in-polygon, multi-frame debounce, cooldown deduplication).
- **Phase 4:** Event Generation & Backend Ingestion Client (`API_CONTRACT.md` payload formatting, HTTP POST, error handling).
- **Phase 5:** End-to-End Integration, Replay Fallback, Benchmarking & Documentation.
