"""Automated tests for person detector adapters (YOLOPersonDetector, MockPersonDetector)."""

from typing import Any, List
import unittest
from unittest.mock import MagicMock, patch

from sentinel_cv.config import CVConfig, ConfigurationError
from sentinel_cv.detector import (
    MockPersonDetector,
    ModelLoadingError,
    YOLOPersonDetector,
    create_detector,
)
from sentinel_cv.models import BoundingBox, Detection, FrameMetadata


class MockYOLOBox:
    """Mock Ultralytics Results.boxes element."""

    def __init__(self, cls_id: int, conf: float, xyxy: List[float], track_id: Any = None) -> None:
        self.cls = [cls_id]
        self.conf = [conf]
        self.xyxy = [xyxy]
        self.id = [track_id] if track_id is not None else None


class TestMockPersonDetector(unittest.TestCase):
    """Test suite for MockPersonDetector."""

    def setUp(self) -> None:
        self.meta = FrameMetadata(frame_index=1, timestamp=0.1, width=1280, height=720)
        self.bbox = BoundingBox(x1=10.0, y1=20.0, x2=50.0, y2=100.0)
        self.sample_detection = Detection(class_name="person", confidence=0.9, bbox=self.bbox)

    def test_mock_detector_readiness_and_error(self) -> None:
        """Verify readiness flag and error when not ready."""
        detector = MockPersonDetector(ready=True)
        self.assertTrue(detector.is_ready())

        detector.set_ready(False)
        self.assertFalse(detector.is_ready())
        with self.assertRaises(ModelLoadingError):
            detector.detect(frame=None, metadata=self.meta)

    def test_canned_detections_routing(self) -> None:
        """Verify canned detections return based on frame_index."""
        detector = MockPersonDetector(
            canned_detections={1: [self.sample_detection]},
            default_detections=[],
        )

        # Frame 1 has detection
        dets1 = detector.detect(frame=None, metadata=self.meta)
        self.assertEqual(len(dets1), 1)
        self.assertEqual(dets1[0].confidence, 0.9)

        # Frame 2 has no detection
        meta2 = FrameMetadata(frame_index=2, timestamp=0.2, width=1280, height=720)
        dets2 = detector.detect(frame=None, metadata=meta2)
        self.assertEqual(len(dets2), 0)


class TestYOLOPersonDetector(unittest.TestCase):
    """Test suite for YOLOPersonDetector filtering, validation, and loading."""

    def setUp(self) -> None:
        self.meta = FrameMetadata(frame_index=0, timestamp=0.0, width=1000, height=800)

    def test_invalid_confidence_threshold_raises_value_error(self) -> None:
        """Verify invalid confidence thresholds raise ValueError."""
        with self.assertRaises(ValueError):
            YOLOPersonDetector(confidence_threshold=-0.1)
        with self.assertRaises(ValueError):
            YOLOPersonDetector(confidence_threshold=1.1)
        with self.assertRaises(ValueError):
            YOLOPersonDetector(confidence_threshold=float("nan"))

    def test_model_loading_failure_raises_model_loading_error(self) -> None:
        """Verify attempting to load an invalid model file raises ModelLoadingError."""
        detector = YOLOPersonDetector(model_name_or_path="completely_invalid_path/model.pt")
        with self.assertRaises(ModelLoadingError):
            detector.load_model()

    def test_detect_filters_non_person_classes(self) -> None:
        """Verify only class 0 (person) is retained, while cars/dogs/etc. are filtered out."""
        detector = YOLOPersonDetector(confidence_threshold=0.50)

        # Build mock boxes:
        # Box 0: person (cls=0), conf=0.85 -> KEEP
        # Box 1: car (cls=2), conf=0.92 -> DISCARD
        # Box 2: dog (cls=16), conf=0.78 -> DISCARD
        # Box 3: person (cls=0), conf=0.35 (below 0.50 threshold) -> DISCARD
        box_person = MockYOLOBox(cls_id=0, conf=0.85, xyxy=[100.0, 150.0, 200.0, 350.0], track_id=5)
        box_car = MockYOLOBox(cls_id=2, conf=0.92, xyxy=[300.0, 400.0, 600.0, 600.0])
        box_dog = MockYOLOBox(cls_id=16, conf=0.78, xyxy=[50.0, 50.0, 120.0, 120.0])
        box_low_conf = MockYOLOBox(cls_id=0, conf=0.35, xyxy=[10.0, 20.0, 30.0, 40.0])

        mock_results = [MagicMock(boxes=[box_person, box_car, box_dog, box_low_conf])]
        mock_model = MagicMock(return_value=mock_results)
        mock_model.names = {0: "person", 2: "car", 16: "dog"}

        # Inject mock model
        detector._model = mock_model
        detector._is_loaded = True

        detections = detector.detect(frame="fake_image", metadata=self.meta)

        self.assertEqual(len(detections), 1)
        det = detections[0]
        self.assertEqual(det.class_name, "person")
        self.assertAlmostEqual(det.confidence, 0.85)
        self.assertEqual(det.track_id, 5)
        self.assertEqual(det.bbox.x1, 100.0)
        self.assertEqual(det.bbox.y1, 150.0)
        self.assertEqual(det.bbox.x2, 200.0)
        self.assertEqual(det.bbox.y2, 350.0)

    def test_detect_boundary_clamping(self) -> None:
        """Verify coordinates outside [0, width] / [0, height] are clamped safely."""
        detector = YOLOPersonDetector(confidence_threshold=0.50)

        # Box extending past frame boundaries: [-10, -5, 1050, 850]
        box_overflow = MockYOLOBox(cls_id=0, conf=0.90, xyxy=[-10.0, -5.0, 1050.0, 850.0])
        mock_results = [MagicMock(boxes=[box_overflow])]
        mock_model = MagicMock(return_value=mock_results)
        detector._model = mock_model
        detector._is_loaded = True

        detections = detector.detect(frame="fake_image", metadata=self.meta)

        self.assertEqual(len(detections), 1)
        bbox = detections[0].bbox
        self.assertEqual(bbox.x1, 0.0)
        self.assertEqual(bbox.y1, 0.0)
        self.assertEqual(bbox.x2, 1000.0)
        self.assertEqual(bbox.y2, 800.0)

    def test_detect_empty_or_none_frame(self) -> None:
        """Verify None frame returns empty list."""
        detector = YOLOPersonDetector()
        detector._is_loaded = True
        detector._model = MagicMock()
        dets = detector.detect(frame=None, metadata=self.meta)
        self.assertEqual(dets, [])


class TestCreateDetectorFactory(unittest.TestCase):
    """Test suite for create_detector factory function."""

    def test_create_mock_detector(self) -> None:
        """Verify factory creates MockPersonDetector for model_type='mock'."""
        cfg = CVConfig(model_type="mock")
        detector = create_detector(cfg)
        self.assertIsInstance(detector, MockPersonDetector)

    def test_create_yolo_detector(self) -> None:
        """Verify factory creates YOLOPersonDetector for model_type='yolo'."""
        cfg = CVConfig(model_type="yolo", model_path="custom_weights.pt", confidence_threshold=0.65)
        detector = create_detector(cfg)
        self.assertIsInstance(detector, YOLOPersonDetector)
        self.assertEqual(detector.model_name_or_path, "custom_weights.pt")
        self.assertEqual(detector.confidence_threshold, 0.65)

    def test_create_unsupported_detector_raises_config_error(self) -> None:
        """Verify factory raises ConfigurationError on unknown model types."""
        cfg = CVConfig(model_type="invalid_framework")
        with self.assertRaises(ConfigurationError):
            create_detector(cfg)


class TestRealYOLOInference(unittest.TestCase):
    """Integration test suite for genuine YOLOv8 person detector execution.

    Distinguishes genuine neural network inference from mock/replay canned outputs.
    Tests model loading, real person detection, empty frame behavior, and zone analysis.
    """

    @classmethod
    def setUpClass(cls) -> None:
        import os
        cls.ultralytics_available = False
        cls.weights_path = None

        try:
            import ultralytics
            cls.ultralytics_available = True
            # Check potential locations for weights
            for candidate in ("yolov8n.pt", "cv-engine/yolov8n.pt", "../yolov8n.pt"):
                if os.path.exists(candidate):
                    cls.weights_path = os.path.abspath(candidate)
                    break
            cls.bus_img_path = os.path.join(os.path.dirname(ultralytics.__file__), "assets", "bus.jpg")
        except ImportError:
            pass

    def setUp(self) -> None:
        if not self.ultralytics_available or not self.weights_path:
            self.skipTest("Ultralytics or yolov8n.pt weights not available in this environment.")

    def test_real_yolo_model_loading(self) -> None:
        """Verify real YOLO model loads from disk and resolves class names dictionary."""
        detector = YOLOPersonDetector(model_name_or_path=self.weights_path, confidence_threshold=0.50)
        self.assertFalse(detector.is_ready())
        detector.load_model()
        self.assertTrue(detector.is_ready())
        self.assertEqual(detector.person_class_id, 0)
        self.assertEqual(detector.person_class_name, "person")

    def test_real_yolo_detects_person_in_image(self) -> None:
        """Verify real YOLO inference detects real persons with valid bboxes and confidence."""
        import cv2
        frame = cv2.imread(self.bus_img_path)
        self.assertIsNotNone(frame, "Failed to read test image bus.jpg")
        h, w = frame.shape[:2]
        meta = FrameMetadata(frame_index=0, timestamp=0.0, width=w, height=h)

        detector = YOLOPersonDetector(model_name_or_path=self.weights_path, confidence_threshold=0.50)
        detector.load_model()
        detections = detector.detect(frame, meta)

        self.assertGreaterEqual(len(detections), 1, "Real YOLO should detect at least 1 person in bus.jpg")
        for det in detections:
            self.assertEqual(det.class_name, "person")
            self.assertGreaterEqual(det.confidence, 0.50)
            self.assertLessEqual(det.confidence, 1.0)
            # Verify coordinates are valid and bounded
            self.assertGreaterEqual(det.bbox.x1, 0.0)
            self.assertGreaterEqual(det.bbox.y1, 0.0)
            self.assertLessEqual(det.bbox.x2, float(w))
            self.assertLessEqual(det.bbox.y2, float(h))
            self.assertLess(det.bbox.x1, det.bbox.x2)
            self.assertLess(det.bbox.y1, det.bbox.y2)

    def test_real_yolo_blank_frame_returns_zero_detections(self) -> None:
        """Verify real YOLO does NOT invent detections on a blank frame (distinguishing from mock)."""
        import numpy as np
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        meta = FrameMetadata(frame_index=0, timestamp=0.0, width=640, height=480)

        detector = YOLOPersonDetector(model_name_or_path=self.weights_path, confidence_threshold=0.50)
        detector.load_model()
        detections = detector.detect(blank_frame, meta)

        self.assertEqual(len(detections), 0, "Real YOLO must return 0 detections on blank frame")

    def test_real_yolo_zone_incursion_and_rejection(self) -> None:
        """Verify real detections connected to ZoneAnalyzer distinguish zone incursion from outside persons."""
        import cv2
        from sentinel_cv.zone import ZoneAnalyzer
        from sentinel_cv.config import CVConfig

        frame = cv2.resize(cv2.imread(self.bus_img_path), (1280, 720))
        meta = FrameMetadata(frame_index=0, timestamp=0.0, width=1280, height=720)

        cfg = CVConfig()
        analyzer = ZoneAnalyzer(zones=cfg.get_configured_zones(), reference_point_strategy="bottom_center")
        detector = YOLOPersonDetector(model_name_or_path=self.weights_path, confidence_threshold=0.50)
        detector.load_model()

        detections = detector.detect(frame, meta)
        results = analyzer.evaluate(detections, meta)

        self.assertEqual(len(results), len(detections))
        inside_count = sum(1 for r in results if r.is_inside)
        outside_count = sum(1 for r in results if not r.is_inside)

        # In 1280x720 resized bus.jpg, exactly 1 person is inside the central zone and 3 are outside
        self.assertGreaterEqual(inside_count, 1, "At least one person should be inside central zone")
        self.assertGreaterEqual(outside_count, 1, "At least one person should be outside central zone")


if __name__ == "__main__":
    unittest.main()

