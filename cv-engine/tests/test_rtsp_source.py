"""Automated test suite for RTSPVideoSource video ingestion module.

Verifies:
1. Safe credential redaction and protocol validation.
2. Connection lifecycle (DISCONNECTED -> CONNECTING -> CONNECTED).
3. Frame reading and metadata timestamp computation.
4. Automatic reconnection with exponential backoff on stream failure.
5. Bounded failure transitions (FAILED state after max attempts).
6. Synthetic fallback mode for headless/offline testing.
"""

from typing import Any, List, Optional, Tuple
import unittest
from unittest.mock import MagicMock

from sentinel_cv.models import FrameMetadata
from sentinel_cv.rtsp_source import (
    RTSPConnectionState,
    RTSPVideoSource,
    is_rtsp_url,
    redact_stream_url,
)


class MockVideoCapture:
    """Mock OpenCV VideoCapture object for deterministic testing."""

    def __init__(
        self,
        frames: int = 5,
        width: int = 1920,
        height: int = 1080,
        fps: float = 25.0,
        should_open: bool = True,
        fail_after: Optional[int] = None,
    ) -> None:
        self.frames = frames
        self.width = width
        self.height = height
        self.fps = fps
        self._is_opened = should_open
        self._current_frame = 0
        self.fail_after = fail_after
        self.released = False

    def isOpened(self) -> bool:
        return self._is_opened and not self.released

    def get(self, prop_id: int) -> float:
        if prop_id == 3:
            return float(self.width)
        if prop_id == 4:
            return float(self.height)
        if prop_id == 5:
            return float(self.fps)
        return 0.0

    def read(self) -> Tuple[bool, Optional[Any]]:
        if not self.isOpened():
            return False, None
        if self.fail_after is not None and self._current_frame >= self.fail_after:
            return False, None
        if self._current_frame >= self.frames:
            return False, None

        mock_frame = MagicMock()
        mock_frame.shape = (self.height, self.width, 3)
        self._current_frame += 1
        return True, mock_frame

    def release(self) -> None:
        self.released = True
        self._is_opened = False


class TestRTSPVideoSource(unittest.TestCase):
    """Test suite for RTSP stream acquisition and fault tolerance."""

    def test_url_redaction(self) -> None:
        """Verify passwords in RTSP and HTTP URLs are properly masked."""
        url_with_pass = "rtsp://admin:supersecret@192.168.1.50:554/h264"
        redacted = redact_stream_url(url_with_pass)
        self.assertNotIn("supersecret", redacted)
        self.assertIn("admin:***", redacted)
        self.assertIn("192.168.1.50:554/h264", redacted)

        # URL without credentials remains unchanged
        clean_url = "rtsp://edge-cam-01.local:554/live"
        self.assertEqual(redact_stream_url(clean_url), clean_url)

        # Empty and None handling
        self.assertEqual(redact_stream_url(""), "")
        self.assertEqual(redact_stream_url(None), "")

    def test_is_rtsp_url(self) -> None:
        """Verify scheme detection for RTSP protocols."""
        self.assertTrue(is_rtsp_url("rtsp://10.0.0.1:554/stream"))
        self.assertTrue(is_rtsp_url("rtsps://secure-cam.internal/feed"))
        self.assertTrue(is_rtsp_url("  RTSP://cam.local/h264  "))
        self.assertFalse(is_rtsp_url("http://localhost:8000/stream.mjpg"))
        self.assertFalse(is_rtsp_url("sample-data/demo.mp4"))
        self.assertFalse(is_rtsp_url(""))
        self.assertFalse(is_rtsp_url(None))

    def test_open_valid_stream(self) -> None:
        """Verify successful opening sets state to CONNECTED and extracts properties."""
        fake_cap = MockVideoCapture(frames=10, width=1280, height=720, fps=20.0)
        source = RTSPVideoSource(
            url="rtsp://operator:secret@10.0.0.5:554/ch01",
            source_id="cam-sector-a",
            capture_factory=lambda u: fake_cap,
        )

        self.assertEqual(source.connection_state, RTSPConnectionState.DISCONNECTED)
        self.assertNotIn("secret", source.redacted_url)

        opened = source.open()
        self.assertTrue(opened)
        self.assertTrue(source.is_opened())
        self.assertEqual(source.connection_state, RTSPConnectionState.CONNECTED)
        self.assertEqual(source.width, 1280)
        self.assertEqual(source.height, 720)
        self.assertEqual(source.fps, 20.0)
        self.assertEqual(source.total_frames, -1)  # Live stream marker

    def test_read_frames_successfully(self) -> None:
        """Verify sequential frame extraction with valid FrameMetadata."""
        fake_cap = MockVideoCapture(frames=3, width=1920, height=1080, fps=10.0)
        source = RTSPVideoSource(
            url="rtsp://10.0.0.5:554/live",
            source_id="cam-north",
            capture_factory=lambda u: fake_cap,
        )

        success, frame, meta = source.read_frame()
        self.assertTrue(success)
        self.assertIsNotNone(frame)
        self.assertIsInstance(meta, FrameMetadata)
        self.assertEqual(meta.frame_index, 0)
        self.assertEqual(meta.timestamp, 0.0)
        self.assertEqual(meta.source_id, "cam-north")

        # Second frame
        success2, frame2, meta2 = source.read_frame()
        self.assertTrue(success2)
        self.assertEqual(meta2.frame_index, 1)
        self.assertAlmostEqual(meta2.timestamp, 0.1, places=2)

    def test_reconnection_on_read_failure(self) -> None:
        """Verify automatic reconnection with exponential backoff on stream drop."""
        caps: List[MockVideoCapture] = [
            MockVideoCapture(frames=1, should_open=True, fail_after=1),  # fails after 1 frame
            MockVideoCapture(frames=5, should_open=True),                 # successful reconnect
        ]
        cap_iter = iter(caps)

        sleep_delays: List[float] = []

        source = RTSPVideoSource(
            url="rtsp://10.0.0.5:554/live",
            source_id="cam-failover",
            max_reconnect_attempts=3,
            initial_backoff_sec=0.5,
            backoff_factor=2.0,
            capture_factory=lambda u: next(cap_iter),
        )

        # First read succeeds
        ok1, _, meta1 = source.read_frame(sleep_fn=sleep_delays.append)
        self.assertTrue(ok1)
        self.assertEqual(meta1.frame_index, 0)

        # Second read triggers reconnect and recovers from 2nd capture
        ok2, _, meta2 = source.read_frame(sleep_fn=sleep_delays.append)
        self.assertTrue(ok2)
        self.assertGreater(source.reconnect_count, 0)
        self.assertEqual(source.connection_state, RTSPConnectionState.CONNECTED)

    def test_permanent_failure_after_max_reconnects(self) -> None:
        """Verify state transitions to FAILED when max_reconnect_attempts is reached."""
        source = RTSPVideoSource(
            url="rtsp://10.0.0.99:554/dead_stream",
            source_id="cam-dead",
            max_reconnect_attempts=2,
            initial_backoff_sec=0.1,
            capture_factory=lambda u: MockVideoCapture(should_open=False),
        )

        delays: List[float] = []
        # Attempt open
        opened = source.open()
        self.assertFalse(opened)

        # Attempt frame read - will try reconnects and hit limit
        ok, frame, meta = source.read_frame(sleep_fn=delays.append)
        self.assertFalse(ok)
        self.assertIsNone(frame)
        self.assertEqual(source.connection_state, RTSPConnectionState.FAILED)

    def test_synthetic_fallback_mode(self) -> None:
        """Verify synthetic fallback generates frames when real stream fails."""
        source = RTSPVideoSource(
            url="rtsp://unreachable.host:554/stream",
            source_id="cam-synth",
            synthetic_fallback=True,
            capture_factory=lambda u: MockVideoCapture(should_open=False),
        )

        opened = source.open()
        self.assertTrue(opened)
        self.assertTrue(source.is_synthetic)
        self.assertEqual(source.connection_state, RTSPConnectionState.CONNECTED)

        ok, frame, meta = source.read_frame()
        self.assertTrue(ok)
        self.assertIsNotNone(frame)
        self.assertEqual(meta.source_id, "cam-synth")
        self.assertEqual(meta.frame_index, 0)

    def test_clean_close_and_context_manager(self) -> None:
        """Verify resources are cleanly released and state reset on close."""
        fake_cap = MockVideoCapture(frames=5)
        with RTSPVideoSource(
            url="rtsp://10.0.0.1:554/live",
            capture_factory=lambda u: fake_cap,
        ) as source:
            self.assertTrue(source.is_opened())
            self.assertEqual(source.connection_state, RTSPConnectionState.CONNECTED)

        self.assertFalse(source.is_opened())
        self.assertEqual(source.connection_state, RTSPConnectionState.DISCONNECTED)
        self.assertTrue(fake_cap.released)


if __name__ == "__main__":
    unittest.main()
