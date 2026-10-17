"""Restricted-zone geometry representation and person-versus-zone analysis.

Provides:
- PolygonZone: Validated 2D polygonal restricted zone with zero-dependency ray casting.
- ZoneAnalyzer: Evaluates person detections against configured restricted zones using
  approximated ground-plane foot contact (bottom-center) or bounding-box center.
- Pure Python computational geometry ensuring 100% architecture neutrality across
  x86-64, ARM64, and IBM LinuxONE (s390x) environments.

Note on Human-in-the-Loop Monitoring:
Restricted-zone entry is an observable geometric condition. It does NOT constitute
evidence of malicious intent or automated criminality classification.
Risk scoring and explanation reasons are strictly owned by the backend per API_CONTRACT.md.
"""

from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from sentinel_cv.interfaces import IZoneAnalyzer
from sentinel_cv.logging_config import get_logger
from sentinel_cv.models import Detection, FrameMetadata, ZoneAnalysisResult

logger = get_logger("zone")

EPSILON = 1e-6


def _point_on_segment(
    px: float, py: float, x1: float, y1: float, x2: float, y2: float, eps: float = EPSILON
) -> bool:
    """Check if point (px, py) lies on line segment (x1, y1)-(x2, y2) within eps."""
    # Check bounding box of segment first
    if not (min(x1, x2) - eps <= px <= max(x1, x2) + eps):
        return False
    if not (min(y1, y2) - eps <= py <= max(y1, y2) + eps):
        return False

    # Cross product for collinearity: (py - y1)*(x2 - x1) - (px - x1)*(y2 - y1)
    cross_product = (py - y1) * (x2 - x1) - (px - x1) * (y2 - y1)
    return abs(cross_product) <= eps * max(1.0, abs(x2 - x1), abs(y2 - y1))


@dataclass(frozen=True)
class PolygonZone:
    """Polygonal restricted zone defined in video frame pixel coordinates.

    Attributes:
        zone_id: Stable, unique zone identifier (e.g. 'zone-restricted-01').
        name: Human-readable zone designation (e.g. 'Perimeter North Buffer').
        vertices: Sequence of (x, y) coordinate tuples defining the closed boundary.
        enabled: Whether the zone is active for evaluation.
    """

    zone_id: str
    name: str
    vertices: Tuple[Tuple[float, float], ...]
    enabled: bool = True

    def __post_init__(self) -> None:
        """Validate polygon attributes and geometry."""
        # 1. Validate identifiers
        if not self.zone_id or not str(self.zone_id).strip():
            raise ValueError("zone_id must be a non-empty string.")
        if not self.name or not str(self.name).strip():
            raise ValueError("name must be a non-empty string.")

        # 2. Validate vertex count
        if not isinstance(self.vertices, (list, tuple)) or len(self.vertices) < 3:
            raise ValueError(
                f"PolygonZone must have at least 3 vertices to define an area, got {len(self.vertices) if hasattr(self.vertices, '__len__') else type(self.vertices).__name__}"
            )

        # 3. Validate vertex coordinates
        normalized_vertices: List[Tuple[float, float]] = []
        for i, vertex in enumerate(self.vertices):
            if not isinstance(vertex, (list, tuple)) or len(vertex) != 2:
                raise ValueError(f"Vertex {i} must be a 2-tuple (x, y), got {vertex}")
            vx, vy = vertex
            if not isinstance(vx, (int, float)) or not isinstance(vy, (int, float)) or isinstance(vx, bool) or isinstance(vy, bool):
                raise ValueError(f"Vertex {i} coordinates must be numbers, got ({type(vx).__name__}, {type(vy).__name__})")
            if not math.isfinite(vx) or not math.isfinite(vy):
                raise ValueError(f"Vertex {i} coordinates must be finite numbers, got ({vx}, {vy})")
            if vx < 0.0 or vy < 0.0:
                raise ValueError(f"Vertex {i} coordinates cannot be negative, got ({vx}, {vy})")
            normalized_vertices.append((float(vx), float(vy)))

        object.__setattr__(self, "vertices", tuple(normalized_vertices))

        # 4. Validate non-zero area via Shoelace formula
        area = self._calculate_area()
        if area <= EPSILON:
            raise ValueError(
                f"PolygonZone vertices define a collinear or zero-area polygon (area={area:.6f})."
            )

    def _calculate_area(self) -> float:
        """Calculate polygon area using the Shoelace formula."""
        n = len(self.vertices)
        signed_area = 0.0
        for i in range(n):
            x1, y1 = self.vertices[i]
            x2, y2 = self.vertices[(i + 1) % n]
            signed_area += (x1 * y2) - (x2 * y1)
        return abs(signed_area) / 2.0

    @property
    def area(self) -> float:
        """Area of the polygonal zone in square pixels."""
        return self._calculate_area()

    @property
    def bounding_box(self) -> Tuple[float, float, float, float]:
        """Axis-aligned bounding box (min_x, min_y, max_x, max_y) of the polygon."""
        xs = [v[0] for v in self.vertices]
        ys = [v[1] for v in self.vertices]
        return (min(xs), min(ys), max(xs), max(ys))

    def contains_point(self, point: Tuple[float, float]) -> bool:
        """Determine whether point (px, py) is inside or on the boundary of the polygon.

        Uses Ray-Casting algorithm with boundary tolerance:
        - Points strictly inside the polygon return True.
        - Points strictly outside the polygon return False.
        - Points lying directly on edges or vertices are defined as inside and return True.

        Args:
            point: (px, py) coordinates in frame pixel space.

        Returns:
            bool: True if point is inside or on the boundary, False otherwise.
        """
        if not self.enabled:
            return False

        px, py = point
        if not math.isfinite(px) or not math.isfinite(py):
            return False

        min_x, min_y, max_x, max_y = self.bounding_box

        # Quick rejection using polygon bounding box
        if px < min_x - EPSILON or px > max_x + EPSILON or py < min_y - EPSILON or py > max_y + EPSILON:
            return False

        n = len(self.vertices)
        inside = False

        for i in range(n):
            x1, y1 = self.vertices[i]
            x2, y2 = self.vertices[(i + 1) % n]

            # 1. Boundary check: point on edge
            if _point_on_segment(px, py, x1, y1, x2, y2):
                return True

            # 2. Ray-casting check: ray extending from (px, py) towards +X
            if (y1 > py) != (y2 > py):
                # Calculate X intersection coordinate with horizontal ray at Y = py
                x_intersection = (x2 - x1) * (py - y1) / (y2 - y1) + x1
                if px < x_intersection:
                    inside = not inside

        return inside

    def to_dict(self) -> Dict[str, Any]:
        """Serialize zone configuration to dictionary."""
        return {
            "zone_id": self.zone_id,
            "name": self.name,
            "enabled": self.enabled,
            "vertices": [list(v) for v in self.vertices],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolygonZone":
        """Deserialize zone configuration from dictionary."""
        raw_vertices = data.get("vertices", [])
        vertices = tuple((float(v[0]), float(v[1])) for v in raw_vertices)
        return cls(
            zone_id=str(data.get("zone_id", "")),
            name=str(data.get("name", "")),
            vertices=vertices,
            enabled=bool(data.get("enabled", True)),
        )


class ZoneAnalyzer(IZoneAnalyzer):
    """Evaluates person detections against configured polygonal restricted zones.

    Attributes:
        zones: List of configured PolygonZone instances.
        reference_point_strategy: Strategy for mapping detection box to a 2D point.
                                  Options: 'bottom_center' (default) or 'center'.
    """

    VALID_STRATEGIES = {"bottom_center", "center"}

    def __init__(
        self,
        zones: Optional[Sequence[PolygonZone]] = None,
        reference_point_strategy: str = "bottom_center",
    ) -> None:
        """Initialize zone analyzer.

        Args:
            zones: Sequence of PolygonZone definitions.
            reference_point_strategy: 'bottom_center' (ground plane) or 'center'.
        """
        self.zones: List[PolygonZone] = list(zones) if zones is not None else []

        strategy = reference_point_strategy.strip().lower()
        if strategy not in self.VALID_STRATEGIES:
            raise ValueError(
                f"Invalid reference_point_strategy '{reference_point_strategy}'. "
                f"Must be one of: {sorted(self.VALID_STRATEGIES)}"
            )
        self.reference_point_strategy: str = strategy

        logger.info(
            "ZoneAnalyzer initialized with %d zone(s) | Strategy: %s",
            len(self.zones),
            self.reference_point_strategy,
        )

    def get_reference_point(self, detection: Detection) -> Tuple[float, float]:
        """Compute evaluation reference point for a detection based on strategy.

        Args:
            detection: Detection instance with validated BoundingBox.

        Returns:
            Tuple[float, float]: (x, y) reference coordinates.
        """
        if self.reference_point_strategy == "center":
            return detection.bbox.center
        # Default: bottom-center (ground plane contact point)
        return detection.bbox.bottom_center

    def evaluate(
        self, detections: List[Detection], metadata: FrameMetadata
    ) -> List[ZoneAnalysisResult]:
        """Evaluate all detections against all enabled zones in the current frame.

        Args:
            detections: List of validated Detection instances in the frame.
            metadata: Associated FrameMetadata.

        Returns:
            List[ZoneAnalysisResult]: Assessment result for each detection-zone pair.
        """
        results: List[ZoneAnalysisResult] = []
        enabled_zones = [z for z in self.zones if z.enabled]

        if not enabled_zones or not detections:
            return results

        for detection in detections:
            ref_pt = self.get_reference_point(detection)

            for zone in enabled_zones:
                is_inside = zone.contains_point(ref_pt)

                res = ZoneAnalysisResult(
                    detection=detection,
                    frame_index=metadata.frame_index,
                    timestamp=metadata.timestamp,
                    zone_id=zone.zone_id,
                    zone_name=zone.name,
                    is_inside=is_inside,
                    reference_point=ref_pt,
                    detection_confidence=detection.confidence,
                )
                results.append(res)

        return results

    def evaluate_inside(
        self, detections: List[Detection], metadata: FrameMetadata
    ) -> List[ZoneAnalysisResult]:
        """Convenience method returning ONLY detections that are inside enabled zones."""
        all_results = self.evaluate(detections, metadata)
        return [r for r in all_results if r.is_inside]
