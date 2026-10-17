"""Shared Computer Vision data models for SentinelAI.

Defines validated data structures for bounding boxes, detections, frame
metadata, zone analysis results, and pipeline outputs.

Important architectural boundary:
Detector confidence reflects the statistical certainty of the visual detector
model only. It does NOT represent threat intent or overall risk score.
Risk scoring and explanation reasons are strictly computed by the backend
service per API_CONTRACT.md.
"""

from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class BoundingBox:
    """Axis-aligned bounding box representation in pixel coordinates.

    Coordinates represent:
        (x1, y1): Top-left corner
        (x2, y2): Bottom-right corner

    Requirements:
        - All coordinates must be finite non-negative numbers.
        - x2 must be strictly greater than x1.
        - y2 must be strictly greater than y1.
    """

    x1: float
    y1: float
    x2: float
    y2: float

    def __post_init__(self) -> None:
        """Validate bounding box coordinates."""
        coords = {"x1": self.x1, "y1": self.y1, "x2": self.x2, "y2": self.y2}

        # Check types and finite values
        for name, val in coords.items():
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                raise ValueError(f"BoundingBox {name} must be a numeric type, got {type(val).__name__}")
            if not math.isfinite(val):
                raise ValueError(f"BoundingBox {name} must be a finite number, got {val}")
            if val < 0.0:
                raise ValueError(f"BoundingBox {name} cannot be negative, got {val}")

        # Check geometry
        if self.x2 <= self.x1:
            raise ValueError(
                f"Invalid horizontal bounds: x2 ({self.x2}) must be strictly greater than x1 ({self.x1})"
            )
        if self.y2 <= self.y1:
            raise ValueError(
                f"Invalid vertical bounds: y2 ({self.y2}) must be strictly greater than y1 ({self.y1})"
            )

    @property
    def width(self) -> float:
        """Width of the bounding box."""
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        """Height of the bounding box."""
        return self.y2 - self.y1

    @property
    def area(self) -> float:
        """Area of the bounding box in pixels squared."""
        return self.width * self.height

    @property
    def center(self) -> Tuple[float, float]:
        """Geometric centroid (cx, cy) of the bounding box."""
        return (self.x1 + self.width / 2.0, self.y1 + self.height / 2.0)

    @property
    def bottom_center(self) -> Tuple[float, float]:
        """Footprint / ground-plane contact point (bottom center).

        In CCTV surveillance, the bottom center of a detected person represents
        their contact with the ground plane, which is the most reliable anchor
        for polygonal zone-intersection checks.
        """
        return (self.x1 + self.width / 2.0, self.y2)

    def as_tuple(self) -> Tuple[float, float, float, float]:
        """Return coordinates as (x1, y1, x2, y2)."""
        return (self.x1, self.y1, self.x2, self.y2)

    def as_dict(self) -> Dict[str, float]:
        """Return coordinates as a dictionary."""
        return {"x1": self.x1, "y1": self.y1, "x2": self.x2, "y2": self.y2}


@dataclass(frozen=True)
class Detection:
    """A detected object in a video frame.

    Attributes:
        class_name: Detected object class (e.g., 'person', 'vehicle').
        confidence: Detector confidence score strictly within [0.0, 1.0].
        bbox: Validated BoundingBox instance.
        track_id: Optional persistent object tracking identifier.

    Note:
        confidence is the statistical confidence of the detector.
        It is NOT a risk score or malicious intent probability.
    """

    class_name: str
    confidence: float
    bbox: BoundingBox
    track_id: Optional[int] = None

    def __post_init__(self) -> None:
        """Validate detection fields."""
        if not isinstance(self.class_name, str) or not self.class_name.strip():
            raise ValueError("Detection class_name must be a non-empty string.")

        if (
            not isinstance(self.confidence, (int, float))
            or isinstance(self.confidence, bool)
            or not math.isfinite(self.confidence)
        ):
            raise ValueError(f"Detection confidence must be a finite number, got {self.confidence}")

        if not (0.0 <= float(self.confidence) <= 1.0):
            raise ValueError(
                f"Detection confidence must be between 0.0 and 1.0 inclusive, got {self.confidence}"
            )

        if not isinstance(self.bbox, BoundingBox):
            raise ValueError(f"Detection bbox must be an instance of BoundingBox, got {type(self.bbox).__name__}")

        if self.track_id is not None:
            if not isinstance(self.track_id, int) or isinstance(self.track_id, bool) or self.track_id < 0:
                raise ValueError(f"track_id must be a non-negative integer or None, got {self.track_id}")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize detection for evidence payloads."""
        return {
            "class_name": self.class_name,
            "confidence": round(float(self.confidence), 4),
            "bbox": self.bbox.as_dict(),
            "track_id": self.track_id,
        }


@dataclass(frozen=True)
class FrameMetadata:
    """Metadata describing a single processed video frame.

    Attributes:
        frame_index: Zero-based sequential frame counter (non-negative).
        timestamp: Elapsed video time in seconds or presentation timestamp (non-negative).
        width: Frame width in pixels (> 0).
        height: Frame height in pixels (> 0).
        source_id: Optional camera or stream identifier.
    """

    frame_index: int
    timestamp: float
    width: int
    height: int
    source_id: str = ""

    def __post_init__(self) -> None:
        """Validate frame metadata fields."""
        if not isinstance(self.frame_index, int) or isinstance(self.frame_index, bool) or self.frame_index < 0:
            raise ValueError(f"frame_index must be a non-negative integer, got {self.frame_index}")

        if (
            not isinstance(self.timestamp, (int, float))
            or isinstance(self.timestamp, bool)
            or not math.isfinite(self.timestamp)
            or self.timestamp < 0.0
        ):
            raise ValueError(f"timestamp must be a finite non-negative number, got {self.timestamp}")

        if not isinstance(self.width, int) or isinstance(self.width, bool) or self.width <= 0:
            raise ValueError(f"width must be a positive integer, got {self.width}")

        if not isinstance(self.height, int) or isinstance(self.height, bool) or self.height <= 0:
            raise ValueError(f"height must be a positive integer, got {self.height}")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize metadata for logging or evidence structures."""
        return {
            "frame_index": self.frame_index,
            "timestamp": round(float(self.timestamp), 3),
            "width": self.width,
            "height": self.height,
            "source_id": self.source_id,
        }


@dataclass(frozen=True)
class ZoneAnalysisResult:
    """Structured assessment of a detected person against a restricted zone.

    Attributes:
        detection: Source Detection instance.
        frame_index: Sequence frame index.
        timestamp: Elapsed video timestamp in seconds.
        zone_id: Stable identifier of the evaluated zone.
        zone_name: Human-readable name of the evaluated zone.
        is_inside: True if detection reference point is inside/on the zone boundary.
        reference_point: (x, y) coordinates evaluated (e.g. bottom-center).
        detection_confidence: Statistical confidence of the visual detector.
    """

    detection: Detection
    frame_index: int
    timestamp: float
    zone_id: str
    zone_name: str
    is_inside: bool
    reference_point: Tuple[float, float]
    detection_confidence: float

    def __post_init__(self) -> None:
        """Validate zone analysis result fields."""
        if not isinstance(self.frame_index, int) or isinstance(self.frame_index, bool) or self.frame_index < 0:
            raise ValueError(f"frame_index must be a non-negative integer, got {self.frame_index}")

        if (
            not isinstance(self.timestamp, (int, float))
            or isinstance(self.timestamp, bool)
            or not math.isfinite(self.timestamp)
            or self.timestamp < 0.0
        ):
            raise ValueError(f"timestamp must be a non-negative finite number, got {self.timestamp}")

        if not self.zone_id or not str(self.zone_id).strip():
            raise ValueError("zone_id must be a non-empty string.")

        if not isinstance(self.reference_point, tuple) or len(self.reference_point) != 2:
            raise ValueError(f"reference_point must be a 2-tuple of (x, y), got {self.reference_point}")

        rx, ry = self.reference_point
        if not (math.isfinite(rx) and math.isfinite(ry)):
            raise ValueError(f"reference_point coordinates must be finite numbers, got {self.reference_point}")

        if (
            not isinstance(self.detection_confidence, (int, float))
            or isinstance(self.detection_confidence, bool)
            or not math.isfinite(self.detection_confidence)
            or not (0.0 <= float(self.detection_confidence) <= 1.0)
        ):
            raise ValueError(f"detection_confidence must be in [0.0, 1.0], got {self.detection_confidence}")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize zone analysis result to dictionary."""
        return {
            "zone_id": self.zone_id,
            "zone_name": self.zone_name,
            "is_inside": self.is_inside,
            "frame_index": self.frame_index,
            "timestamp": round(float(self.timestamp), 3),
            "reference_point": (round(self.reference_point[0], 2), round(self.reference_point[1], 2)),
            "detection_confidence": round(float(self.detection_confidence), 4),
            "detection": self.detection.to_dict(),
        }


@dataclass(frozen=True)
class PipelineResult:
    """Predictable container for pipeline frame processing results.

    Attributes:
        metadata: FrameMetadata associated with the frame.
        detections: Tuple of Detection instances found in the frame.
        zone_results: Tuple of ZoneAnalysisResult instances for the frame.
        processed: Whether the frame was actively analyzed.
        status_message: Informative status or diagnostic message.
    """

    metadata: FrameMetadata
    detections: Tuple[Detection, ...] = field(default_factory=tuple)
    zone_results: Tuple[ZoneAnalysisResult, ...] = field(default_factory=tuple)
    processed: bool = False
    status_message: str = "Initialized"

    @property
    def inside_zone_results(self) -> Tuple[ZoneAnalysisResult, ...]:
        """Return only the zone results where detections are actively inside a zone."""
        return tuple(r for r in self.zone_results if r.is_inside)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize pipeline result to dictionary."""
        return {
            "metadata": self.metadata.to_dict(),
            "detections": [d.to_dict() for d in self.detections],
            "zone_results": [z.to_dict() for z in self.zone_results],
            "inside_zone_count": len(self.inside_zone_results),
            "processed": self.processed,
            "status_message": self.status_message,
        }
