"""Pipeline orchestration module for SentinelAI Computer Vision Engine.

Provides the foundational CVPipeline class implementing ICVPipeline.
In Phase 1, this class validates configuration, lifecycle state management,
metadata handling, and interface contracts. Video decoding and object detection
are intentionally deferred to Phase 2.
"""

from typing import Any, List, Optional, Tuple

from sentinel_cv.config import CVConfig, ConfigurationError
from sentinel_cv.interfaces import ICVPipeline, IDetector, IVideoSource
from sentinel_cv.logging_config import get_logger, setup_logging
from sentinel_cv.models import Detection, FrameMetadata, PipelineResult

logger = get_logger("pipeline")


class CVPipeline(ICVPipeline):
    """Computer vision pipeline orchestrator for SentinelAI.

    Manages lifecycle states (initialization, execution, termination)
    and routes frames through video acquisition, detector evaluation,
    and structured result generation.
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
            video_source: Video source adapter (Phase 2).
            detector: Object detector adapter (Phase 2).
        """
        self.config: CVConfig = config if config is not None else CVConfig.from_env()
        self.video_source: Optional[IVideoSource] = video_source
        self.detector: Optional[IDetector] = detector

        self._is_initialized: bool = False
        self._is_running: bool = False

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
            "Initializing SentinelAI CV Pipeline (Phase 1 Foundation) | "
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
            PipelineResult: Predictable output structure.

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

        # In Phase 1, if an active detector is passed, we delegate to it.
        # Otherwise, we return a structured result with zero detections and clear status.
        if self.detector is not None and self.detector.is_ready():
            detections = self.detector.detect(frame, metadata)
            return PipelineResult(
                metadata=metadata,
                detections=tuple(detections),
                processed=True,
                status_message="Frame processed by attached detector adapter.",
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

    def run(self) -> None:
        """Execute the continuous video processing loop.

        Raises:
            RuntimeError: If pipeline is not initialized.
            NotImplementedError: In Phase 1 when video source reader is not yet attached.
        """
        if not self._is_initialized:
            raise RuntimeError("CVPipeline must be initialized before running.")

        if self.video_source is None:
            raise NotImplementedError(
                "Continuous video processing loop requires a video source reader. "
                "OpenCV video acquisition will be implemented in Phase 2."
            )

        self._is_running = True
        logger.info("Starting processing loop...")

        try:
            if not self.video_source.is_opened():
                opened = self.video_source.open()
                if not opened:
                    logger.error("Failed to open video source: %s", self.config.video_source)
                    return

            while self._is_running:
                success, frame, metadata = self.video_source.read_frame()
                if not success or frame is None or metadata is None:
                    logger.info("End of video stream or read failure reached.")
                    break

                _ = self.process_frame(frame, metadata)
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the processing loop and release resources."""
        self._is_running = False
        if self.video_source is not None and self.video_source.is_opened():
            self.video_source.close()
        logger.info("Pipeline processing stopped.")
