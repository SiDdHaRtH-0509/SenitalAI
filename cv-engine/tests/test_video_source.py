"""Automated tests for OpenCVVideoSource video ingestion module."""

import math
from typing import Any, Optional, Tuple
import unittest
from unittest.mock import MagicMock

from sentinel_cv.models import FrameMetadata
from sentinel_cv.video_source import OpenCVVideoSource, VideoSourceError


class FakeCapture:
    """Simulated video capture object mimicking cv2.VideoCapture."""

    def __init__(
        self,
        num_frames: int = 5,
        width: int = 1280,
        height: int = 720,
        fps: float = 30.0,
        should_open: bool = True,
    ) -> None:
        self.num_frames = num_frames
        self.width = width
        self.height = height
        self.fps = fps
        self._is_opened = should_open
        self._current_frame = 0

    def isOpened(self) -> bool:
        return self._is_opened

    def get(self, prop_id: int) -> float:
        # cv2 property IDs: 3=WIDTH, 4=HEIGHT, 5=FPS, 7=FRAME_COUNT
        if prop_id == 3:
            return float(self.width)
        if prop_id == 4:
            return float(self.height)
        if prop_id == 5:
            return float(self.fps)
        if prop_id == 7:
            return float(self.num_frames)
        return 0.0

    def read(self) -> Tuple[bool, Optional[Any]]:
        if not self._is_opened or self._current_frame >= self.num_frames:
            return False, None

        # Return a mock frame object with shape attribute (height, width, channels)
        mock_frame = MagicMock()
        mock_frame.shape = (self.height, self.width, 3)
        self._current_frame += 1
        return True, mock_frame

    def release(self) -> None:
        self._is_opened = False


class TestOpenCVVideoSource(unittest.TestCase):
    """Test suite for OpenCVVideoSource behavior, properties, and error states."""

    def test_open_valid_mock_source(self) -> None:
        """Verify successful opening and property extraction from capture."""
        fake_cap = FakeCapture(num_frames=10, width=1920, height=1080, fps=24.0)
        source = OpenCVVideoSource(
            source="mock_feed.mp4",
            source_id="cam-gate-01",
            capture_factory=lambda src: fake_cap,
        )

        self.assertFalse(source.is_opened())
        opened = source.open()

        self.assertTrue(opened)
        self.assertTrue(source.is_opened())
        self.assertEqual(source.width, 1920)
        self.assertEqual(source.height, 1080)
        self.assertEqual(source.fps, 24.0)
        self.assertEqual(source.total_frames, 10)
        self.assertEqual(source.source_id, "cam-gate-01")

        source.close()
        self.assertFalse(source.is_opened())

    def test_open_nonexistent_file_path(self) -> None:
        """Verify opening a non-existent local file returns False without crashing."""
        source = OpenCVVideoSource(source="non_existent_directory/invalid_video_999.mp4")
        opened = source.open()
        self.assertFalse(opened)
        self.assertFalse(source.is_opened())

    def test_open_failing_capture_factory(self) -> None:
        """Verify failure when capture object cannot open."""
        unopened_cap = FakeCapture(should_open=False)
        source = OpenCVVideoSource(
            source="cam_0",
            capture_factory=lambda src: unopened_cap,
        )

        opened = source.open()
        self.assertFalse(opened)
        self.assertFalse(source.is_opened())

    def test_read_frames_sequential_and_metadata(self) -> None:
        """Verify sequential frame reading, frame indexing, and elapsed timestamp calculation."""
        fake_cap = FakeCapture(num_frames=3, width=640, height=480, fps=10.0)
        source = OpenCVVideoSource(
            source="demo.mp4",
            source_id="cam-01",
            capture_factory=lambda src: fake_cap,
        )

        source.open()

        # Frame 0
        ret0, frame0, meta0 = source.read_frame()
        self.assertTrue(ret0)
        self.assertIsNotNone(frame0)
        self.assertIsInstance(meta0, FrameMetadata)
        self.assertEqual(meta0.frame_index, 0)
        self.assertAlmostEqual(meta0.timestamp, 0.0)  # 0 / 10.0
        self.assertEqual(meta0.width, 640)
        self.assertEqual(meta0.height, 480)

        # Frame 1
        ret1, frame1, meta1 = source.read_frame()
        self.assertTrue(ret1)
        self.assertEqual(meta1.frame_index, 1)
        self.assertAlmostEqual(meta1.timestamp, 0.1)  # 1 / 10.0

        # Frame 2
        ret2, frame2, meta2 = source.read_frame()
        self.assertTrue(ret2)
        self.assertEqual(meta2.frame_index, 2)
        self.assertAlmostEqual(meta2.timestamp, 0.2)  # 2 / 10.0

        # EOF at Frame 3
        ret_eof, frame_eof, meta_eof = source.read_frame()
        self.assertFalse(ret_eof)
        self.assertIsNone(frame_eof)
        self.assertIsNone(meta_eof)

        source.close()

    def test_fallback_fps_when_container_reports_zero_or_nan(self) -> None:
        """Verify fallback FPS is used when container reports zero, negative, or NaN FPS."""
        # Zero FPS
        fake_zero_fps = FakeCapture(num_frames=5, fps=0.0)
        source_zero = OpenCVVideoSource(
            source="zero_fps.mp4",
            fallback_fps=15.0,
            capture_factory=lambda src: fake_zero_fps,
        )
        source_zero.open()
        self.assertEqual(source_zero.fps, 15.0)

        # Read a frame to verify zero-division protection
        ret, _, meta = source_zero.read_frame()
        self.assertTrue(ret)
        self.assertAlmostEqual(meta.timestamp, 0.0)
        source_zero.close()

        # NaN FPS
        fake_nan_fps = FakeCapture(num_frames=5, fps=float("nan"))
        source_nan = OpenCVVideoSource(
            source="nan_fps.mp4",
            fallback_fps=20.0,
            capture_factory=lambda src: fake_nan_fps,
        )
        source_nan.open()
        self.assertEqual(source_nan.fps, 20.0)
        source_nan.close()

    def test_invalid_fallback_fps_raises_value_error(self) -> None:
        """Verify negative or non-positive fallback_fps raises ValueError."""
        with self.assertRaises(ValueError):
            OpenCVVideoSource(source="demo.mp4", fallback_fps=0.0)
        with self.assertRaises(ValueError):
            OpenCVVideoSource(source="demo.mp4", fallback_fps=-10.0)
        with self.assertRaises(ValueError):
            OpenCVVideoSource(source="demo.mp4", fallback_fps=float("nan"))

    def test_context_manager_lifecycle(self) -> None:
        """Verify context manager protocol opens and automatically closes source."""
        fake_cap = FakeCapture(num_frames=2)
        with OpenCVVideoSource(source="ctx.mp4", capture_factory=lambda s: fake_cap) as src:
            self.assertTrue(src.is_opened())
            ret, _, _ = src.read_frame()
            self.assertTrue(ret)

        self.assertFalse(src.is_opened())


class TestReplayVideoSource(unittest.TestCase):
    """Test suite for ReplayVideoSource and create_video_source factory."""

    def test_replay_video_source_lifecycle(self) -> None:
        """Verify ReplayVideoSource generates synthetic frames up to limit."""
        from sentinel_cv.video_source import ReplayVideoSource

        source = ReplayVideoSource(total_frames=3, fps=10.0, width=640, height=480, source_id="test-cam")
        self.assertFalse(source.is_opened())
        self.assertTrue(source.open())
        self.assertTrue(source.is_opened())
        self.assertEqual(source.fps, 10.0)
        self.assertEqual(source.width, 640)
        self.assertEqual(source.height, 480)
        self.assertEqual(source.total_frames, 3)

        frames_read = 0
        for i in range(5):
            success, frame, meta = source.read_frame()
            if not success:
                break
            frames_read += 1
            self.assertIsNotNone(frame)
            self.assertIsNotNone(meta)
            self.assertEqual(meta.frame_index, i)
            self.assertAlmostEqual(meta.timestamp, i * 0.1)
            self.assertEqual(meta.source_id, "test-cam")

        self.assertEqual(frames_read, 3)
        self.assertEqual(source.frames_read, 3)
        source.close()
        self.assertFalse(source.is_opened())

    def test_replay_video_source_invalid_parameters(self) -> None:
        """Verify invalid parameters raise ValueError."""
        from sentinel_cv.video_source import ReplayVideoSource

        with self.assertRaises(ValueError):
            ReplayVideoSource(total_frames=0)
        with self.assertRaises(ValueError):
            ReplayVideoSource(fps=0.0)
        with self.assertRaises(ValueError):
            ReplayVideoSource(fps=-5.0)
        with self.assertRaises(ValueError):
            ReplayVideoSource(width=0)
        with self.assertRaises(ValueError):
            ReplayVideoSource(height=-10)

    def test_replay_video_source_context_manager(self) -> None:
        """Verify context manager protocol works for ReplayVideoSource."""
        from sentinel_cv.video_source import ReplayVideoSource

        with ReplayVideoSource(total_frames=2) as src:
            self.assertTrue(src.is_opened())
            ret, _, meta = src.read_frame()
            self.assertTrue(ret)
            self.assertEqual(meta.frame_index, 0)
        self.assertFalse(src.is_opened())

    def test_create_video_source_factory(self) -> None:
        """Verify create_video_source returns ReplayVideoSource when replay is requested."""
        from sentinel_cv.config import CVConfig
        from sentinel_cv.video_source import OpenCVVideoSource, ReplayVideoSource, create_video_source

        # Replay mode with missing video file -> ReplayVideoSource
        cfg_replay = CVConfig(replay_mode=True, video_source="non_existent_file.mp4")
        src = create_video_source(cfg_replay)
        self.assertIsInstance(src, ReplayVideoSource)

        # Standard file mode -> OpenCVVideoSource
        cfg_file = CVConfig(input_source_type="file", video_source="sample.mp4")
        src2 = create_video_source(cfg_file)
        self.assertIsInstance(src2, OpenCVVideoSource)


if __name__ == "__main__":
    unittest.main()

