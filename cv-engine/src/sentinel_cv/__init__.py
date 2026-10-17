"""SentinelAI Computer Vision Engine (Lead 2).

Intelligent Video Analytics Platform for Border Surveillance.
Phase 4: Event Generation & Backend Integration.
"""

__version__ = "0.4.0"

from sentinel_cv.backend_client import BackendClient
from sentinel_cv.config import CVConfig, ConfigurationError
from sentinel_cv.detector import (
    MockPersonDetector,
    ModelLoadingError,
    YOLOPersonDetector,
    create_detector,
)
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
    BoundingBox,
    Detection,
    EventSubmissionResult,
    FrameMetadata,
    PipelineResult,
    SecurityEvent,
    ZoneAnalysisResult,
)
from sentinel_cv.pipeline import CVPipeline
from sentinel_cv.video_source import OpenCVVideoSource, VideoSourceError
from sentinel_cv.zone import PolygonZone, ZoneAnalyzer

__all__ = [
    "__version__",
    "BackendClient",
    "BoundingBox",
    "ConfigurationError",
    "CVConfig",
    "CVPipeline",
    "Detection",
    "EventGenerator",
    "EventSubmissionResult",
    "FrameMetadata",
    "IBackendClient",
    "ICVPipeline",
    "IDetector",
    "IEventGenerator",
    "IVideoSource",
    "IZoneAnalyzer",
    "MockPersonDetector",
    "ModelLoadingError",
    "OpenCVVideoSource",
    "PipelineResult",
    "PolygonZone",
    "SecurityEvent",
    "VideoSourceError",
    "YOLOPersonDetector",
    "ZoneAnalysisResult",
    "ZoneAnalyzer",
    "create_detector",
    "get_logger",
    "setup_logging",
]
