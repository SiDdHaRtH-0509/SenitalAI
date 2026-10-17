# Lead 2 — Computer Vision

## Responsibilities
Own video input, detector integration, zone logic and structured event production. Backend owns risk scoring; do not change the API schema independently.

## Assigned files
- `cv-engine/`
- This folder's prompt/checklist/next-task instructions.

## Dependencies
- `API_CONTRACT.md`
- Authorized sample video
- Backend endpoint from Overall Lead

## Deliverables
- Runnable video processor.
- Zone configuration and cooldown.
- HTTP event client.
- Requirements and run instructions.
- Test log and fallback procedure.
- PR on `lead-2/cv-engine`.

## Done when
A sample video produces an event accepted by the backend, or a clearly labelled replay fallback uses the same event contract if model runtime is blocked.

## Current Progress
- **Phase 1 (CV Engine Foundation):** Completed. Established modular structure in `cv-engine/`, configuration with strict validation, structured logging, validated data models (`BoundingBox`, `Detection`, `FrameMetadata`, `PipelineResult`), component interfaces (`IVideoSource`, `IDetector`, `IZoneAnalyzer`, `ICVPipeline`), pipeline orchestrator, and 41 passing automated tests.
- **Phase 2 (Video Ingestion & Detection Adapter):** Completed. Implemented `OpenCVVideoSource` with safe fallback FPS and EOF detection, `YOLOPersonDetector` with strict COCO person class filtering and bounding box clamping, `MockPersonDetector` for offline testing, streaming generator `process_stream()`, `python -m sentinel_cv` CLI, and 68 passing automated unit tests.
- **Phase 3 (Restricted-Zone Detection):** Completed. Implemented `PolygonZone` with Shoelace area calculation and axis-aligned bbox caching, pure Python Ray-Casting algorithm with boundary tolerance, ground-plane foot-contact reference point strategy (`bottom_center`), `ZoneAnalyzer` adapter, pipeline integration with incursion logging, CLI zone parameters, and 88 passing automated tests.
- **Phase 4 (Event Generation & Backend Ingestion):** Pending authorization.

