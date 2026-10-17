# Lead 2 Checklist — Computer Vision

## Primary tasks
- [x] Read project context, architecture and event contract. **Done when:** payload and ownership are understood. *(Phase 1 completed)*
- [ ] Verify sample video permission, format and path. **Done when:** team can legally use it and access is documented. *(Ongoing: synthetic video fixture validated; awaiting official datathon sample video)*
- [x] Inspect Python/OS/architecture and existing model availability. **Done when:** chosen runtime is tested or a blocker is reported. *(Phase 1/2 completed: Python 3.14 verified, OpenCV 5.0 and Ultralytics YOLOv8 tested on CPU)*
- [x] Create/verify `cv-engine/` environment and requirements. **Done when:** setup steps are reproducible. *(Phase 1/2 completed: dependencies documented in requirements.txt, .env.example, .gitignore)*
- [x] Implement video reading. **Done when:** frames are read and invalid paths fail clearly. *(Phase 2 completed: OpenCVVideoSource with sequential frame extraction, zero-division safe fallback FPS, context manager, and EOF handling)*
- [x] Integrate a compatible pretrained person detector. **Done when:** a sample frame produces a detection or documented fallback is activated. *(Phase 2 completed: YOLOPersonDetector using YOLOv8n CPU, COCO person class filtering, BoundingBox validation, and MockPersonDetector fallback)*
- [x] Implement one configurable zone. **Done when:** zone is visible/configurable and geometry is documented. *(Phase 3 completed: PolygonZone with Shoelace area, bbox caching, and JSON/tuple vertex configuration)*
- [x] Implement zone-entry logic. **Done when:** representative point and entry rule are deterministic. *(Phase 3 completed: pure Python Ray-Casting algorithm with boundary tolerance, bottom-center ground contact anchor, ZoneAnalyzer adapter)*
- [ ] Add temporal confirmation. **Done when:** a single noisy frame does not immediately create an event. *(Phase 4)*
- [ ] Add event cooldown/deduplication. **Done when:** continuous presence does not flood backend. *(Phase 4)*
- [ ] Build event payload exactly as API contract. **Done when:** schema validation succeeds. *(Phase 4)*
- [ ] POST event to backend. **Done when:** event appears in backend storage/dashboard. *(Phase 4)*
- [ ] Add model/video/API error handling. **Done when:** failures are visible and recoverable. *(Phase 4)*
- [ ] Commit and open PR. **Done when:** lead can review isolated CV changes. *(Phase 5)*

## Secondary tasks
- [x] Add CLI options for video path, zone config, camera ID and backend URL. *(Phase 2/3 completed: CLI supports --video, --model, --confidence, --max-frames, --camera-id, --zone-id, --zone-vertices, --zones-file, --strategy, --json)*
- [ ] Save a short test log showing generated event fields.
- [ ] Add a clearly labelled deterministic replay fallback.

## Tertiary / optional
- [ ] Add vehicle detection only if person/zone pipeline is already integrated.
- [ ] Add tracking only if needed to stabilize zone entry and time remains.

## Completion criteria
One authorized video produces a valid zone-entry event through the shared API, duplicate events are controlled, and setup/limitations are documented.
