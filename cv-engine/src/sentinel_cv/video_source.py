"""Video source ingestion module for SentinelAI Computer Vision Engine.

Provides OpenCVVideoSource implementing IVideoSource with support for:
- Prerecorded video files and live camera streams.
- Sequential frame extraction with accurate elapsed timestamps.
- Zero-division-safe fallback FPS handling.
- Graceful EOF and corruption detection.
- Context manager protocol for guaranteed resource cleanup.
- Dependency injection for deterministic testing without physical hardware.
"""

import math
import os
from typing import Any, Callable, Optional, Tuple, Union

try:
    import cv2
except ImportError:
    cv2 = None  # type: ignore

from sentinel_cv.interfaces import IVideoSource
from sentinel_cv.logging_config import get_logger
from sentinel_cv.models import FrameMetadata

logger = get_logger("video_source")


class VideoSourceError(RuntimeError):
    """Raised when an unrecoverable video source error occurs."""
    pass


class OpenCVVideoSource(IVideoSource):
    """OpenCV-based video source reader for video files and camera feeds.

    Attributes:
        source: File path (str) or camera index (int).
        source_id: Identifier for camera or stream (e.g. 'cam-demo-01').
        fallback_fps: Fallback FPS if video container reports 0, NaN, or invalid rate.
    """

    def __init__(
        self,
        source: Union[str, int],
        source_id: str = "cam-demo-01",
        fallback_fps: float = 25.0,
        capture_factory: Optional[Callable[[Union[str, int]], Any]] = None,
    ) -> None:
        """Initialize the video source reader.

        Args:
            source: Path to video file or camera index.
            source_id: Camera identifier for metadata tagging.
            fallback_fps: Safe default FPS if source FPS is indeterminate.
            capture_factory: Optional callable returning a cv2.VideoCapture-like object.
        """
        self.source: Union[str, int] = source
        self.source_id: str = source_id

        if not isinstance(fallback_fps, (int, float)) or fallback_fps <= 0.0 or not math.isfinite(fallback_fps):
            raise ValueError(f"fallback_fps must be a positive finite number, got {fallback_fps}")
        self.fallback_fps: float = float(fallback_fps)

        self._custom_factory: bool = capture_factory is not None
        self._capture_factory: Callable[[Union[str, int]], Any] = (
            capture_factory if capture_factory is not None else self._default_capture_factory
        )

        self._cap: Optional[Any] = None
        self._is_opened: bool = False
        self._frame_count: int = 0
        self._fps: float = self.fallback_fps
        self._width: int = 0
        self._height: int = 0
        self._total_frames: int = -1

    @staticmethod
    def _default_capture_factory(source: Union[str, int]) -> Any:
        if cv2 is None:
            raise VideoSourceError(
                "OpenCV (cv2) is required for OpenCVVideoSource but is not installed."
            )
        return cv2.VideoCapture(source)

    @property
    def fps(self) -> float:
        """Effective frames per second used for elapsed video time calculation."""
        return self._fps

    @property
    def width(self) -> int:
        """Frame width reported by the video source."""
        return self._width

    @property
    def height(self) -> int:
        """Frame height reported by the video source."""
        return self._height

    @property
    def total_frames(self) -> int:
        """Total frame count reported by video container, or -1 if live stream."""
        return self._total_frames

    @property
    def frames_read(self) -> int:
        """Number of frames successfully read so far."""
        return self._frame_count

    def open(self) -> bool:
        """Open the video stream or file.

        Returns:
            bool: True if source opened successfully, False otherwise.
        """
        if self._is_opened and self._cap is not None:
            return True

        # If using default capture factory and source is a local file path, verify file exists
        if not self._custom_factory and isinstance(self.source, str) and not self.source.startswith(("rtsp://", "http://", "https://")):
            if not os.path.exists(self.source):
                logger.error("Video file does not exist: %s", self.source)
                self._is_opened = False
                return False

        try:
            self._cap = self._capture_factory(self.source)
        except Exception as exc:
            logger.error("Failed to initialize capture for source '%s': %s", self.source, exc)
            self._is_opened = False
            return False

        # Verify capture opened successfully
        is_open_fn = getattr(self._cap, "isOpened", None)
        if is_open_fn is None or not is_open_fn():
            logger.error("Could not open video source: %s", self.source)
            self.close()
            return False

        self._is_opened = True
        self._frame_count = 0

        # Query container properties
        get_prop = getattr(self._cap, "get", None)
        if callable(get_prop) and cv2 is not None:
            try:
                raw_fps = float(get_prop(cv2.CAP_PROP_FPS))
                if math.isfinite(raw_fps) and raw_fps > 0.0:
                    self._fps = raw_fps
                else:
                    logger.warning(
                        "Video source reported invalid FPS (%s). Using fallback: %.1f FPS",
                        raw_fps,
                        self.fallback_fps,
                    )
                    self._fps = self.fallback_fps

                self._width = int(get_prop(cv2.CAP_PROP_FRAME_WIDTH))
                self._height = int(get_prop(cv2.CAP_PROP_FRAME_HEIGHT))
                self._total_frames = int(get_prop(cv2.CAP_PROP_FRAME_COUNT))
            except Exception as prop_err:
                logger.warning("Could not read video container properties: %s", prop_err)
                self._fps = self.fallback_fps
        else:
            self._fps = self.fallback_fps

        logger.info(
            "Opened video source: %s | Dimensions: %sx%s | FPS: %.2f | Container Frames: %s",
            self.source,
            self._width,
            self._height,
            self._fps,
            self._total_frames if self._total_frames > 0 else "unknown",
        )
        return True

    def read_frame(self) -> Tuple[bool, Optional[Any], Optional[FrameMetadata]]:
        """Read the next sequential frame and compute its metadata.

        Returns:
            Tuple containing:
                - bool: True if frame read succeeded, False on EOF or failure.
                - Optional[Any]: Raw image array (numpy array).
                - Optional[FrameMetadata]: FrameMetadata with sequence index and elapsed time.
        """
        if not self._is_opened or self._cap is None:
            if not self.open():
                return False, None, None

        read_fn = getattr(self._cap, "read", None)
        if not callable(read_fn):
            logger.error("Underlying capture object does not implement read()")
            return False, None, None

        try:
            ret, frame = read_fn()
        except Exception as exc:
            logger.error("Error occurred while reading frame %d: %s", self._frame_count, exc)
            return False, None, None

        if not ret or frame is None:
            logger.info(
                "Reached end of video stream or read failed at frame index %d.",
                self._frame_count,
            )
            return False, None, None

        # Dynamically determine frame dimensions if container didn't report them
        frame_height = self._height
        frame_width = self._width
        if hasattr(frame, "shape") and len(frame.shape) >= 2:
            frame_height = frame.shape[0]
            frame_width = frame.shape[1]
            self._height = frame_height
            self._width = frame_width

        # Ensure valid dimensions
        if frame_width <= 0:
            frame_width = 1280
        if frame_height <= 0:
            frame_height = 720

        # Calculate source-video elapsed time in seconds (strictly non-negative)
        elapsed_sec = float(self._frame_count) / self._fps if self._fps > 0 else 0.0

        metadata = FrameMetadata(
            frame_index=self._frame_count,
            timestamp=elapsed_sec,
            width=frame_width,
            height=frame_height,
            source_id=self.source_id,
        )

        self._frame_count += 1
        return True, frame, metadata

    def close(self) -> None:
        """Release the video capture handle and associated resources."""
        if self._cap is not None:
            release_fn = getattr(self._cap, "release", None)
            if callable(release_fn):
                try:
                    release_fn()
                except Exception as exc:
                    logger.warning("Error releasing video capture: %s", exc)
            self._cap = None

        self._is_opened = False
        logger.debug("Closed video source: %s", self.source)

    def is_opened(self) -> bool:
        """Check whether the video source is currently opened and active."""
        if not self._is_opened or self._cap is None:
            return False
        is_open_fn = getattr(self._cap, "isOpened", None)
        if callable(is_open_fn):
            return bool(is_open_fn())
        return self._is_opened

    def __enter__(self) -> "OpenCVVideoSource":
        """Enter context manager, opening the video source."""
        self.open()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager, releasing the video source."""
        self.close()
