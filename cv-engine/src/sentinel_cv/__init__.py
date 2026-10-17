"""SentinelAI Computer Vision Engine (Lead 2).

Intelligent Video Analytics Platform for Border Surveillance.
Phase 2: Video Processing & Person Detection.
"""

__version__ = "0.2.0"

from sentinel_cv.config import CVConfig, ConfigurationError
from sentinel_cv.detector import (
    MockPersonDetector,
    ModelLoadingError,
    YOLOPersonDetector,
    create_detector,
)
from sentinel_cv.interfaces import (
    ICVPipeline,
    IDetector,
    IVideoSource,
    IZoneAnalyzer,
)
from sentinel_cv.logging_config import get_logger, setup_logging
from sentinel_cv.models import (
    BoundingBox,
    Detection,
    FrameMetadata,
    PipelineResult,
)
from sentinel_cv.pipeline import CVPipeline
from sentinel_cv.video_source import OpenCVVideoSource, VideoSourceError

__all__ = [
    "__version__",
    "BoundingBox",
    "ConfigurationError",
    "CVConfig",
    "CVPipeline",
    "Detection",
    "FrameMetadata",
    "ICVPipeline",
    "IDetector",
    "IVideoSource",
    "IZoneAnalyzer",
    "MockPersonDetector",
    "ModelLoadingError",
    "OpenCVVideoSource",
    "PipelineResult",
    "VideoSourceError",
    "YOLOPersonDetector",
    "create_detector",
    "get_logger",
    "setup_logging",
]
