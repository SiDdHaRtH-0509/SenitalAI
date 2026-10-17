"""Pipeline orchestration module for SentinelAI Computer Vision Engine.

Connects video acquisition, frame metadata generation, object detector
evaluation, and restricted-zone spatial analysis into an incremental,
streaming processing pipeline.

Phase 3 capabilities:
- Incremental frame extraction via OpenCVVideoSource.
- Validated FrameMetadata generation.
- Person detection via IDetector (YOLOPersonDetector / MockPersonDetector).
- Restricted-zone spatial intersection via IZoneAnalyzer (ZoneAnalyzer).
- Streaming generator process_stream() preventing buffering frames in memory.
- Optional max_frames processing limits for controlled evaluation.
- Clean resource reclamation on EOF, limit reached, or exception.
"""

from typing import Any, Iterator, List, Optional, Tuple

from sentinel_cv.backend_client import BackendClient
from sentinel_cv.config import CVConfig, ConfigurationError
from sentinel_cv.detector import create_detector
from sentinel_cv.event_generator import EventGenerator
from sentinel_cv.interfaces import (
    IBackendClient,
    ICVPipeline,
    IDetector,
    IEventGenerator,
    IVideoSource,
    IZoneAnalyzer,
)
from sentinel_cv.logging_config import get_logger, setup_logging
from sentinel_cv.models import (
    Detection,
    EventSubmissionResult,
    FrameMetadata,
    PipelineResult,
    SecurityEvent,
    ZoneAnalysisResult,
)
from sentinel_cv.video_source import OpenCVVideoSource, ReplayVideoSource, VideoSourceError, create_video_source
from sentinel_cv.zone import ZoneAnalyzer

logger = get_logger("pipeline")


class CVPipeline(ICVPipeline):
    """Computer vision pipeline orchestrator for SentinelAI.

    Coordinates video stream ingestion, object detection, restricted-zone analysis,
    structured security event generation, and backend transmission.
    """

    def __init__(
        self,
        config: Optional[CVConfig] = None,
        video_source: Optional[IVideoSource] = None,
        detector: Optional[IDetector] = None,
        zone_analyzer: Optional[IZoneAnalyzer] = None,
        event_generator: Optional[IEventGenerator] = None,
        backend_client: Optional[IBackendClient] = None,
    ) -> None:
        """Initialize the pipeline with configuration and optional components.

        Args:
            config: CVConfig instance. If None, loads defaults from environment.
            video_source: Video source adapter (e.g. OpenCVVideoSource).
            detector: Object detector adapter (e.g. YOLOPersonDetector).
            zone_analyzer: Spatial zone analyzer (e.g. ZoneAnalyzer).
            event_generator: Security event generator (e.g. EventGenerator).
            backend_client: API client for backend transmission (e.g. BackendClient).
        """
        self.config: CVConfig = config if config is not None else CVConfig.from_env()
        self.video_source: Optional[IVideoSource] = video_source
        self.detector: Optional[IDetector] = detector
        self.zone_analyzer: Optional[IZoneAnalyzer] = zone_analyzer
        self.event_generator: Optional[IEventGenerator] = event_generator
        self.backend_client: Optional[IBackendClient] = backend_client

        self._is_initialized: bool = False
        self._is_running: bool = False

    @classmethod
    def from_config(
        cls,
        config: Optional[CVConfig] = None,
        auto_init: bool = True,
        enable_zone_analyzer: bool = True,
        enable_event_generator: bool = True,
        enable_backend_client: bool = True,
    ) -> "CVPipeline":
        """Factory creating a fully wired pipeline from configuration.

        Args:
            config: CVConfig instance or None to read environment.
            auto_init: If True, calls initialize() before returning.
            enable_zone_analyzer: If True, configures and attaches ZoneAnalyzer.
            enable_event_generator: If True, configures and attaches EventGenerator.
            enable_backend_client: If True, configures and attaches BackendClient.

        Returns:
            CVPipeline: Configured pipeline with all active components.
        """
        cfg = config if config is not None else CVConfig.from_env()
        source = create_video_source(cfg)
        detector = create_detector(cfg)

        zone_analyzer: Optional[IZoneAnalyzer] = None
        if enable_zone_analyzer:
            zones = cfg.get_configured_zones()
            zone_analyzer = ZoneAnalyzer(
                zones=zones,
                reference_point_strategy=cfg.reference_point_strategy,
            )

        event_generator: Optional[IEventGenerator] = None
        if enable_event_generator:
            event_generator = EventGenerator(
                camera_id=cfg.camera_id,
                severity=cfg.event_severity,
                temporal_confirmation_frames=cfg.temporal_confirmation_frames,
                deduplication_cooldown_sec=cfg.deduplication_cooldown_sec,
                base_timestamp=cfg.base_timestamp,
            )

        backend_client: Optional[IBackendClient] = None
        if enable_backend_client:
            backend_client = BackendClient(
                base_url=cfg.backend_url,
                timeout_seconds=cfg.api_timeout,
                max_retries=cfg.api_max_retries,
                events_enabled=cfg.events_enabled,
            )

        pipeline = cls(
            config=cfg,
            video_source=source,
            detector=detector,
            zone_analyzer=zone_analyzer,
            event_generator=event_generator,
            backend_client=backend_client,
        )
        if auto_init:
            pipeline.initialize()
        return pipeline

    @property
    def is_initialized(self) -> bool:
        """Whether the pipeline has been initialized."""
        return self._is_initialized

    @property
    def is_running(self) -> bool:
        """Whether the pipeline processing loop is currently running."""
        return self._is_running

    def initialize(self) -> bool:
        """Configure logging and validate pipeline readiness.

        Returns:
            bool: True on successful initialization.

        Raises:
            ConfigurationError: If pipeline configuration is invalid.
        """
        setup_logging(log_level=self.config.log_level)
        logger.info(
            "Initializing SentinelAI CV Pipeline | "
            "Source Type: %s | Source: %s | Camera: %s | Target: %sx%s @ %s FPS",
            self.config.input_source_type,
            self.config.video_source,
            self.config.camera_id,
            self.config.target_width,
            self.config.target_height,
            self.config.target_fps,
        )

        if self.detector is not None:
            if hasattr(self.detector, "load_model") and not self.detector.is_ready():
                try:
                    self.detector.load_model()
                except Exception as load_err:
                    logger.error("Failed to load detector during pipeline initialization: %s", load_err)
                    raise
            logger.info("Detector adapter attached: %s", type(self.detector).__name__)
        else:
            logger.info(
                "No detector attached. Phase 1 foundation active; "
                "detection model integration is scheduled for Phase 2."
            )

        if self.video_source is not None:
            logger.info("Video source adapter attached: %s", type(self.video_source).__name__)
        else:
            logger.info(
                "No video source attached. Video decoding integration "
                "is scheduled for Phase 2."
            )

        if self.zone_analyzer is not None:
            logger.info("Zone analyzer attached: %s", type(self.zone_analyzer).__name__)
        else:
            logger.debug("No zone analyzer attached.")

        if self.event_generator is not None:
            logger.info("Event generator attached: %s", type(self.event_generator).__name__)
        else:
            logger.debug("No event generator attached.")

        if self.backend_client is not None:
            logger.info(
                "Backend client attached: %s (Target: %s, Enabled: %s)",
                type(self.backend_client).__name__,
                self.config.backend_url,
                self.config.events_enabled,
            )
        else:
            logger.debug("No backend client attached.")

        self._is_initialized = True
        return True

    def process_frame(self, frame: Any, metadata: FrameMetadata) -> PipelineResult:
        """Process a single frame through the pipeline interface.

        Args:
            frame: Frame image buffer (numpy array or placeholder).
            metadata: Associated FrameMetadata.

        Returns:
            PipelineResult: Structured processing result with detections and zone evaluations.

        Raises:
            RuntimeError: If called before pipeline is initialized.
            ValueError: If metadata is invalid or missing.
        """
        if not self._is_initialized:
            raise RuntimeError("CVPipeline must be initialized before processing frames.")

        if not isinstance(metadata, FrameMetadata):
            raise ValueError(
                f"metadata must be an instance of FrameMetadata, got {type(metadata).__name__}"
            )

        if self.detector is not None:
            if not self.detector.is_ready() and hasattr(self.detector, "load_model"):
                self.detector.load_model()

            if self.detector.is_ready():
                detections = self.detector.detect(frame, metadata)
            zone_results: List[ZoneAnalysisResult] = []

            # Evaluate zone incursions if zone analyzer is attached
            if self.zone_analyzer is not None and detections:
                zone_results = self.zone_analyzer.evaluate(detections, metadata)

            # Generate security events if event generator is attached
            events: List[SecurityEvent] = []
            submissions: List[EventSubmissionResult] = []
            if self.event_generator is not None and zone_results:
                events = self.event_generator.process_zone_results(zone_results, metadata)

                # Submit events to backend if client is attached
                if self.backend_client is not None and events:
                    for ev in events:
                        sub_res = self.backend_client.submit_event(ev)
                        submissions.append(sub_res)

            inside_count = sum(1 for z in zone_results if z.is_inside)
            status_msg = (
                f"Detected {len(detections)} object(s) ({inside_count} inside restricted zone, "
                f"{len(events)} event(s) emitted)."
            )

            return PipelineResult(
                metadata=metadata,
                detections=tuple(detections),
                zone_results=tuple(zone_results),
                events=tuple(events),
                event_submissions=tuple(submissions),
                processed=True,
                status_message=status_msg,
            )

        return PipelineResult(
            metadata=metadata,
            detections=tuple(),
            zone_results=tuple(),
            events=tuple(),
            event_submissions=tuple(),
            processed=False,
            status_message=(
                "Phase 1 Foundation: Detector not attached. "
                "Object detection will be implemented in Phase 2."
            ),
        )

    def process_stream(
        self,
        max_frames: Optional[int] = None,
        progress_interval: int = 50,
    ) -> Iterator[PipelineResult]:
        """Streamingly process video frames one by one without buffering full video.

        Yields:
            PipelineResult: Structured detection results for each frame.

        Raises:
            RuntimeError: If pipeline is not initialized.
            NotImplementedError: If video source reader is not attached.
            VideoSourceError: If the video source cannot be opened.
        """
        if not self._is_initialized:
            raise RuntimeError("CVPipeline must be initialized before processing stream.")

        if self.video_source is None:
            raise NotImplementedError(
                "Continuous video processing loop requires a video source reader. "
                "OpenCV video acquisition will be implemented in Phase 2."
            )

        if max_frames is not None and max_frames <= 0:
            return

        self._is_running = True
        logger.info(
            "Beginning video stream processing (max_frames=%s)...",
            max_frames if max_frames is not None else "unlimited",
        )

        frames_processed = 0
        total_detections = 0
        total_zone_incursions = 0
        total_events_emitted = 0

        try:
            if not self.video_source.is_opened():
                opened = self.video_source.open()
                if not opened:
                    logger.error("Failed to open video source: %s", self.config.video_source)
                    raise VideoSourceError(f"Failed to open video source: {self.config.video_source}")

            while self._is_running:
                if max_frames is not None and frames_processed >= max_frames:
                    logger.info("Reached configured frame processing limit (%d frames).", max_frames)
                    break

                success, frame, metadata = self.video_source.read_frame()
                if not success or frame is None or metadata is None:
                    logger.info("End of video stream or read termination reached.")
                    break

                result = self.process_frame(frame, metadata)
                frames_processed += 1
                total_detections += len(result.detections)
                total_zone_incursions += len(result.inside_zone_results)
                total_events_emitted += len(result.events)

                if frames_processed % progress_interval == 0:
                    logger.info(
                        "Progress: Processed %d frames | Person Detections: %d | Zone Incursions: %d | Events: %d",
                        frames_processed,
                        total_detections,
                        total_zone_incursions,
                        total_events_emitted,
                    )

                yield result
        finally:
            self.stop()
            logger.info(
                "Video processing finished. Total frames: %d | Detections: %d | Incursions: %d | Events: %d",
                frames_processed,
                total_detections,
                total_zone_incursions,
                total_events_emitted,
            )

    def run(self, max_frames: Optional[int] = None) -> List[PipelineResult]:
        """Execute the continuous video processing loop and return results list.

        Args:
            max_frames: Optional limit on the number of frames to process.

        Returns:
            List[PipelineResult]: Collected results for the processed frames.

        Raises:
            RuntimeError: If pipeline is not initialized.
            NotImplementedError: In Phase 1 when video source reader is not yet attached.
        """
        results: List[PipelineResult] = []
        for res in self.process_stream(max_frames=max_frames):
            results.append(res)
        return results

    def stop(self) -> None:
        """Stop the processing loop and release resources."""
        self._is_running = False
        if self.video_source is not None and self.video_source.is_opened():
            self.video_source.close()
        logger.debug("Pipeline processing stopped.")
