"""SentinelAI Computer Vision Engine (Lead 2).

Intelligent Video Analytics Platform for Border Surveillance.
Provides modular, architecture-neutral computer vision building blocks.
"""

__version__ = "0.1.0"

from sentinel_cv.config import CVConfig, ConfigurationError
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
    "PipelineResult",
    "get_logger",
    "setup_logging",
]
