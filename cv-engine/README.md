# SentinelAI — Computer Vision Engine (`cv-engine`)

**Role:** Lead 2 (Computer Vision & Event Producer)  
**Current Status:** Phase 3 Complete (Restricted-Zone Detection)

---

## 1. Purpose of the CV Engine

The `cv-engine` is the visual processing subsystem of **SentinelAI**, an AI-based intelligent video analytics platform for border surveillance using existing CCTV infrastructure.

Its responsibilities within the SentinelAI architecture:
1. Ingest authorized CCTV video streams or prerecorded footage sequentially.
2. Extract frame buffers and attach validated sequence and elapsed timing metadata.
3. Detect observable objects (specifically persons) using compatible pretrained detector models.
4. Evaluate detections against configured restricted spatial zones (Phase 3).
5. Apply temporal confirmation (multi-frame debouncing) and cooldown deduplication (Phase 4).
6. Transmit structured, observable events conforming to `API_CONTRACT.md` to the backend API (Phase 4).

> **Architectural Boundary:**  
> The Computer Vision engine only produces observable detections, spatial zone incursions, and detector statistical confidence (`confidence` ∈ `[0.0, 1.0]`). It **never** computes threat scores, intent probabilities, or risk levels. Risk scoring and explanation reasons are strictly owned and computed by the backend service.

---

## 2. Phase 3 Capabilities & Current Status

Phase 3 builds upon the Phase 1 and 2 foundation by delivering polygon-based restricted-zone spatial analysis:
- **Polygon Geometry Engine:** `PolygonZone` models arbitrary 2D polygonal security zones with strict vertex validation, Shoelace area computation, axis-aligned bounding box caching, and coordinate bounds checking.
- **Pure Python Point-in-Polygon:** Robust Ray-Casting algorithm implemented entirely in the Python standard library with zero native C-extension dependencies (no GEOS/Shapely required), guaranteeing 100% portability to IBM LinuxONE (`s390x`).
- **Boundary Tolerance:** Boundary and vertex contacts are explicitly classified as inside the zone (`is_inside=True`) via collinear cross-product segment checking.
- **Ground-Plane Reference Point (Foot-Contact Anchor):** Default reference point evaluates the bottom-center of the bounding box `(x1 + w/2, y2)` representing physical ground contact. Prevents false positive alerts when a subject stands outside the zone boundary but leans or gestures across it.
- **Zone Analyzer Adapter:** `ZoneAnalyzer` implementing `IZoneAnalyzer`, supporting multi-zone evaluation, zone enable/disable toggling, and configurable reference point strategies (`bottom_center`, `center`).
- **Pipeline Integration:** `CVPipeline` processes detections through `ZoneAnalyzer`, logging zone incursions and populating `zone_results` and `inside_zone_results` in `PipelineResult`.
- **Command-Line Interface:** `python -m sentinel_cv` CLI extended with `--zone-id`, `--zone-vertices`, `--zones-file`, and `--strategy` flags.
- **Comprehensive Automated Test Suite:** 88 passing unit and integration tests covering geometry, boundaries, concave polygons, ground-contact vs centroid reference points, streaming, and pipeline integration.

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
│       ├── __init__.py       # Package exports and version metadata (v0.3.0)
│       ├── __main__.py       # Executable module entry point
│       ├── cli.py            # CLI entry point (arguments, summaries, JSON output)
│       ├── config.py         # CVConfig dataclass with strict validation
│       ├── detector.py       # YOLOPersonDetector, MockPersonDetector, factory
│       ├── interfaces.py     # IVideoSource, IDetector, IZoneAnalyzer, ICVPipeline
│       ├── logging_config.py # Structured logging setup & namespaces
│       ├── models.py         # BoundingBox, Detection, FrameMetadata, ZoneAnalysisResult, PipelineResult
│       ├── pipeline.py       # CVPipeline streaming orchestrator
│       ├── video_source.py   # OpenCVVideoSource with zero-division safe FPS
│       └── zone.py           # PolygonZone, ZoneAnalyzer, ray-casting point-in-polygon
└── tests/
    ├── __init__.py
    ├── test_cli.py           # CLI argument and execution tests
    ├── test_config.py        # Config defaults, env loading, validation error tests
    ├── test_detector.py      # YOLO class filtering, confidence bounds, boundary tests
    ├── test_models.py        # BoundingBox, Detection, FrameMetadata geometry tests
    ├── test_pipeline.py      # Lifecycle, streaming, max_frames, zone integration tests
    ├── test_video_source.py  # Sequential reads, fallback FPS, EOF, context manager
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

## 7. Command-Line Interface (CLI)

Run person detection and zone analysis on an authorized local video file:

```bash
# Basic run with frame limit
python -m sentinel_cv --video sample-data/synthetic_border_test.mp4 --max-frames 100

# Specify custom model and confidence threshold
python -m sentinel_cv --video sample-data/synthetic_border_test.mp4 --model yolov8n.pt --confidence 0.65

# Configure restricted zone and ground-contact strategy
python -m sentinel_cv --video sample-data/synthetic_border_test.mp4 \
  --zone-id perimeter_buffer \
  --zone-vertices "[(100,200),(500,200),(500,600),(100,600)]" \
  --strategy bottom_center \
  --max-frames 50

# Offline / Synthetic test mode with JSON summary
python -m sentinel_cv --video sample-data/synthetic_border_test.mp4 --model mock --max-frames 30 --json

# Output structured per-frame detections and zone evaluations
python -m sentinel_cv --video sample-data/synthetic_border_test.mp4 --max-frames 10 --per-frame-json
```

### Example Summary Output:
```text
========================================================
 SENTINELAI CV ENGINE — VIDEO PROCESSING SUMMARY
========================================================
 Video Source:            sample-data/synthetic_border_test.mp4
 Camera ID:               cam-demo-01
 Zone ID:                 perimeter_buffer
 Strategy:                bottom_center
 Model Type:              yolo (yolov8n.pt)
 Confidence Threshold:    0.5
 Frames Processed:        100
 Total Person Detections: 42
 Total Zone Incursions:   18
 Processing Time:         1.84s
 Average Processing FPS:  54.35 FPS
========================================================
```

---

## 8. Running Automated Tests

Run the complete test suite (88 tests) using Python's standard `unittest` runner:

```bash
# Windows PowerShell
$env:PYTHONPATH="src"; python -m unittest discover -v -s tests -p "test_*.py"

# Linux / macOS / IBM LinuxONE
PYTHONPATH=src python3 -m unittest discover -v -s tests -p "test_*.py"
```

All unit tests run deterministically without internet access, physical cameras, or external API endpoints.

---

## 9. Performance and Resource Considerations

- **Streaming Generator:** `CVPipeline.process_stream()` yields frame results incrementally without holding all video frames in RAM.
- **Bounding Box Caching:** `PolygonZone` caches its axis-aligned bounding box to perform $O(1)$ rejection before executing ray-casting checks.
- **CPU Inference:** `yolov8n.pt` operates in CPU mode by default, consuming approximately 6.2 MB of model storage and maintaining low memory overhead.
- **Progress Logging:** Logs progress every 50 frames rather than outputting log messages for every individual frame.
- **Clean Teardown:** Handles interrupts and EOF gracefully, closing video streams and freeing capture buffers.

---

## 10. IBM LinuxONE (`s390x`) Compatibility Status

- **Python Version Tested:** Python 3.14.2 (Windows x86-64 development environment).
- **OpenCV Version Tested:** OpenCV 5.0.0 (`cv2.VideoCapture`).
- **Detection Framework:** `ultralytics` 8.4.178 with PyTorch 2.14.1 (CPU mode).
- **Geometry & Spatial Analysis:** 100% pure Python standard library (`sentinel_cv.zone`). Zero C-extensions (no GEOS, Shapely, or GDAL) required.
- **Target Architecture Status (`s390x`):**
  - Pure Python components (`models.py`, `config.py`, `interfaces.py`, `pipeline.py`, `zone.py`, `MockPersonDetector`) are 100% architecture-neutral.
  - On `s390x` LinuxONE systems where PyTorch/Ultralytics wheels may not be pre-compiled, the engine provides:
    1. `MockPersonDetector` for offline verification and CI testing.
    2. Architecture fallback: Running the CV engine on an authorized workstation and streaming structured events over HTTP to the LinuxONE backend per `ARCHITECTURE.md`.

---

## 11. Planned Progression

- **Phase 1 (Complete):** CV Engine Foundation, Configuration, Models, Interfaces, Logging, Tests.
- **Phase 2 (Complete):** Video Ingestion & Person Detection Adapter (`OpenCVVideoSource`, `YOLOPersonDetector`, streaming pipeline, CLI, unit tests).
- **Phase 3 (Complete):** Configurable Restricted Zone & Person-vs-Zone Spatial Analysis (`PolygonZone`, Ray-Casting algorithm, ground-contact reference point, `ZoneAnalyzer`, unit/integration tests).
- **Phase 4:** Event Generation & Backend Ingestion Client (temporal confirmation multi-frame debounce, cooldown deduplication, `API_CONTRACT.md` payload formatting, HTTP POST).
- **Phase 5:** End-to-End Integration, Replay Fallback, Benchmarking & Final Documentation.
