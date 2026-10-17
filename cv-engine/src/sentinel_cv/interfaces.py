"""Abstract interfaces and protocols for SentinelAI CV Engine components.

Defines clear component boundaries between video acquisition, object detection,
zone analysis, and pipeline orchestration. Future phases will provide concrete
implementations of these interfaces (e.g. OpenCV video reader, ONNX/YOLO detector).
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple

from sentinel_cv.models import (
    Detection,
    EventSubmissionResult,
    FrameMetadata,
    PipelineResult,
    SecurityEvent,
    ZoneAnalysisResult,
)


class IVideoSource(ABC):
    """Interface for video acquisition sources (files, RTSP streams, camera devices)."""

    @abstractmethod
    def open(self) -> bool:
        """Open the video stream or file.

        Returns:
            bool: True if the source was opened successfully, False otherwise.
        """
        pass

    @abstractmethod
    def read_frame(self) -> Tuple[bool, Optional[Any], Optional[FrameMetadata]]:
        """Read the next video frame and its associated metadata.

        Returns:
            Tuple containing:
                - bool: True if frame read succeeded, False on EOF or failure.
                - Optional[Any]: Raw frame buffer/array (e.g. numpy array or placeholder).
                - Optional[FrameMetadata]: Frame sequence and timing metadata.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Release underlying video acquisition resources."""
        pass

    @abstractmethod
    def is_opened(self) -> bool:
        """Check whether the video source is currently opened and active."""
        pass


class IDetector(ABC):
    """Interface for object detector adapters (e.g. MobileNet, YOLO, ONNX, CPU fallback)."""

    @abstractmethod
    def is_ready(self) -> bool:
        """Check whether model weights/runtime are loaded and ready for inference."""
        pass

    @abstractmethod
    def detect(self, frame: Any, metadata: FrameMetadata) -> List[Detection]:
        """Perform object detection on a single frame.

        Args:
            frame: Raw image array / frame buffer.
            metadata: Associated frame metadata.

        Returns:
            List[Detection]: Detected objects with validated bounding boxes and confidences.
        """
        pass


class IZoneAnalyzer(ABC):
    """Interface for spatial zone-intersection analysis (Phase 3)."""

    @abstractmethod
    def evaluate(self, detections: List[Detection], metadata: FrameMetadata) -> List[Any]:
        """Evaluate detections against configured restricted zones.

        Args:
            detections: Detections in the current frame.
            metadata: Frame metadata.

        Returns:
            List of detected zone-entry events or candidates.
        """
        pass


class IEventGenerator(ABC):
    """Interface for generating structured security events from zone analysis observations."""

    @abstractmethod
    def process_zone_results(
        self,
        zone_results: List[ZoneAnalysisResult],
        metadata: FrameMetadata,
    ) -> List[SecurityEvent]:
        """Evaluate zone results and generate structured events conforming to API_CONTRACT.md.

        Applies temporal confirmation debouncing and cooldown deduplication policies.

        Args:
            zone_results: Results of spatial evaluation for current frame.
            metadata: Associated frame sequence and timing metadata.

        Returns:
            List[SecurityEvent]: Structured security events qualifying for emission.
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset internal temporal debounce and cooldown state."""
        pass


class IBackendClient(ABC):
    """Interface for submitting events to the shared SentinelAI backend service."""

    @abstractmethod
    def check_health(self) -> Tuple[bool, str]:
        """Check backend service connectivity via GET /api/health.

        Returns:
            Tuple[bool, str]: (is_healthy, status_message)
        """
        pass

    @abstractmethod
    def submit_event(self, event: SecurityEvent) -> EventSubmissionResult:
        """Submit a single SecurityEvent to POST /api/events.

        Args:
            event: Structured SecurityEvent.

        Returns:
            EventSubmissionResult: Outcome of submission (success, status_code, response/error).
        """
        pass


class ICVPipeline(ABC):
    """High-level orchestration interface for the CV engine."""

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize pipeline components, configuration, and logging.

        Returns:
            bool: True if initialized successfully, False otherwise.
        """
        pass

    @abstractmethod
    def process_frame(self, frame: Any, metadata: FrameMetadata) -> PipelineResult:
        """Process a single frame through the pipeline.

        Args:
            frame: Frame buffer / placeholder.
            metadata: Associated frame metadata.

        Returns:
            PipelineResult: Structured processing result.
        """
        pass

    @abstractmethod
    def run(self) -> None:
        """Execute the continuous video processing loop."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Signal the processing loop to terminate and release resources."""
        pass
