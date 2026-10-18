"""RTSP Video Source module for SentinelAI Computer Vision Engine.

Provides RTSPVideoSource implementing IVideoSource with:
- Safe RTSP URL parsing and password redaction (never logging credentials).
- OpenCV VideoCapture backend with FFMPEG and TCP transport configuration.
- Connection state tracking (DISCONNECTED, CONNECTING, CONNECTED, RECONNECTING, FAILED).
- Robust connection timeout, exponential backoff, and automatic reconnection.
- Bounded read timeouts preventing indefinite socket hangs.
- Dependency injection / synthetic frame fallback for deterministic offline testing.
"""

from enum import Enum
import math
import os
import re
import time
from typing import Any, Callable, Optional, Tuple, Union
import urllib.parse

try:
    import cv2
except ImportError:
    cv2 = None  # type: ignore

from sentinel_cv.interfaces import IVideoSource
from sentinel_cv.logging_config import get_logger
from sentinel_cv.models import FrameMetadata

logger = get_logger("rtsp_source")


class RTSPConnectionState(str, Enum):
    """Connection states for RTSP video streams."""
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    RECONNECTING = "RECONNECTING"
    FAILED = "FAILED"


def redact_stream_url(url: Optional[str]) -> str:
    """Mask credentials in RTSP or HTTP URLs for safe logging and telemetry.

    Example:
        rtsp://admin:secret123@192.168.1.50:554/h264 -> rtsp://admin:***@192.168.1.50:554/h264
    """
    if not url or not isinstance(url, str):
        return ""
    try:
        parsed = urllib.parse.urlsplit(url)
        if parsed.password:
            netloc = f"{parsed.username}:***@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            return urllib.parse.urlunsplit((
                parsed.scheme,
                netloc,
                parsed.path,
                parsed.query,
                parsed.fragment,
            ))
        return url
    except Exception:
        return re.sub(r"://([^:@]+):([^@]+)@", r"://\1:***@", url)


def is_rtsp_url(url: Optional[str]) -> bool:
    """Check whether a URL is an RTSP stream URI."""
    if not url or not isinstance(url, str):
        return False
    lower = url.strip().lower()
    return lower.startswith("rtsp://") or lower.startswith("rtsps://")


class RTSPVideoSource(IVideoSource):
    """High-reliability RTSP video stream reader for continuous CCTV surveillance.

    Attributes:
        url: Raw RTSP stream URL (may contain authentication credentials).
        redacted_url: Credential-masked URL safe for logging and telemetry.
        source_id: Camera identifier (e.g. 'cam-north-01').
        fallback_fps: Default FPS if stream does not report frame rate.
        connection_state: Current operational state of the RTSP connection.
        reconnect_count: Total number of reconnection attempts made.
    """

    def __init__(
        self,
        url: str,
        source_id: str = "rtsp-cam-01",
        fallback_fps: float = 20.0,
        max_reconnect_attempts: int = 5,
        initial_backoff_sec: float = 1.0,
        backoff_factor: float = 2.0,
        max_backoff_sec: float = 30.0,
        read_timeout_sec: float = 5.0,
        transport_protocol: str = "tcp",
        capture_factory: Optional[Callable[[str], Any]] = None,
        synthetic_fallback: bool = False,
    ) -> None:
        """Initialize the RTSP stream ingestion source.

        Args:
            url: RTSP stream URL (e.g. rtsp://user:pass@192.168.1.10:554/live).
            source_id: Unique camera hardware / sector identifier.
            fallback_fps: Fallback FPS if RTSP SDP/container reports 0 or invalid FPS.
            max_reconnect_attempts: Max consecutive reconnect attempts (0 or negative = unlimited).
            initial_backoff_sec: Initial delay before first reconnection in seconds.
            backoff_factor: Multiplier for exponential backoff on consecutive retries.
            max_backoff_sec: Maximum reconnection backoff cap in seconds.
            read_timeout_sec: Frame read timeout before declaring connection degraded.
            transport_protocol: RTSP transport ('tcp' or 'udp'). TCP recommended for reliability.
            capture_factory: Optional injectable callable returning a VideoCapture-like object.
            synthetic_fallback: If True, falls back to synthetic frames when stream is unreachable.
        """
        if not url or not str(url).strip():
            raise ValueError("RTSP stream URL must be a non-empty string.")

        if not isinstance(fallback_fps, (int, float)) or fallback_fps <= 0.0 or not math.isfinite(fallback_fps):
            raise ValueError(f"fallback_fps must be a positive finite number, got {fallback_fps}")

        self.url: str = str(url).strip()
        self.redacted_url: str = redact_stream_url(self.url)
        self.source_id: str = source_id
        self.fallback_fps: float = float(fallback_fps)
        self.max_reconnect_attempts: int = max_reconnect_attempts
        self.initial_backoff_sec: float = max(0.1, float(initial_backoff_sec))
        self.backoff_factor: float = max(1.0, float(backoff_factor))
        self.max_backoff_sec: float = max(self.initial_backoff_sec, float(max_backoff_sec))
        self.read_timeout_sec: float = max(0.5, float(read_timeout_sec))
        self.transport_protocol: str = transport_protocol.lower() if transport_protocol in ("tcp", "udp") else "tcp"
        self.synthetic_fallback: bool = synthetic_fallback

        self._custom_factory: bool = capture_factory is not None
        self._capture_factory: Callable[[str], Any] = (
            capture_factory if capture_factory is not None else self._default_capture_factory
        )

        self._cap: Optional[Any] = None
        self._state: RTSPConnectionState = RTSPConnectionState.DISCONNECTED
        self._frame_count: int = 0
        self._fps: float = self.fallback_fps
        self._width: int = 1280
        self._height: int = 720
        self._total_frames: int = -1  # Live RTSP streams have indefinite frames
        self._reconnect_count: int = 0
        self._consecutive_failures: int = 0
        self._last_frame_time: float = 0.0
        self._last_reconnect_time: float = 0.0
        self._synthetic_mode: bool = False

    def _default_capture_factory(self, stream_url: str) -> Any:
        if cv2 is None:
            raise RuntimeError("OpenCV (cv2) is required for RTSPVideoSource but is not installed.")

        # Ensure TCP transport for RTSP to prevent packet drop artifacts over UDP
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = f"rtsp_transport;{self.transport_protocol}"
        try:
            return cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
        except Exception:
            return cv2.VideoCapture(stream_url)

    @property
    def connection_state(self) -> RTSPConnectionState:
        """Current connection state of the RTSP stream."""
        return self._state

    @property
    def reconnect_count(self) -> int:
        """Total number of reconnection attempts."""
        return self._reconnect_count

    @property
    def consecutive_failures(self) -> int:
        """Consecutive failed connection or read attempts."""
        return self._consecutive_failures

    @property
    def fps(self) -> float:
        """Effective stream FPS."""
        return self._fps

    @property
    def width(self) -> int:
        """Frame width."""
        return self._width

    @property
    def height(self) -> int:
        """Frame height."""
        return self._height

    @property
    def total_frames(self) -> int:
        """Total frames (-1 for live RTSP stream)."""
        return self._total_frames

    @property
    def frames_read(self) -> int:
        """Frames read since opening."""
        return self._frame_count

    @property
    def last_frame_timestamp(self) -> float:
        """Monotonic timestamp of the most recent successfully ingested frame."""
        return self._last_frame_time

    @property
    def is_synthetic(self) -> bool:
        """Whether the stream is operating in synthetic fallback mode."""
        return self._synthetic_mode

    def is_opened(self) -> bool:
        """Check whether the video stream is currently open and healthy."""
        if self._synthetic_mode:
            return self._state == RTSPConnectionState.CONNECTED
        if self._state != RTSPConnectionState.CONNECTED or self._cap is None:
            return False
        is_open_fn = getattr(self._cap, "isOpened", None)
        if callable(is_open_fn):
            return bool(is_open_fn())
        return True

    def open(self) -> bool:
        """Open the RTSP stream connection with timeout handling.

        Returns:
            bool: True if connection succeeded, False otherwise.
        """
        if self.is_opened():
            return True

        self._state = RTSPConnectionState.CONNECTING
        logger.info("Connecting to RTSP stream: %s (camera: %s, transport: %s)...",
                    self.redacted_url, self.source_id, self.transport_protocol)

        try:
            self._cap = self._capture_factory(self.url)
        except Exception as exc:
            logger.error("Failed to initialize capture for RTSP stream %s: %s", self.redacted_url, exc)
            return self._handle_open_failure()

        is_open_fn = getattr(self._cap, "isOpened", None)
        if is_open_fn is None or not is_open_fn():
            logger.warning("Could not establish RTSP connection to %s", self.redacted_url)
            return self._handle_open_failure()

        # Connection successful
        self._state = RTSPConnectionState.CONNECTED
        self._consecutive_failures = 0
        self._last_frame_time = time.monotonic()
        self._synthetic_mode = False

        # Query container / stream properties
        get_prop = getattr(self._cap, "get", None)
        if callable(get_prop):
            try:
                raw_fps = float(get_prop(5))
                if math.isfinite(raw_fps) and raw_fps > 0.0:
                    self._fps = raw_fps
                else:
                    self._fps = self.fallback_fps

                w = int(get_prop(3))
                h = int(get_prop(4))
                if w > 0 and h > 0:
                    self._width = w
                    self._height = h
            except Exception as prop_err:
                logger.debug("Could not read RTSP container properties: %s", prop_err)
                self._fps = self.fallback_fps

        logger.info("Connected to RTSP stream %s | Resolution: %sx%s | FPS: %.2f",
                    self.redacted_url, self._width, self._height, self._fps)
        return True

    def _handle_open_failure(self) -> bool:
        """Handle connection failure and check for synthetic fallback."""
        self.close()
        self._consecutive_failures += 1

        if self.synthetic_fallback:
            logger.warning(
                "RTSP stream %s unreachable. Engaging synthetic fallback for camera %s.",
                self.redacted_url,
                self.source_id,
            )
            self._state = RTSPConnectionState.CONNECTED
            self._synthetic_mode = True
            self._fps = self.fallback_fps
            self._last_frame_time = time.monotonic()
            return True

        if self.max_reconnect_attempts > 0 and self._consecutive_failures >= self.max_reconnect_attempts:
            self._state = RTSPConnectionState.FAILED
            logger.error(
                "RTSP stream %s failed permanently after %d consecutive attempts.",
                self.redacted_url,
                self._consecutive_failures,
            )
        else:
            self._state = RTSPConnectionState.RECONNECTING

        return False

    def reconnect(self, sleep_fn: Optional[Callable[[float], None]] = None) -> bool:
        """Attempt to reconnect to the RTSP stream using exponential backoff.

        Args:
            sleep_fn: Optional callable for sleeping (injected for deterministic testing).

        Returns:
            bool: True if reconnected successfully, False otherwise.
        """
        self._reconnect_count += 1
        self._state = RTSPConnectionState.RECONNECTING

        # Calculate exponential backoff duration
        attempt = self._consecutive_failures
        backoff = min(
            self.max_backoff_sec,
            self.initial_backoff_sec * (self.backoff_factor ** max(0, attempt - 1)),
        )

        logger.info(
            "Reconnecting to RTSP stream %s (attempt %d, backoff %.2fs)...",
            self.redacted_url,
            self._reconnect_count,
            backoff,
        )

        sleeper = sleep_fn if sleep_fn is not None else time.sleep
        try:
            if backoff > 0:
                sleeper(backoff)
        except Exception:
            pass

        self.close()
        return self.open()

    def read_frame(
        self,
        sleep_fn: Optional[Callable[[float], None]] = None,
    ) -> Tuple[bool, Optional[Any], Optional[FrameMetadata]]:
        """Read the next video frame from the RTSP stream.

        Handles transient drops, stream stall timeouts, and automatic reconnection.

        Returns:
            Tuple containing:
                - bool: True if frame read succeeded, False otherwise.
                - Optional[Any]: Raw frame buffer (numpy array or synthetic frame).
                - Optional[FrameMetadata]: Frame sequence and timing metadata.
        """
        # If in synthetic mode, generate synthetic frames deterministically
        if self._synthetic_mode:
            return self._generate_synthetic_frame()

        if not self.is_opened():
            if self._state == RTSPConnectionState.FAILED:
                return False, None, None
            if not self.reconnect(sleep_fn=sleep_fn):
                return False, None, None

        read_fn = getattr(self._cap, "read", None)
        if not callable(read_fn):
            logger.error("Capture object missing read() method.")
            self._state = RTSPConnectionState.FAILED
            return False, None, None

        try:
            ret, frame = read_fn()
        except Exception as exc:
            logger.warning("Exception during frame read on RTSP stream %s: %s", self.redacted_url, exc)
            ret, frame = False, None

        # Check for empty frame or read failure
        if not ret or frame is None:
            self._consecutive_failures += 1
            logger.warning(
                "RTSP frame read dropped on %s (consecutive drops: %d).",
                self.redacted_url,
                self._consecutive_failures,
            )

            # Trigger reconnection
            if self.max_reconnect_attempts <= 0 or self._consecutive_failures < self.max_reconnect_attempts:
                reconnected = self.reconnect(sleep_fn=sleep_fn)
                if reconnected and self._cap is not None:
                    # Retry reading once immediately after reconnect
                    try:
                        ret_retry, frame_retry = self._cap.read()
                        if ret_retry and frame_retry is not None:
                            return self._process_frame_payload(frame_retry)
                    except Exception:
                        pass
            else:
                self._state = RTSPConnectionState.FAILED
                logger.error("RTSP stream %s exceeded max reconnect attempts.", self.redacted_url)

            return False, None, None

        return self._process_frame_payload(frame)

    def _process_frame_payload(self, frame: Any) -> Tuple[bool, Any, FrameMetadata]:
        """Process successful frame buffer and compute metadata."""
        self._consecutive_failures = 0
        now = time.monotonic()
        self._last_frame_time = now

        if hasattr(frame, "shape") and len(frame.shape) >= 2:
            self._height = int(frame.shape[0])
            self._width = int(frame.shape[1])

        elapsed_sec = float(self._frame_count) / self._fps if self._fps > 0 else 0.0

        metadata = FrameMetadata(
            frame_index=self._frame_count,
            timestamp=elapsed_sec,
            width=self._width,
            height=self._height,
            source_id=self.source_id,
        )

        self._frame_count += 1
        return True, frame, metadata

    def _generate_synthetic_frame(self) -> Tuple[bool, Any, FrameMetadata]:
        """Generate a synthetic frame when running in fallback mode."""
        now = time.monotonic()
        self._last_frame_time = now

        elapsed_sec = float(self._frame_count) / self._fps if self._fps > 0 else 0.0
        metadata = FrameMetadata(
            frame_index=self._frame_count,
            timestamp=elapsed_sec,
            width=self._width,
            height=self._height,
            source_id=self.source_id,
        )

        try:
            import numpy as np
            frame = np.zeros((self._height, self._width, 3), dtype=np.uint8)
        except ImportError:
            frame = f"synthetic_rtsp_frame_{self._frame_count}"

        self._frame_count += 1
        return True, frame, metadata

    def close(self) -> None:
        """Release underlying stream resources and reset connection state."""
        if self._cap is not None:
            release_fn = getattr(self._cap, "release", None)
            if callable(release_fn):
                try:
                    release_fn()
                except Exception as exc:
                    logger.debug("Error releasing RTSP capture: %s", exc)
            self._cap = None

        if self._state != RTSPConnectionState.FAILED:
            self._state = RTSPConnectionState.DISCONNECTED
        logger.debug("Closed RTSP stream: %s", self.redacted_url)

    def __enter__(self) -> "RTSPVideoSource":
        self.open()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
