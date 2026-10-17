"""Automated tests for CV Engine Pipeline orchestration, streaming, and lifecycle."""

from typing import Any, List, Optional, Tuple
import unittest

from sentinel_cv.config import CVConfig
from sentinel_cv.interfaces import IDetector, IVideoSource
from sentinel_cv.models import BoundingBox, Detection, FrameMetadata, PipelineResult
from sentinel_cv.pipeline import CVPipeline


class MockDetector(IDetector):
    """Mock detector used strictly for testing interface contracts."""

    def __init__(self, ready: bool = True) -> None:
        self._ready = ready

    def is_ready(self) -> bool:
        return self._ready

    def detect(self, frame: Any, metadata: FrameMetadata) -> List[Detection]:
        bbox = BoundingBox(x1=10.0, y1=20.0, x2=50.0, y2=100.0)
        return [Detection(class_name="person", confidence=0.92, bbox=bbox)]


class MockVideoSource(IVideoSource):
    """Mock video source used strictly for testing pipeline loop orchestration."""

    def __init__(self, max_frames: int = 5) -> None:
        self.max_frames = max_frames
        self.current_frame = 0
        self._opened = False

    def open(self) -> bool:
        self._opened = True
        return True

    def read_frame(self) -> Tuple[bool, Optional[Any], Optional[FrameMetadata]]:
        if not self._opened or self.current_frame >= self.max_frames:
            return False, None, None
        meta = FrameMetadata(
            frame_index=self.current_frame,
            timestamp=float(self.current_frame) * 0.1,
            width=1280,
            height=720,
        )
        self.current_frame += 1
        return True, "fake_frame_buffer", meta

    def close(self) -> None:
        self._opened = False

    def is_opened(self) -> bool:
        return self._opened


class TestCVPipeline(unittest.TestCase):
    """Test suite for CVPipeline initialization, frame routing, streaming, and lifecycle."""

    def setUp(self) -> None:
        self.config = CVConfig(
            input_source_type="file",
            video_source="sample-data/demo.mp4",
            camera_id="cam-test",
            log_level="INFO",
        )
        self.pipeline = CVPipeline(config=self.config)
        self.sample_metadata = FrameMetadata(
            frame_index=0,
            timestamp=0.0,
            width=1280,
            height=720,
        )

    def test_pipeline_initialization(self) -> None:
        """Verify pipeline initializes cleanly and updates state."""
        self.assertFalse(self.pipeline.is_initialized)
        self.assertFalse(self.pipeline.is_running)

        success = self.pipeline.initialize()
        self.assertTrue(success)
        self.assertTrue(self.pipeline.is_initialized)

    def test_process_frame_uninitialized_raises_runtime_error(self) -> None:
        """Verify processing frame before initialization raises RuntimeError."""
        with self.assertRaises(RuntimeError) as ctx:
            self.pipeline.process_frame(frame=None, metadata=self.sample_metadata)
        self.assertIn("must be initialized", str(ctx.exception))

    def test_process_frame_invalid_metadata_raises_value_error(self) -> None:
        """Verify passing non-FrameMetadata raises ValueError."""
        self.pipeline.initialize()
        with self.assertRaises(ValueError):
            self.pipeline.process_frame(frame=None, metadata="invalid_metadata")  # type: ignore

    def test_process_frame_phase_1_foundation_behavior(self) -> None:
        """Verify Phase 1 behavior when detector is intentionally not attached.

        In Phase 1, pipeline must NOT fabricate fake detections or events.
        It returns a structured PipelineResult with zero detections and clear status.
        """
        self.pipeline.initialize()
        result = self.pipeline.process_frame(frame=None, metadata=self.sample_metadata)

        self.assertIsInstance(result, PipelineResult)
        self.assertEqual(result.metadata, self.sample_metadata)
        self.assertEqual(len(result.detections), 0)
        self.assertFalse(result.processed)
        self.assertIn("Phase 1 Foundation", result.status_message)

    def test_process_frame_with_attached_detector(self) -> None:
        """Verify pipeline properly routes frames to an attached detector interface."""
        mock_detector = MockDetector(ready=True)
        pipeline = CVPipeline(config=self.config, detector=mock_detector)
        pipeline.initialize()

        result = pipeline.process_frame(frame="frame_data", metadata=self.sample_metadata)
        self.assertTrue(result.processed)
        self.assertEqual(len(result.detections), 1)
        self.assertEqual(result.detections[0].class_name, "person")
        self.assertEqual(result.detections[0].confidence, 0.92)

    def test_run_uninitialized_raises_runtime_error(self) -> None:
        """Verify calling run before initialize raises RuntimeError."""
        with self.assertRaises(RuntimeError):
            self.pipeline.run()

    def test_run_without_video_source_raises_not_implemented(self) -> None:
        """Verify calling run in Phase 1 without video source raises NotImplementedError."""
        self.pipeline.initialize()
        with self.assertRaises(NotImplementedError) as ctx:
            self.pipeline.run()
        self.assertIn("Phase 2", str(ctx.exception))

    def test_run_with_mock_video_source_lifecycle(self) -> None:
        """Verify pipeline run executes loop until EOF and releases source cleanly."""
        mock_source = MockVideoSource(max_frames=3)
        pipeline = CVPipeline(config=self.config, video_source=mock_source)
        pipeline.initialize()

        results = pipeline.run()

        self.assertFalse(pipeline.is_running)
        self.assertFalse(mock_source.is_opened())
        self.assertEqual(len(results), 3)

    # --- Phase 2 Specific Tests ---

    def test_process_stream_streaming_incremental(self) -> None:
        """Verify process_stream yields results incrementally in sequential order."""
        mock_source = MockVideoSource(max_frames=4)
        mock_detector = MockDetector(ready=True)
        pipeline = CVPipeline(config=self.config, video_source=mock_source, detector=mock_detector)
        pipeline.initialize()

        stream = pipeline.process_stream()
        results = []
        for res in stream:
            self.assertIsInstance(res, PipelineResult)
            self.assertTrue(res.processed)
            self.assertEqual(len(res.detections), 1)
            results.append(res)

        self.assertEqual(len(results), 4)
        self.assertEqual([r.metadata.frame_index for r in results], [0, 1, 2, 3])
        self.assertFalse(pipeline.is_running)
        self.assertFalse(mock_source.is_opened())

    def test_process_stream_max_frames_limit(self) -> None:
        """Verify process_stream terminates immediately upon reaching max_frames."""
        mock_source = MockVideoSource(max_frames=10)
        pipeline = CVPipeline(config=self.config, video_source=mock_source)
        pipeline.initialize()

        results = list(pipeline.process_stream(max_frames=2))
        self.assertEqual(len(results), 2)
        self.assertFalse(pipeline.is_running)
        self.assertFalse(mock_source.is_opened())

    def test_process_stream_uninitialized_raises_runtime_error(self) -> None:
        """Verify calling process_stream before initialize raises RuntimeError."""
        with self.assertRaises(RuntimeError):
            next(self.pipeline.process_stream())

    def test_process_stream_without_source_raises_not_implemented(self) -> None:
        """Verify calling process_stream without video source raises NotImplementedError."""
        self.pipeline.initialize()
        with self.assertRaises(NotImplementedError):
            next(self.pipeline.process_stream())

    def test_pipeline_from_config_factory(self) -> None:
        """Verify CVPipeline.from_config factory creates and initializes components."""
        cfg = CVConfig(
            video_source="sample-data/demo.mp4",
            camera_id="cam-factory",
            model_type="mock",
        )
        pipeline = CVPipeline.from_config(config=cfg, auto_init=True)
        self.assertTrue(pipeline.is_initialized)
        self.assertIsNotNone(pipeline.video_source)
        self.assertIsNotNone(pipeline.detector)


if __name__ == "__main__":
    unittest.main()
