"""Automated tests for PolygonZone geometry and ZoneAnalyzer person-versus-zone analysis."""

import math
import unittest

from sentinel_cv.models import BoundingBox, Detection, FrameMetadata, ZoneAnalysisResult
from sentinel_cv.zone import PolygonZone, ZoneAnalyzer


class TestPolygonZone(unittest.TestCase):
    """Test suite for PolygonZone geometry representation and validation."""

    def setUp(self) -> None:
        # Standard rectangular zone: (100, 100) to (400, 300)
        self.rect_vertices = (
            (100.0, 100.0),
            (400.0, 100.0),
            (400.0, 300.0),
            (100.0, 300.0),
        )
        self.zone = PolygonZone(
            zone_id="zone-01",
            name="Test Buffer Zone",
            vertices=self.rect_vertices,
        )

    def test_valid_polygon_zone_properties(self) -> None:
        """Verify initialization, calculated area, and bounding box."""
        self.assertEqual(self.zone.zone_id, "zone-01")
        self.assertEqual(self.zone.name, "Test Buffer Zone")
        self.assertTrue(self.zone.enabled)
        # Area: 300 * 200 = 60000.0
        self.assertAlmostEqual(self.zone.area, 60000.0)
        self.assertEqual(self.zone.bounding_box, (100.0, 100.0, 400.0, 300.0))

    def test_too_few_vertices_raises_value_error(self) -> None:
        """Verify fewer than 3 vertices raises ValueError."""
        with self.assertRaises(ValueError):
            PolygonZone(zone_id="z", name="n", vertices=((10.0, 20.0), (30.0, 40.0)))
        with self.assertRaises(ValueError):
            PolygonZone(zone_id="z", name="n", vertices=())

    def test_zero_area_or_collinear_polygon_raises_value_error(self) -> None:
        """Verify collinear vertices with zero area raise ValueError."""
        collinear = ((100.0, 100.0), (200.0, 200.0), (300.0, 300.0))
        with self.assertRaises(ValueError) as ctx:
            PolygonZone(zone_id="z", name="n", vertices=collinear)
        self.assertIn("zero-area", str(ctx.exception))

    def test_non_finite_and_negative_coordinates_raise_value_error(self) -> None:
        """Verify NaN, Inf, and negative coordinates raise ValueError."""
        with self.assertRaises(ValueError):
            PolygonZone(zone_id="z", name="n", vertices=((float("nan"), 0.0), (10.0, 0.0), (10.0, 10.0)))
        with self.assertRaises(ValueError):
            PolygonZone(zone_id="z", name="n", vertices=((float("inf"), 0.0), (10.0, 0.0), (10.0, 10.0)))
        with self.assertRaises(ValueError):
            PolygonZone(zone_id="z", name="n", vertices=((-5.0, 0.0), (10.0, 0.0), (10.0, 10.0)))

    def test_empty_zone_id_and_name_raise_value_error(self) -> None:
        """Verify empty identifiers raise ValueError."""
        with self.assertRaises(ValueError):
            PolygonZone(zone_id="", name="Valid Name", vertices=self.rect_vertices)
        with self.assertRaises(ValueError):
            PolygonZone(zone_id="valid-id", name="", vertices=self.rect_vertices)

    def test_point_clearly_inside(self) -> None:
        """Verify points inside the polygon return True."""
        self.assertTrue(self.zone.contains_point((200.0, 200.0)))
        self.assertTrue(self.zone.contains_point((150.0, 150.0)))

    def test_point_clearly_outside(self) -> None:
        """Verify points outside the polygon return False."""
        self.assertFalse(self.zone.contains_point((50.0, 50.0)))
        self.assertFalse(self.zone.contains_point((500.0, 200.0)))
        self.assertFalse(self.zone.contains_point((200.0, 350.0)))
        self.assertFalse(self.zone.contains_point((200.0, 50.0)))

    def test_points_on_boundary_and_vertices(self) -> None:
        """Verify points on the edges and vertices are considered inside (True)."""
        # On edges
        self.assertTrue(self.zone.contains_point((250.0, 100.0)))  # top edge
        self.assertTrue(self.zone.contains_point((400.0, 200.0)))  # right edge
        self.assertTrue(self.zone.contains_point((250.0, 300.0)))  # bottom edge
        self.assertTrue(self.zone.contains_point((100.0, 200.0)))  # left edge

        # On vertices
        self.assertTrue(self.zone.contains_point((100.0, 100.0)))
        self.assertTrue(self.zone.contains_point((400.0, 100.0)))
        self.assertTrue(self.zone.contains_point((400.0, 300.0)))
        self.assertTrue(self.zone.contains_point((100.0, 300.0)))

    def test_disabled_zone_rejects_all_points(self) -> None:
        """Verify disabled zones return False even for interior points."""
        disabled_zone = PolygonZone(
            zone_id="disabled-z",
            name="Disabled Zone",
            vertices=self.rect_vertices,
            enabled=False,
        )
        self.assertFalse(disabled_zone.contains_point((200.0, 200.0)))

    def test_concave_l_shaped_polygon(self) -> None:
        """Verify non-convex (L-shaped) polygon handles notch void correctly."""
        # L-shaped polygon covering (0,0) to (100,100) with a cut-out at (50,50) to (100,100)
        l_vertices = (
            (0.0, 0.0),
            (100.0, 0.0),
            (100.0, 50.0),
            (50.0, 50.0),
            (50.0, 100.0),
            (0.0, 100.0),
        )
        l_zone = PolygonZone(zone_id="l-zone", name="L Zone", vertices=l_vertices)

        # Inside the solid body
        self.assertTrue(l_zone.contains_point((25.0, 25.0)))
        self.assertTrue(l_zone.contains_point((75.0, 25.0)))
        self.assertTrue(l_zone.contains_point((25.0, 75.0)))

        # Inside the notch/cutout (outside the polygon!)
        self.assertFalse(l_zone.contains_point((75.0, 75.0)))

    def test_serialization_roundtrip(self) -> None:
        """Verify to_dict and from_dict roundtrip."""
        zone_dict = self.zone.to_dict()
        reconstructed = PolygonZone.from_dict(zone_dict)
        self.assertEqual(reconstructed.zone_id, self.zone.zone_id)
        self.assertEqual(reconstructed.name, self.zone.name)
        self.assertEqual(reconstructed.vertices, self.zone.vertices)


class TestZoneAnalyzer(unittest.TestCase):
    """Test suite for ZoneAnalyzer person-versus-zone evaluation."""

    def setUp(self) -> None:
        self.meta = FrameMetadata(frame_index=10, timestamp=1.0, width=1280, height=720)
        # Zone covers Y from 200 to 500, X from 200 to 600
        self.zone1 = PolygonZone(
            zone_id="zone-01",
            name="Perimeter Zone",
            vertices=(
                (200.0, 200.0),
                (600.0, 200.0),
                (600.0, 500.0),
                (200.0, 500.0),
            ),
        )
        self.analyzer = ZoneAnalyzer(zones=[self.zone1], reference_point_strategy="bottom_center")

    def test_person_inside_zone(self) -> None:
        """Verify person with bottom-center inside zone is detected as inside."""
        # Person bbox: x1=300, y1=250, x2=340, y2=350 -> bottom_center = (320, 350) (inside zone)
        bbox = BoundingBox(x1=300.0, y1=250.0, x2=340.0, y2=350.0)
        det = Detection(class_name="person", confidence=0.91, bbox=bbox)

        results = self.analyzer.evaluate([det], self.meta)
        self.assertEqual(len(results), 1)
        res = results[0]
        self.assertTrue(res.is_inside)
        self.assertEqual(res.zone_id, "zone-01")
        self.assertEqual(res.reference_point, (320.0, 350.0))
        self.assertEqual(res.frame_index, 10)
        self.assertAlmostEqual(res.timestamp, 1.0)

    def test_person_outside_zone(self) -> None:
        """Verify person completely outside zone returns is_inside=False."""
        # Person bbox at (50, 50, 90, 150) -> bottom_center = (70, 150) (outside zone)
        bbox = BoundingBox(x1=50.0, y1=50.0, x2=90.0, y2=150.0)
        det = Detection(class_name="person", confidence=0.88, bbox=bbox)

        results = self.analyzer.evaluate([det], self.meta)
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].is_inside)

    def test_ground_plane_anchor_vs_centroid_strategy(self) -> None:
        """CRITICAL TEST: Verify difference between bottom-center and center strategies.

        Scenario: A person standing just below the bottom boundary of the zone (at Y=510),
        with their upper body and head extending up to Y=450.
        Zone extends up to Y=500.
        - Centroid (center): Y = (450 + 510)/2 = 480 -> INSIDE zone!
        - Ground contact (bottom_center): Y = 510 -> OUTSIDE zone!
        Because the person's feet have NOT stepped into the restricted ground zone,
        the bottom_center strategy must report OUTSIDE (is_inside=False)!
        """
        bbox = BoundingBox(x1=300.0, y1=450.0, x2=340.0, y2=510.0)
        det = Detection(class_name="person", confidence=0.95, bbox=bbox)

        # 1. Evaluate with bottom_center strategy (Ground-Plane foot contact)
        analyzer_bottom = ZoneAnalyzer(zones=[self.zone1], reference_point_strategy="bottom_center")
        res_bottom = analyzer_bottom.evaluate([det], self.meta)
        self.assertEqual(len(res_bottom), 1)
        self.assertFalse(
            res_bottom[0].is_inside,
            "Person feet at Y=510 must be OUTSIDE zone with boundary at Y=500",
        )

        # 2. Evaluate with center strategy (Bounding-Box centroid)
        analyzer_center = ZoneAnalyzer(zones=[self.zone1], reference_point_strategy="center")
        res_center = analyzer_center.evaluate([det], self.meta)
        self.assertEqual(len(res_center), 1)
        self.assertTrue(
            res_center[0].is_inside,
            "Person centroid at Y=480 is geometrically inside zone boundary at Y=500",
        )

    def test_multiple_persons_and_multiple_zones(self) -> None:
        """Verify handling multiple persons and multiple overlapping zones."""
        zone2 = PolygonZone(
            zone_id="zone-02",
            name="Inner Core",
            vertices=(
                (250.0, 250.0),
                (450.0, 250.0),
                (450.0, 400.0),
                (250.0, 400.0),
            ),
        )
        multi_analyzer = ZoneAnalyzer(zones=[self.zone1, zone2])

        # Person 1 inside both zone 1 and zone 2 (feet at 300, 300)
        p1 = Detection(class_name="person", confidence=0.9, bbox=BoundingBox(280.0, 200.0, 320.0, 300.0))
        # Person 2 inside zone 1 only (feet at 550, 450)
        p2 = Detection(class_name="person", confidence=0.85, bbox=BoundingBox(530.0, 350.0, 570.0, 450.0))
        # Person 3 outside all zones (feet at 50, 50)
        p3 = Detection(class_name="person", confidence=0.92, bbox=BoundingBox(30.0, 10.0, 70.0, 50.0))

        results = multi_analyzer.evaluate([p1, p2, p3], self.meta)
        # 3 persons * 2 zones = 6 evaluations
        self.assertEqual(len(results), 6)

        inside_only = multi_analyzer.evaluate_inside([p1, p2, p3], self.meta)
        # p1 is inside both (2), p2 is inside zone1 (1) -> total 3 incursions
        self.assertEqual(len(inside_only), 3)

    def test_disabled_zone_ignored_in_evaluation(self) -> None:
        """Verify disabled zones are completely ignored by the analyzer."""
        disabled_zone = PolygonZone(
            zone_id="zone-disabled",
            name="Inactive Zone",
            vertices=self.zone1.vertices,
            enabled=False,
        )
        analyzer = ZoneAnalyzer(zones=[disabled_zone])
        det = Detection(class_name="person", confidence=0.9, bbox=BoundingBox(250.0, 250.0, 350.0, 350.0))

        results = analyzer.evaluate([det], self.meta)
        self.assertEqual(len(results), 0)

    def test_empty_detections_list(self) -> None:
        """Verify empty detections list returns empty result list."""
        results = self.analyzer.evaluate([], self.meta)
        self.assertEqual(results, [])

    def test_invalid_reference_point_strategy_raises_value_error(self) -> None:
        """Verify invalid strategy name raises ValueError."""
        with self.assertRaises(ValueError):
            ZoneAnalyzer(reference_point_strategy="invalid_strategy")


if __name__ == "__main__":
    unittest.main()
