"""Person detection module for SentinelAI Computer Vision Engine.

Provides detector adapters implementing IDetector:
- YOLOPersonDetector: Lightweight pretrained object detector using Ultralytics YOLO
  (e.g., YOLOv8n), strictly filtering for person class (COCO class 0).
- MockPersonDetector: Predictable, network-free detector for deterministic automated tests.
- Factory function create_detector(config) for clean component instantiation.

Note on Confidence Scores:
Detection confidence reflects statistical model certainty only. It is NOT a threat
probability or risk score. Risk assessment is strictly computed by the backend service.
"""

import math
from typing import Any, Dict, List, Optional, Sequence, Union

from sentinel_cv.config import CVConfig, ConfigurationError
from sentinel_cv.interfaces import IDetector
from sentinel_cv.logging_config import get_logger
from sentinel_cv.models import BoundingBox, Detection, FrameMetadata

logger = get_logger("detector")


class ModelLoadingError(RuntimeError):
    """Raised when an object detection model fails to load."""
    pass


class MockPersonDetector(IDetector):
    """Deterministic mock detector for testing and offline execution.

    Allows injecting predefined detections per frame index or returning
    a static list of detections without requiring model downloads or GPU/CPU weights.
    """

    def __init__(
        self,
        canned_detections: Optional[Dict[int, List[Detection]]] = None,
        default_detections: Optional[List[Detection]] = None,
        ready: bool = True,
    ) -> None:
        """Initialize mock detector.

        Args:
            canned_detections: Mapping from frame_index to List[Detection].
            default_detections: Fallback list of detections for any frame.
            ready: Initial ready state flag.
        """
        self._canned: Dict[int, List[Detection]] = canned_detections or {}
        self._default: List[Detection] = default_detections or []
        self._ready: bool = ready

    def is_ready(self) -> bool:
        """Check whether mock detector is ready."""
        return self._ready

    def set_ready(self, ready: bool) -> None:
        """Set ready state for testing error handling."""
        self._ready = ready

    def detect(self, frame: Any, metadata: FrameMetadata) -> List[Detection]:
        """Return predefined detections matching metadata.frame_index."""
        if not self._ready:
            raise ModelLoadingError("Mock detector is not ready.")

        if metadata.frame_index in self._canned:
            return list(self._canned[metadata.frame_index])
        return list(self._default)


class YOLOPersonDetector(IDetector):
    """Pretrained person detector utilizing Ultralytics YOLO.

    Enforces:
    - Lazy loading and single-instance model caching.
    - Strict class filtering (retaining ONLY person class detections).
    - Validation and boundary clamping of bounding box coordinates.
    - Strict threshold filtering on confidence scores.
    """

    DEFAULT_MODEL = "yolov8n.pt"
    COCO_PERSON_CLASS_ID = 0
    COCO_PERSON_CLASS_NAME = "person"

    def __init__(
        self,
        model_name_or_path: Optional[str] = None,
        confidence_threshold: float = 0.50,
        device: str = "cpu",
        person_class_name: str = "person",
        person_class_id: Optional[int] = 0,
    ) -> None:
        """Initialize YOLO person detector adapter.

        Args:
            model_name_or_path: Name or local path to YOLO weights (defaults to 'yolov8n.pt').
            confidence_threshold: Minimum confidence score [0.0, 1.0].
            device: Compute device ('cpu', 'cuda', etc. Default 'cpu' for LinuxONE/laptop safety).
            person_class_name: Name of target class (default 'person').
            person_class_id: Class index in model's class mapping (default 0 for COCO).
        """
        self.model_name_or_path: str = model_name_or_path or self.DEFAULT_MODEL
        if not math.isfinite(confidence_threshold) or not (0.0 <= confidence_threshold <= 1.0):
            raise ValueError(f"confidence_threshold must be between 0.0 and 1.0, got {confidence_threshold}")
        self.confidence_threshold: float = float(confidence_threshold)
        self.device: str = device
        self.person_class_name: str = person_class_name
        self.person_class_id: Optional[int] = person_class_id

        self._model: Optional[Any] = None
        self._is_loaded: bool = False

    def is_ready(self) -> bool:
        """Check whether the model weights and runtime are loaded."""
        return self._is_loaded and self._model is not None

    def load_model(self) -> None:
        """Load the YOLO model weights into memory.

        Raises:
            ModelLoadingError: If ultralytics is missing or model fails to load.
        """
        if self._is_loaded and self._model is not None:
            return

        try:
            from ultralytics import YOLO
        except ImportError as err:
            raise ModelLoadingError(
                "Ultralytics package is not installed. "
                "Install with 'pip install ultralytics' or configure a different detector."
            ) from err

        logger.info(
            "Loading YOLO detector model: %s on device: %s (confidence threshold: %.2f)",
            self.model_name_or_path,
            self.device,
            self.confidence_threshold,
        )

        try:
            self._model = YOLO(self.model_name_or_path)
            # Verify and adapt person class identifier if model exposes names dict
            if hasattr(self._model, "names") and isinstance(self._model.names, dict):
                names_dict = self._model.names
                # Find matching key for person_class_name
                matched_id = None
                for cid, cname in names_dict.items():
                    if str(cname).lower() == self.person_class_name.lower():
                        matched_id = int(cid)
                        break
                if matched_id is not None:
                    self.person_class_id = matched_id
                    logger.debug("Resolved '%s' class ID to %d in model dictionary.", self.person_class_name, matched_id)
                elif self.person_class_id is None:
                    self.person_class_id = self.COCO_PERSON_CLASS_ID

            self._is_loaded = True
            logger.info("YOLO model loaded successfully.")
        except Exception as load_err:
            self._model = None
            self._is_loaded = False
            raise ModelLoadingError(
                f"Failed to load YOLO model '{self.model_name_or_path}': {load_err}"
            ) from load_err

    def detect(self, frame: Any, metadata: FrameMetadata) -> List[Detection]:
        """Perform person detection on a frame image array.

        Args:
            frame: Raw image array (e.g. numpy array).
            metadata: Associated FrameMetadata.

        Returns:
            List[Detection]: Validated person detections with BoundingBox.
        """
        if not self._is_loaded or self._model is None:
            self.load_model()

        if frame is None:
            return []

        try:
            # Run inference without console spam, using configured device and threshold
            results = self._model(
                frame,
                verbose=False,
                conf=self.confidence_threshold,
                device=self.device,
            )
        except Exception as infer_err:
            logger.error("Inference failure on frame %d: %s", metadata.frame_index, infer_err)
            raise RuntimeError(f"Detector inference failed on frame {metadata.frame_index}: {infer_err}") from infer_err

        if not results or len(results) == 0:
            return []

        boxes_obj = getattr(results[0], "boxes", None)
        if boxes_obj is None or len(boxes_obj) == 0:
            return []

        detections: List[Detection] = []
        target_class_id = self.person_class_id if self.person_class_id is not None else self.COCO_PERSON_CLASS_ID

        for box in boxes_obj:
            # 1. Class filter: retain ONLY the person class
            try:
                raw_cls = box.cls[0]
                cls_id = int(raw_cls.item() if hasattr(raw_cls, "item") else raw_cls)
            except (AttributeError, IndexError, TypeError):
                continue

            if cls_id != target_class_id:
                # Discard non-person classes (e.g., vehicles, animals, objects)
                continue

            # 2. Confidence filter
            try:
                raw_conf = box.conf[0]
                conf = float(raw_conf.item() if hasattr(raw_conf, "item") else raw_conf)
            except (AttributeError, IndexError, TypeError):
                continue

            if not math.isfinite(conf) or conf < self.confidence_threshold:
                continue
            conf = min(1.0, max(0.0, conf))

            # 3. Bounding box coordinates [x1, y1, x2, y2]
            try:
                raw_xyxy = box.xyxy[0]
                xyxy_list = raw_xyxy.tolist() if hasattr(raw_xyxy, "tolist") else list(raw_xyxy)
                raw_x1, raw_y1, raw_x2, raw_y2 = (
                    float(xyxy_list[0]),
                    float(xyxy_list[1]),
                    float(xyxy_list[2]),
                    float(xyxy_list[3]),
                )
            except (AttributeError, IndexError, TypeError, ValueError):
                continue

            # Clamp coordinates to frame dimensions
            clamped_x1 = max(0.0, min(float(metadata.width), raw_x1))
            clamped_y1 = max(0.0, min(float(metadata.height), raw_y1))
            clamped_x2 = max(0.0, min(float(metadata.width), raw_x2))
            clamped_y2 = max(0.0, min(float(metadata.height), raw_y2))

            # Guard against invalid box geometry
            if clamped_x2 <= clamped_x1 or clamped_y2 <= clamped_y1:
                logger.debug(
                    "Skipping degraded bounding box on frame %d: (%.1f, %.1f, %.1f, %.1f)",
                    metadata.frame_index,
                    clamped_x1,
                    clamped_y1,
                    clamped_x2,
                    clamped_y2,
                )
                continue

            try:
                bbox = BoundingBox(
                    x1=clamped_x1,
                    y1=clamped_y1,
                    x2=clamped_x2,
                    y2=clamped_y2,
                )
            except ValueError as bbox_err:
                logger.debug("BoundingBox validation rejected box: %s", bbox_err)
                continue

            # Optional tracking ID
            track_id = None
            if hasattr(box, "id") and box.id is not None:
                try:
                    raw_id = box.id[0]
                    track_id = int(raw_id.item() if hasattr(raw_id, "item") else raw_id)
                except (IndexError, TypeError, ValueError):
                    track_id = None

            detection = Detection(
                class_name=self.person_class_name,
                confidence=conf,
                bbox=bbox,
                track_id=track_id,
            )
            detections.append(detection)

        return detections


def create_detector(config: CVConfig) -> IDetector:
    """Factory creating an IDetector based on CVConfig.

    Args:
        config: CVConfig containing model_type, model_path, confidence_threshold.

    Returns:
        IDetector: Instantiated detector adapter.
    """
    model_type = config.model_type.strip().lower()

    if model_type in {"mock", "test"}:
        logger.info("Instantiating MockPersonDetector for testing/offline mode.")
        return MockPersonDetector()

    if model_type in {"yolo", "yolov8", "ultralytics", "placeholder"}:
        # In Phase 2, default placeholder or yolo maps to YOLOPersonDetector
        model_target = config.model_path or YOLOPersonDetector.DEFAULT_MODEL
        logger.info("Instantiating YOLOPersonDetector with target: %s", model_target)
        return YOLOPersonDetector(
            model_name_or_path=model_target,
            confidence_threshold=config.confidence_threshold,
        )

    raise ConfigurationError(
        f"Unsupported model_type '{config.model_type}'. Supported: 'yolo', 'mock'."
    )
