"""Automated tests for shared CV data models (BoundingBox, Detection, FrameMetadata)."""

import math
import unittest

from sentinel_cv.models import BoundingBox, Detection, FrameMetadata, PipelineResult


class TestBoundingBox(unittest.TestCase):
    """Test suite for BoundingBox validation, geometry, and serialization."""

    def test_valid_bounding_box(self) -> None:
        """Verify creation and computed properties of a valid bounding box."""
        bbox = BoundingBox(x1=100.0, y1=150.0, x2=300.0, y2=450.0)

        self.assertEqual(bbox.x1, 100.0)
        self.assertEqual(bbox.y1, 150.0)
        self.assertEqual(bbox.x2, 300.0)
        self.assertEqual(bbox.y2, 450.0)

        # Geometric properties
        self.assertAlmostEqual(bbox.width, 200.0)
        self.assertAlmostEqual(bbox.height, 300.0)
        self.assertAlmostEqual(bbox.area, 60000.0)
        self.assertEqual(bbox.center, (200.0, 300.0))
        self.assertEqual(bbox.bottom_center, (200.0, 450.0))

        # Serializations
        self.assertEqual(bbox.as_tuple(), (100.0, 150.0, 300.0, 450.0))
        self.assertEqual(
            bbox.as_dict(),
            {"x1": 100.0, "y1": 150.0, "x2": 300.0, "y2": 450.0},
        )

    def test_invalid_horizontal_bounds(self) -> None:
        """Verify x2 <= x1 raises ValueError."""
        # x2 == x1
        with self.assertRaises(ValueError) as ctx:
            BoundingBox(x1=100.0, y1=50.0, x2=100.0, y2=150.0)
        self.assertIn("strictly greater than x1", str(ctx.exception))

        # x2 < x1
        with self.assertRaises(ValueError) as ctx:
            BoundingBox(x1=150.0, y1=50.0, x2=100.0, y2=150.0)
        self.assertIn("strictly greater than x1", str(ctx.exception))

    def test_invalid_vertical_bounds(self) -> None:
        """Verify y2 <= y1 raises ValueError."""
        # y2 == y1
        with self.assertRaises(ValueError) as ctx:
            BoundingBox(x1=50.0, y1=200.0, x2=150.0, y2=200.0)
        self.assertIn("strictly greater than y1", str(ctx.exception))

        # y2 < y1
        with self.assertRaises(ValueError) as ctx:
            BoundingBox(x1=50.0, y1=250.0, x2=150.0, y2=200.0)
        self.assertIn("strictly greater than y1", str(ctx.exception))

    def test_negative_coordinates(self) -> None:
        """Verify negative coordinates raise ValueError."""
        with self.assertRaises(ValueError):
            BoundingBox(x1=-10.0, y1=0.0, x2=100.0, y2=100.0)
        with self.assertRaises(ValueError):
            BoundingBox(x1=0.0, y1=-5.0, x2=100.0, y2=100.0)

    def test_nan_and_infinite_coordinates(self) -> None:
        """Verify NaN and Inf values raise ValueError."""
        with self.assertRaises(ValueError):
            BoundingBox(x1=float("nan"), y1=0.0, x2=100.0, y2=100.0)
        with self.assertRaises(ValueError):
            BoundingBox(x1=0.0, y1=0.0, x2=float("inf"), y2=100.0)
        with self.assertRaises(ValueError):
            BoundingBox(x1=0.0, y1=0.0, x2=100.0, y2=float("-inf"))

    def test_invalid_types_for_coordinates(self) -> None:
        """Verify non-numeric and boolean types raise ValueError."""
        with self.assertRaises(ValueError):
            BoundingBox(x1=True, y1=0.0, x2=100.0, y2=100.0)
        with self.assertRaises(ValueError):
            BoundingBox(x1="10", y1=0.0, x2=100.0, y2=100.0)  # type: ignore


class TestDetection(unittest.TestCase):
    """Test suite for Detection model validation and boundaries."""

    def setUp(self) -> None:
        self.valid_bbox = BoundingBox(x1=10.0, y1=20.0, x2=50.0, y2=120.0)

    def test_valid_detection(self) -> None:
        """Verify valid detection creation and serialization."""
        det = Detection(
            class_name="person",
            confidence=0.88,
            bbox=self.valid_bbox,
            track_id=1,
        )

        self.assertEqual(det.class_name, "person")
        self.assertEqual(det.confidence, 0.88)
        self.assertEqual(det.bbox, self.valid_bbox)
        self.assertEqual(det.track_id, 1)

        det_dict = det.to_dict()
        self.assertEqual(det_dict["class_name"], "person")
        self.assertEqual(det_dict["confidence"], 0.88)
        self.assertEqual(det_dict["track_id"], 1)
        self.assertEqual(det_dict["bbox"]["x1"], 10.0)

    def test_confidence_boundaries(self) -> None:
        """Verify confidence boundary values 0.0 and 1.0 are valid."""
        det_zero = Detection(class_name="person", confidence=0.0, bbox=self.valid_bbox)
        self.assertEqual(det_zero.confidence, 0.0)

        det_one = Detection(class_name="person", confidence=1.0, bbox=self.valid_bbox)
        self.assertEqual(det_one.confidence, 1.0)

    def test_confidence_out_of_bounds(self) -> None:
        """Verify confidence < 0 or > 1 raises ValueError."""
        with self.assertRaises(ValueError):
            Detection(class_name="person", confidence=-0.001, bbox=self.valid_bbox)
        with self.assertRaises(ValueError):
            Detection(class_name="person", confidence=1.001, bbox=self.valid_bbox)

    def test_confidence_nan_and_inf(self) -> None:
        """Verify NaN or Inf confidence raises ValueError."""
        with self.assertRaises(ValueError):
            Detection(class_name="person", confidence=float("nan"), bbox=self.valid_bbox)
        with self.assertRaises(ValueError):
            Detection(class_name="person", confidence=float("inf"), bbox=self.valid_bbox)

    def test_invalid_class_name(self) -> None:
        """Verify empty or non-string class_name raises ValueError."""
        with self.assertRaises(ValueError):
            Detection(class_name="", confidence=0.9, bbox=self.valid_bbox)
        with self.assertRaises(ValueError):
            Detection(class_name="   ", confidence=0.9, bbox=self.valid_bbox)
        with self.assertRaises(ValueError):
            Detection(class_name=123, confidence=0.9, bbox=self.valid_bbox)  # type: ignore

    def test_invalid_bbox_type(self) -> None:
        """Verify non-BoundingBox raises ValueError."""
        with self.assertRaises(ValueError):
            Detection(class_name="person", confidence=0.9, bbox=(10, 20, 30, 40))  # type: ignore

    def test_invalid_track_id(self) -> None:
        """Verify negative or boolean track_id raises ValueError."""
        with self.assertRaises(ValueError):
            Detection(class_name="person", confidence=0.9, bbox=self.valid_bbox, track_id=-1)
        with self.assertRaises(ValueError):
            Detection(class_name="person", confidence=0.9, bbox=self.valid_bbox, track_id=True)


class TestFrameMetadata(unittest.TestCase):
    """Test suite for FrameMetadata validation."""

    def test_valid_frame_metadata(self) -> None:
        """Verify valid frame metadata creation and serialization."""
        meta = FrameMetadata(
            frame_index=150,
            timestamp=5.0,
            width=1920,
            height=1080,
            source_id="cam-demo-01",
        )

        self.assertEqual(meta.frame_index, 150)
        self.assertEqual(meta.timestamp, 5.0)
        self.assertEqual(meta.width, 1920)
        self.assertEqual(meta.height, 1080)
        self.assertEqual(meta.source_id, "cam-demo-01")

        meta_dict = meta.to_dict()
        self.assertEqual(meta_dict["frame_index"], 150)
        self.assertEqual(meta_dict["timestamp"], 5.0)

    def test_invalid_frame_index(self) -> None:
        """Verify negative or boolean frame_index raises ValueError."""
        with self.assertRaises(ValueError):
            FrameMetadata(frame_index=-1, timestamp=0.0, width=1280, height=720)
        with self.assertRaises(ValueError):
            FrameMetadata(frame_index=True, timestamp=0.0, width=1280, height=720)

    def test_invalid_timestamp(self) -> None:
        """Verify negative, NaN, or Inf timestamp raises ValueError."""
        with self.assertRaises(ValueError):
            FrameMetadata(frame_index=0, timestamp=-0.1, width=1280, height=720)
        with self.assertRaises(ValueError):
            FrameMetadata(frame_index=0, timestamp=float("nan"), width=1280, height=720)
        with self.assertRaises(ValueError):
            FrameMetadata(frame_index=0, timestamp=float("inf"), width=1280, height=720)

    def test_invalid_dimensions(self) -> None:
        """Verify non-positive or boolean dimensions raise ValueError."""
        with self.assertRaises(ValueError):
            FrameMetadata(frame_index=0, timestamp=0.0, width=0, height=720)
        with self.assertRaises(ValueError):
            FrameMetadata(frame_index=0, timestamp=0.0, width=-100, height=720)
        with self.assertRaises(ValueError):
            FrameMetadata(frame_index=0, timestamp=0.0, width=1280, height=0)
        with self.assertRaises(ValueError):
            FrameMetadata(frame_index=0, timestamp=0.0, width=1280, height=-50)
        with self.assertRaises(ValueError):
            FrameMetadata(frame_index=0, timestamp=0.0, width=True, height=720)


class TestPipelineResult(unittest.TestCase):
    """Test suite for PipelineResult container."""

    def test_pipeline_result_structure(self) -> None:
        """Verify PipelineResult packaging and serialization."""
        meta = FrameMetadata(frame_index=0, timestamp=0.0, width=1280, height=720)
        bbox = BoundingBox(x1=10, y1=20, x2=50, y2=100)
        det = Detection(class_name="person", confidence=0.95, bbox=bbox)

        res = PipelineResult(
            metadata=meta,
            detections=(det,),
            processed=True,
            status_message="OK",
        )

        self.assertEqual(len(res.detections), 1)
        self.assertTrue(res.processed)
        res_dict = res.to_dict()
        self.assertEqual(len(res_dict["detections"]), 1)
        self.assertEqual(res_dict["status_message"], "OK")


if __name__ == "__main__":
    unittest.main()
