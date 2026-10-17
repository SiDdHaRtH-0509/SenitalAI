"""Pipeline orchestration module for SentinelAI Computer Vision Engine.

Connects video acquisition, frame metadata generation, and object detector
evaluation into an incremental, streaming processing pipeline.

Phase 2 capabilities:
- Incremental frame extraction via OpenCVVideoSource.
- Validated FrameMetadata generation.
- Person detection via IDetector (YOLOPersonDetector / MockPersonDetector).
- Streaming generator process_stream() preventing buffering frames in memory.
- Optional max_frames processing limits for controlled evaluation.
- Clean resource reclamation on EOF, limit reached, or exception.
"""

from typing import Any, Iterator, List, Optional, Tuple

from sentinel_cv.config import CVConfig, ConfigurationError
from sentinel_cv.detector import create_detector
from sentinel_cv.interfaces import ICVPipeline, IDetector, IVideoSource
from sentinel_cv.logging_config import get_logger, setup_logging
from sentinel_cv.models import Detection, FrameMetadata, PipelineResult
from sentinel_cv.video_source import OpenCVVideoSource, VideoSourceError

logger = get_logger("pipeline")


class CVPipeline(ICVPipeline):
    """Computer vision pipeline orchestrator for SentinelAI.

    Coordinates video stream ingestion, object detection, and structured
    result production.
    """

    def __init__(
        self,
        config: Optional[CVConfig] = None,
        video_source: Optional[IVideoSource] = None,
        detector: Optional[IDetector] = None,
    ) -> None:
        """Initialize the pipeline with configuration and optional components.

        Args:
            config: CVConfig instance. If None, loads defaults from environment.
            video_source: Video source adapter (e.g. OpenCVVideoSource).
            detector: Object detector adapter (e.g. YOLOPersonDetector).
        """
        self.config: CVConfig = config if config is not None else CVConfig.from_env()
        self.video_source: Optional[IVideoSource] = video_source
        self.detector: Optional[IDetector] = detector

        self._is_initialized: bool = False
        self._is_running: bool = False

    @classmethod
    def from_config(
        cls,
        config: Optional[CVConfig] = None,
        auto_init: bool = True,
    ) -> "CVPipeline":
        """Factory creating a fully wired pipeline from configuration.

        Args:
            config: CVConfig instance or None to read environment.
            auto_init: If True, calls initialize() before returning.

        Returns:
            CVPipeline: Configured pipeline with video source and detector.
        """
        cfg = config if config is not None else CVConfig.from_env()
        source = OpenCVVideoSource(
            source=cfg.video_source,
            source_id=cfg.camera_id,
            fallback_fps=cfg.target_fps,
        )
        detector = create_detector(cfg)

        pipeline = cls(config=cfg, video_source=source, detector=detector)
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

        self._is_initialized = True
        return True

    def process_frame(self, frame: Any, metadata: FrameMetadata) -> PipelineResult:
        """Process a single frame through the pipeline interface.

        Args:
            frame: Frame image buffer (numpy array or placeholder).
            metadata: Associated FrameMetadata.

        Returns:
            PipelineResult: Structured processing result.

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

        if self.detector is not None and self.detector.is_ready():
            detections = self.detector.detect(frame, metadata)
            return PipelineResult(
                metadata=metadata,
                detections=tuple(detections),
                processed=True,
                status_message=f"Detected {len(detections)} object(s).",
            )

        return PipelineResult(
            metadata=metadata,
            detections=tuple(),
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

                if frames_processed % progress_interval == 0:
                    logger.info(
                        "Progress: Processed %d frames | Cumulative Person Detections: %d",
                        frames_processed,
                        total_detections,
                    )

                yield result
        finally:
            self.stop()
            logger.info(
                "Video processing finished. Total frames processed: %d | Total person detections: %d",
                frames_processed,
                total_detections,
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
