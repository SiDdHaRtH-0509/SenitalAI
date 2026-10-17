"""SentinelAI Computer Vision Engine (Lead 2).

Intelligent Video Analytics Platform for Border Surveillance.
Phase 5: Final Testing, Optimization & Handover.
"""

__version__ = "1.0.0"

from sentinel_cv.backend_client import BackendClient
from sentinel_cv.config import CVConfig, ConfigurationError
from sentinel_cv.detector import (
    MockPersonDetector,
    ModelLoadingError,
    YOLOPersonDetector,
    create_detector,
    create_replay_detector,
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
from sentinel_cv.rtsp_source import (
    RTSPConnectionState,
    RTSPVideoSource,
    is_rtsp_url,
    redact_stream_url,
)
from sentinel_cv.video_source import (
    OpenCVVideoSource,
    ReplayVideoSource,
    VideoSourceError,
    create_video_source,
)
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
    "redact_stream_url",
    "ReplayVideoSource",
    "RTSPConnectionState",
    "RTSPVideoSource",
    "SecurityEvent",
    "VideoSourceError",
    "YOLOPersonDetector",
    "ZoneAnalysisResult",
    "ZoneAnalyzer",
    "create_detector",
    "create_replay_detector",
    "create_video_source",
    "get_logger",
    "is_rtsp_url",
    "setup_logging",
]

