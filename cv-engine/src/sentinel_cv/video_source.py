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
from sentinel_cv.rtsp_source import (
    RTSPConnectionState,
    RTSPVideoSource,
    is_rtsp_url,
    redact_stream_url,
)

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
        if callable(get_prop):
            try:
                raw_fps = float(get_prop(5))
                if math.isfinite(raw_fps) and raw_fps > 0.0:
                    self._fps = raw_fps
                else:
                    logger.warning(
                        "Video source reported invalid FPS (%s). Using fallback: %.1f FPS",
                        raw_fps,
                        self.fallback_fps,
                    )
                    self._fps = self.fallback_fps

                self._width = int(get_prop(3))
                self._height = int(get_prop(4))
                self._total_frames = int(get_prop(7))
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


class ReplayVideoSource(IVideoSource):
    """Deterministic synthetic video source for replay demonstration and fallback testing.

    Generates synthetic video frames without requiring external video files, codecs,
    or camera hardware. 100% compatible with headless environments and IBM LinuxONE.
    """

    def __init__(
        self,
        total_frames: int = 10,
        fps: float = 10.0,
        width: int = 1280,
        height: int = 720,
        source_id: str = "replay-stream-01",
    ) -> None:
        if total_frames < 1:
            raise ValueError(f"total_frames must be >= 1, got {total_frames}")
        if fps <= 0.0 or not math.isfinite(fps):
            raise ValueError(f"fps must be a positive finite number, got {fps}")
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive integers")

        self._total_frames = total_frames
        self._fps = float(fps)
        self._width = int(width)
        self._height = int(height)
        self.source_id = source_id

        self._is_opened = False
        self._frame_count = 0

    @property
    def fps(self) -> float:
        return self._fps

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def total_frames(self) -> int:
        return self._total_frames

    @property
    def frames_read(self) -> int:
        return self._frame_count

    def open(self) -> bool:
        self._is_opened = True
        self._frame_count = 0
        logger.info(
            "Opened ReplayVideoSource: %s | Dimensions: %sx%s | FPS: %.2f | Frames: %d",
            self.source_id,
            self._width,
            self._height,
            self._fps,
            self._total_frames,
        )
        return True

    def read_frame(self) -> Tuple[bool, Optional[Any], Optional[FrameMetadata]]:
        if not self._is_opened:
            if not self.open():
                return False, None, None

        if self._frame_count >= self._total_frames:
            logger.info("ReplayVideoSource reached total frames limit (%d).", self._total_frames)
            return False, None, None

        elapsed_sec = float(self._frame_count) / self._fps
        meta = FrameMetadata(
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
            frame = f"synthetic_frame_{self._frame_count}"

        self._frame_count += 1
        return True, frame, meta

    def close(self) -> None:
        self._is_opened = False
        logger.debug("Closed ReplayVideoSource: %s", self.source_id)

    def is_opened(self) -> bool:
        return self._is_opened

    def __enter__(self) -> "ReplayVideoSource":
        self.open()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()


def create_video_source(config: Any) -> IVideoSource:
    """Factory creating an IVideoSource based on CVConfig.

    If input_source_type is 'replay' or replay_mode is active and the video file
    does not exist locally, falls back to ReplayVideoSource.
    If input_source_type is 'stream' or video_source is an RTSP URI, creates RTSPVideoSource.

    Args:
        config: CVConfig containing video configuration.

    Returns:
        IVideoSource: Instantiated video source adapter.
    """
    is_replay = getattr(config, "input_source_type", "file") == "replay" or (
        getattr(config, "replay_mode", False) and not os.path.exists(getattr(config, "video_source", ""))
    )

    if is_replay:
        logger.info("Initializing ReplayVideoSource for deterministic replay fallback.")
        return ReplayVideoSource(
            total_frames=10,
            fps=getattr(config, "target_fps", 10.0),
            width=getattr(config, "target_width", 1280) or 1280,
            height=getattr(config, "target_height", 720) or 720,
            source_id=getattr(config, "camera_id", "cam-demo-01"),
        )

    v_source = str(getattr(config, "video_source", "sample-data/demo.mp4"))
    source_type = getattr(config, "input_source_type", "file")

    if is_rtsp_url(v_source) or source_type in ("stream", "rtsp"):
        logger.info("Initializing RTSPVideoSource for live surveillance stream: %s", redact_stream_url(v_source))
        return RTSPVideoSource(
            url=v_source,
            source_id=getattr(config, "camera_id", "cam-demo-01"),
            fallback_fps=getattr(config, "target_fps", 20.0),
            synthetic_fallback=getattr(config, "replay_mode", False),
        )

    return OpenCVVideoSource(
        source=v_source,
        source_id=getattr(config, "camera_id", "cam-demo-01"),
        fallback_fps=getattr(config, "target_fps", 25.0),
    )


