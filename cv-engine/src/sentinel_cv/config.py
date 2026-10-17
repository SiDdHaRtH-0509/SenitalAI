"""Configuration module for SentinelAI Computer Vision Engine.

Supports loading configuration from environment variables with safe defaults
for local development, strict validation of all parameters, and clear,
actionable error messages.
"""

from dataclasses import dataclass, field
import json
import math
import os
from typing import Any, List, Optional, Set, Tuple

VALID_INPUT_SOURCE_TYPES: Set[str] = {"file", "camera", "stream", "replay"}
VALID_LOG_LEVELS: Set[str] = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
VALID_REF_STRATEGIES: Set[str] = {"bottom_center", "center"}
VALID_SEVERITIES: Set[str] = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


class ConfigurationError(ValueError):
    """Raised when a configuration value is invalid or cannot be parsed."""
    pass


@dataclass(frozen=True)
class CVConfig:
    """Immutable configuration container for the CV engine pipeline."""

    # Input source settings
    input_source_type: str = "file"
    video_source: str = "sample-data/demo.mp4"
    camera_id: str = "cam-demo-01"

    # Processing dimensions & rate
    target_width: Optional[int] = 1280
    target_height: Optional[int] = 720
    target_fps: float = 10.0

    # Logging
    log_level: str = "INFO"

    # Detector settings (Phase 2)
    model_type: str = "placeholder"
    model_path: Optional[str] = None
    confidence_threshold: float = 0.50

    # Zone & Event settings (Phase 3)
    zone_id: str = "zone-restricted-01"
    zone_name: str = "Restricted Zone 01"
    zone_vertices: Optional[Tuple[Tuple[float, float], ...]] = None
    zones_json: Optional[str] = None
    reference_point_strategy: str = "bottom_center"

    # Deduplication & Debounce (Phase 3/4)
    deduplication_cooldown_sec: float = 5.0
    temporal_confirmation_frames: int = 3
    replay_mode: bool = False

    # Event generation & Backend integration target (Phase 4)
    events_enabled: bool = True
    event_severity: str = "HIGH"
    base_timestamp: Optional[str] = "2026-10-17T09:30:00Z"
    backend_url: str = "http://localhost:8000"
    api_timeout: float = 5.0
    api_max_retries: int = 2

    def __post_init__(self) -> None:
        """Validate all configuration attributes strictly."""
        # 1. Validate input source type
        normalized_source_type = self.input_source_type.strip().lower()
        if normalized_source_type not in VALID_INPUT_SOURCE_TYPES:
            raise ConfigurationError(
                f"Invalid input_source_type '{self.input_source_type}'. "
                f"Must be one of: {sorted(VALID_INPUT_SOURCE_TYPES)}"
            )
        object.__setattr__(self, "input_source_type", normalized_source_type)

        # 2. Validate video source
        if not self.video_source or not str(self.video_source).strip():
            raise ConfigurationError(
                "video_source must be a non-empty string path or identifier."
            )

        # 3. Validate camera ID
        if not self.camera_id or not str(self.camera_id).strip():
            raise ConfigurationError("camera_id must be a non-empty string.")

        # 4. Validate target dimensions
        if self.target_width is not None:
            if not isinstance(self.target_width, int) or isinstance(self.target_width, bool) or self.target_width <= 0:
                raise ConfigurationError(
                    f"target_width must be a positive integer, got: {self.target_width}"
                )
        if self.target_height is not None:
            if not isinstance(self.target_height, int) or isinstance(self.target_height, bool) or self.target_height <= 0:
                raise ConfigurationError(
                    f"target_height must be a positive integer, got: {self.target_height}"
                )

        # 5. Validate target FPS
        if not isinstance(self.target_fps, (int, float)) or isinstance(self.target_fps, bool) or not math.isfinite(self.target_fps) or self.target_fps <= 0.0:
            raise ConfigurationError(
                f"target_fps must be a finite positive number, got: {self.target_fps}"
            )

        # 6. Validate log level
        normalized_log_level = self.log_level.strip().upper()
        if normalized_log_level not in VALID_LOG_LEVELS:
            raise ConfigurationError(
                f"Invalid log_level '{self.log_level}'. Must be one of: {sorted(VALID_LOG_LEVELS)}"
            )
        object.__setattr__(self, "log_level", normalized_log_level)

        # 7. Validate confidence threshold
        if (
            not isinstance(self.confidence_threshold, (int, float))
            or isinstance(self.confidence_threshold, bool)
            or not math.isfinite(self.confidence_threshold)
            or not (0.0 <= float(self.confidence_threshold) <= 1.0)
        ):
            raise ConfigurationError(
                f"confidence_threshold must be a finite float between 0.0 and 1.0, got: {self.confidence_threshold}"
            )

        # 8. Validate zone settings
        if not self.zone_id or not str(self.zone_id).strip():
            raise ConfigurationError("zone_id must be a non-empty string.")
        if not self.zone_name or not str(self.zone_name).strip():
            raise ConfigurationError("zone_name must be a non-empty string.")

        normalized_strategy = self.reference_point_strategy.strip().lower()
        if normalized_strategy not in VALID_REF_STRATEGIES:
            raise ConfigurationError(
                f"Invalid reference_point_strategy '{self.reference_point_strategy}'. "
                f"Must be one of: {sorted(VALID_REF_STRATEGIES)}"
            )
        object.__setattr__(self, "reference_point_strategy", normalized_strategy)

        # 9. Validate deduplication cooldown
        if (
            not isinstance(self.deduplication_cooldown_sec, (int, float))
            or isinstance(self.deduplication_cooldown_sec, bool)
            or not math.isfinite(self.deduplication_cooldown_sec)
            or float(self.deduplication_cooldown_sec) < 0.0
        ):
            raise ConfigurationError(
                f"deduplication_cooldown_sec must be a non-negative finite number, got: {self.deduplication_cooldown_sec}"
            )

        # 10. Validate temporal confirmation frames
        if (
            not isinstance(self.temporal_confirmation_frames, int)
            or isinstance(self.temporal_confirmation_frames, bool)
            or self.temporal_confirmation_frames < 1
        ):
            raise ConfigurationError(
                f"temporal_confirmation_frames must be an integer >= 1, got: {self.temporal_confirmation_frames}"
            )

        # 11. Validate backend URL
        if not self.backend_url or not str(self.backend_url).strip():
            raise ConfigurationError("backend_url must be a non-empty string URL.")

        # 12. Validate events_enabled
        if not isinstance(self.events_enabled, bool):
            raise ConfigurationError("events_enabled must be a boolean.")

        # 13. Validate event severity
        normalized_sev = self.event_severity.strip().upper()
        if normalized_sev not in VALID_SEVERITIES:
            raise ConfigurationError(
                f"Invalid event_severity '{self.event_severity}'. Must be one of: {sorted(VALID_SEVERITIES)}"
            )
        object.__setattr__(self, "event_severity", normalized_sev)

        # 14. Validate api_timeout
        if (
            not isinstance(self.api_timeout, (int, float))
            or isinstance(self.api_timeout, bool)
            or not math.isfinite(self.api_timeout)
            or float(self.api_timeout) <= 0.0
        ):
            raise ConfigurationError(
                f"api_timeout must be a positive finite number, got: {self.api_timeout}"
            )

        # 15. Validate api_max_retries
        if (
            not isinstance(self.api_max_retries, int)
            or isinstance(self.api_max_retries, bool)
            or self.api_max_retries < 0
        ):
            raise ConfigurationError(
                f"api_max_retries must be an integer >= 0, got: {self.api_max_retries}"
            )

        # 16. Validate base_timestamp
        if self.base_timestamp is not None:
            ts = str(self.base_timestamp).strip()
            if "T" not in ts or not (ts.endswith("Z") or "+" in ts or "-" in ts[10:]):
                raise ConfigurationError(
                    f"base_timestamp must be a valid ISO-8601 string with timezone, got: '{self.base_timestamp}'"
                )

    def get_configured_zones(self) -> List[Any]:
        """Resolve and instantiate PolygonZone instances from configuration.

        Returns:
            List[PolygonZone]: List of configured restricted zones.
        """
        from sentinel_cv.zone import PolygonZone

        # Priority 1: Explicit JSON list of zones
        if self.zones_json and self.zones_json.strip():
            try:
                data = json.loads(self.zones_json)
                if isinstance(data, list):
                    return [PolygonZone.from_dict(item) for item in data]
                if isinstance(data, dict):
                    return [PolygonZone.from_dict(data)]
            except Exception as json_err:
                raise ConfigurationError(f"Failed to parse CV_ZONES_JSON: {json_err}") from json_err

        # Priority 2: Custom zone_vertices tuple
        if self.zone_vertices is not None:
            return [
                PolygonZone(
                    zone_id=self.zone_id,
                    name=self.zone_name,
                    vertices=self.zone_vertices,
                    enabled=True,
                )
            ]

        # Priority 3: Default synthetic restricted zone for 1280x720 frame
        # (Illustrative polygon covering center-bottom buffer area)
        default_vertices = (
            (300.0, 300.0),
            (980.0, 300.0),
            (980.0, 700.0),
            (300.0, 700.0),
        )
        return [
            PolygonZone(
                zone_id=self.zone_id,
                name=self.zone_name,
                vertices=default_vertices,
                enabled=True,
            )
        ]

    @classmethod
    def from_env(cls) -> "CVConfig":
        """Load configuration from environment variables with safe defaults."""
        raw_width = os.getenv("CV_TARGET_WIDTH")
        parsed_width = int(raw_width) if raw_width and raw_width.strip() else 1280

        raw_height = os.getenv("CV_TARGET_HEIGHT")
        parsed_height = int(raw_height) if raw_height and raw_height.strip() else 720

        raw_fps = os.getenv("CV_TARGET_FPS")
        parsed_fps = float(raw_fps) if raw_fps and raw_fps.strip() else 10.0

        raw_conf = os.getenv("CV_CONFIDENCE_THRESHOLD")
        parsed_conf = float(raw_conf) if raw_conf and raw_conf.strip() else 0.50

        raw_cooldown = os.getenv("CV_DEDUPLICATION_COOLDOWN_SEC")
        parsed_cooldown = float(raw_cooldown) if raw_cooldown and raw_cooldown.strip() else 5.0

        raw_temporal = os.getenv("CV_TEMPORAL_CONFIRMATION_FRAMES")
        parsed_temporal = int(raw_temporal) if raw_temporal and raw_temporal.strip() else 3

        raw_replay = os.getenv("CV_REPLAY_MODE", "false").strip().lower()
        parsed_replay = raw_replay in {"1", "true", "yes", "on"}

        raw_events = os.getenv("CV_EVENTS_ENABLED", "true").strip().lower()
        parsed_events = raw_events in {"1", "true", "yes", "on"}

        raw_timeout = os.getenv("CV_API_TIMEOUT")
        parsed_timeout = float(raw_timeout) if raw_timeout and raw_timeout.strip() else 5.0

        raw_retries = os.getenv("CV_API_MAX_RETRIES")
        parsed_retries = int(raw_retries) if raw_retries and raw_retries.strip() else 2

        return cls(
            input_source_type=os.getenv("CV_INPUT_SOURCE_TYPE", "file"),
            video_source=os.getenv("CV_VIDEO_SOURCE", "sample-data/demo.mp4"),
            camera_id=os.getenv("CV_CAMERA_ID", "cam-demo-01"),
            target_width=parsed_width,
            target_height=parsed_height,
            target_fps=parsed_fps,
            log_level=os.getenv("CV_LOG_LEVEL", "INFO"),
            model_type=os.getenv("CV_MODEL_TYPE", "placeholder"),
            model_path=os.getenv("CV_MODEL_PATH") or None,
            confidence_threshold=parsed_conf,
            zone_id=os.getenv("CV_ZONE_ID", "zone-restricted-01"),
            zone_name=os.getenv("CV_ZONE_NAME", "Restricted Zone 01"),
            zones_json=os.getenv("CV_ZONES_JSON") or None,
            reference_point_strategy=os.getenv("CV_REFERENCE_POINT_STRATEGY", "bottom_center"),
            deduplication_cooldown_sec=parsed_cooldown,
            temporal_confirmation_frames=parsed_temporal,
            replay_mode=parsed_replay,
            events_enabled=parsed_events,
            event_severity=os.getenv("CV_EVENT_SEVERITY", "HIGH"),
            base_timestamp=os.getenv("CV_BASE_TIMESTAMP", "2026-10-17T09:30:00Z"),
            backend_url=os.getenv("CV_BACKEND_URL", "http://localhost:8000"),
            api_timeout=parsed_timeout,
            api_max_retries=parsed_retries,
        )
