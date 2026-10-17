"""Automated tests for SentinelAI SecurityEvent model and EventGenerator.

Verifies:
1. Strict API_CONTRACT.md schema compliance for SecurityEvent.
2. Absence of backend-owned risk fields (risk_score, risk_level, reasons).
3. Deterministic event ID generation without random UUIDs or Python hash().
4. Temporal confirmation debouncing (preventing single-frame noise).
5. Cooldown deduplication (preventing event flood during continuous occupancy).
6. Multi-zone and empty zone handling.
"""

import unittest

from sentinel_cv.event_generator import EventGenerator
from sentinel_cv.models import (
    BoundingBox,
    Detection,
    FrameMetadata,
    SecurityEvent,
    ZoneAnalysisResult,
)


class TestSecurityEventModel(unittest.TestCase):
    """Test suite for SecurityEvent dataclass validation and serialization."""

    def setUp(self) -> None:
        self.valid_evidence = {
            "class_name": "person",
            "track_id": None,
            "frame_number": 420,
            "bounding_box": {"x1": 100.0, "y1": 200.0, "x2": 180.0, "y2": 450.0},
        }

    def test_valid_security_event_creation(self) -> None:
        """Verify valid SecurityEvent initializes and preserves all required fields."""
        event = SecurityEvent(
            event_id="evt-demo-0001",
            camera_id="cam-demo-01",
            event_type="RESTRICTED_ZONE_ENTRY",
            timestamp="2026-10-17T09:30:00Z",
            severity="HIGH",
            confidence=0.91,
            zone_id="zone-restricted-01",
            description="Detection entered the configured zone",
            evidence=self.valid_evidence,
        )
        self.assertEqual(event.event_id, "evt-demo-0001")
        self.assertEqual(event.camera_id, "cam-demo-01")
        self.assertEqual(event.event_type, "RESTRICTED_ZONE_ENTRY")
        self.assertEqual(event.timestamp, "2026-10-17T09:30:00Z")
        self.assertEqual(event.severity, "HIGH")
        self.assertEqual(event.confidence, 0.91)
        self.assertEqual(event.zone_id, "zone-restricted-01")

    def test_to_dict_matches_api_contract_schema(self) -> None:
        """Verify dictionary serialization strictly conforms to API_CONTRACT.md schema."""
        event = SecurityEvent(
            event_id="evt-demo-0001",
            camera_id="cam-demo-01",
            event_type="RESTRICTED_ZONE_ENTRY",
            timestamp="2026-10-17T09:30:00Z",
            severity="HIGH",
            confidence=0.91,
            zone_id="zone-restricted-01",
            description="Detection entered the configured zone",
            evidence=self.valid_evidence,
        )
        d = event.to_dict()

        # Contract required fields
        expected_keys = {
            "event_id",
            "camera_id",
            "event_type",
            "timestamp",
            "severity",
            "confidence",
            "zone_id",
            "description",
            "evidence",
        }
        self.assertEqual(set(d.keys()), expected_keys)

        # STRICT ARCHITECTURAL BOUNDARY: CV engine never generates backend risk fields
        self.assertNotIn("risk_score", d)
        self.assertNotIn("risk_level", d)
        self.assertNotIn("reasons", d)
        self.assertNotIn("recommended_action", d)
        self.assertNotIn("status", d)

    def test_invalid_event_type_raises_value_error(self) -> None:
        """Verify unapproved event type raises ValueError."""
        with self.assertRaises(ValueError):
            SecurityEvent(
                event_id="evt-01",
                camera_id="cam-01",
                event_type="UNAUTHORIZED_CUSTOM_EVENT",
                timestamp="2026-10-17T09:30:00Z",
                severity="HIGH",
                confidence=0.9,
                zone_id="z1",
                description="desc",
            )

    def test_invalid_severity_raises_value_error(self) -> None:
        """Verify invalid severity raises ValueError."""
        with self.assertRaises(ValueError):
            SecurityEvent(
                event_id="evt-01",
                camera_id="cam-01",
                timestamp="2026-10-17T09:30:00Z",
                severity="EXTREME",  # Must be LOW, MEDIUM, HIGH, CRITICAL
                confidence=0.9,
                zone_id="z1",
                description="desc",
            )

    def test_invalid_confidence_raises_value_error(self) -> None:
        """Verify confidence out of [0.0, 1.0] raises ValueError."""
        with self.assertRaises(ValueError):
            SecurityEvent(
                event_id="evt-01",
                camera_id="cam-01",
                timestamp="2026-10-17T09:30:00Z",
                severity="HIGH",
                confidence=1.5,
                zone_id="z1",
                description="desc",
            )

    def test_invalid_timestamp_raises_value_error(self) -> None:
        """Verify non-ISO or non-timezone timestamp raises ValueError."""
        with self.assertRaises(ValueError):
            SecurityEvent(
                event_id="evt-01",
                camera_id="cam-01",
                timestamp="2026-10-17 09:30:00",  # Missing T and timezone
                severity="HIGH",
                confidence=0.8,
                zone_id="z1",
                description="desc",
            )


class TestEventGenerator(unittest.TestCase):
    """Test suite for EventGenerator temporal confirmation and cooldown logic."""

    def setUp(self) -> None:
        self.generator = EventGenerator(
            camera_id="cam-test-01",
            severity="HIGH",
            temporal_confirmation_frames=2,
            deduplication_cooldown_sec=5.0,
            base_timestamp="2026-10-17T09:30:00Z",
        )
        self.sample_detection = Detection(
            class_name="person",
            confidence=0.88,
            bbox=BoundingBox(x1=100.0, y1=200.0, x2=180.0, y2=450.0),
        )

    def _make_zone_result(
        self,
        is_inside: bool = True,
        zone_id: str = "zone-north",
        frame_index: int = 10,
        timestamp: float = 1.0,
        confidence: float = 0.88,
    ) -> ZoneAnalysisResult:
        det = Detection(
            class_name="person",
            confidence=confidence,
            bbox=BoundingBox(x1=100.0, y1=200.0, x2=180.0, y2=450.0),
        )
        return ZoneAnalysisResult(
            detection=det,
            frame_index=frame_index,
            timestamp=timestamp,
            zone_id=zone_id,
            zone_name="North Perimeter",
            is_inside=is_inside,
            reference_point=(140.0, 450.0),
            detection_confidence=confidence,
        )

    def test_person_outside_zone_generates_no_event(self) -> None:
        """Verify detections outside the zone never generate security events."""
        meta = FrameMetadata(frame_index=0, timestamp=0.0, width=1280, height=720)
        res = self._make_zone_result(is_inside=False, frame_index=0, timestamp=0.0)

        events = self.generator.process_zone_results([res], meta)
        self.assertEqual(len(events), 0)

    def test_temporal_confirmation_debouncing(self) -> None:
        """Verify multi-frame confirmation prevents emitting on single-frame transient noise."""
        # temporal_confirmation_frames = 2
        # Frame 1: inside -> counter becomes 1 (< 2) -> NO event
        meta1 = FrameMetadata(frame_index=1, timestamp=0.1, width=1280, height=720)
        res1 = self._make_zone_result(is_inside=True, frame_index=1, timestamp=0.1)
        events1 = self.generator.process_zone_results([res1], meta1)
        self.assertEqual(len(events1), 0)

        # Frame 2: inside -> counter becomes 2 (>= 2) -> EVENT emitted
        meta2 = FrameMetadata(frame_index=2, timestamp=0.2, width=1280, height=720)
        res2 = self._make_zone_result(is_inside=True, frame_index=2, timestamp=0.2)
        events2 = self.generator.process_zone_results([res2], meta2)
        self.assertEqual(len(events2), 1)

        event = events2[0]
        self.assertEqual(event.camera_id, "cam-test-01")
        self.assertEqual(event.zone_id, "zone-north")
        self.assertEqual(event.confidence, 0.88)
        self.assertIn("Z", event.timestamp)
        self.assertEqual(event.evidence["frame_number"], 2)

    def test_cooldown_deduplication(self) -> None:
        """Verify continuous occupancy suppresses duplicates during cooldown window."""
        # Frame 1: debounce 1
        meta1 = FrameMetadata(frame_index=1, timestamp=1.0, width=1280, height=720)
        res1 = self._make_zone_result(is_inside=True, frame_index=1, timestamp=1.0)
        self.generator.process_zone_results([res1], meta1)

        # Frame 2: debounce 2 -> emits event at timestamp 1.1s
        meta2 = FrameMetadata(frame_index=2, timestamp=1.1, width=1280, height=720)
        res2 = self._make_zone_result(is_inside=True, frame_index=2, timestamp=1.1)
        events2 = self.generator.process_zone_results([res2], meta2)
        self.assertEqual(len(events2), 1)

        # Frame 3: at timestamp 2.5s (< 1.1 + 5.0 cooldown) -> in cooldown -> NO event
        meta3 = FrameMetadata(frame_index=15, timestamp=2.5, width=1280, height=720)
        res3 = self._make_zone_result(is_inside=True, frame_index=15, timestamp=2.5)
        events3 = self.generator.process_zone_results([res3], meta3)
        self.assertEqual(len(events3), 0)

        # Frame 4: at timestamp 6.2s (> 1.1 + 5.0 cooldown) -> cooldown expired -> NEW event emitted
        meta4 = FrameMetadata(frame_index=55, timestamp=6.2, width=1280, height=720)
        res4 = self._make_zone_result(is_inside=True, frame_index=55, timestamp=6.2)
        events4 = self.generator.process_zone_results([res4], meta4)
        self.assertEqual(len(events4), 1)

    def test_zone_clearing_resets_debounce_counter(self) -> None:
        """Verify leaving the zone resets the consecutive occupancy counter."""
        # Frame 1: inside -> count=1
        meta1 = FrameMetadata(frame_index=1, timestamp=1.0, width=1280, height=720)
        res1 = self._make_zone_result(is_inside=True, frame_index=1, timestamp=1.0)
        self.generator.process_zone_results([res1], meta1)

        # Frame 2: outside -> count resets to 0
        meta2 = FrameMetadata(frame_index=2, timestamp=1.1, width=1280, height=720)
        res2 = self._make_zone_result(is_inside=False, frame_index=2, timestamp=1.1)
        events2 = self.generator.process_zone_results([res2], meta2)
        self.assertEqual(len(events2), 0)

        # Frame 3: inside again -> count becomes 1 (< 2 required) -> NO event
        meta3 = FrameMetadata(frame_index=3, timestamp=1.2, width=1280, height=720)
        res3 = self._make_zone_result(is_inside=True, frame_index=3, timestamp=1.2)
        events3 = self.generator.process_zone_results([res3], meta3)
        self.assertEqual(len(events3), 0)

    def test_deterministic_event_id_generation(self) -> None:
        """Verify identical inputs produce the identical event_id deterministically."""
        id1 = self.generator.generate_event_id("zone-01", 100, 10.5, 0.85)
        id2 = self.generator.generate_event_id("zone-01", 100, 10.5, 0.85)
        self.assertEqual(id1, id2)

        # Distinct inputs produce distinct IDs
        id3 = self.generator.generate_event_id("zone-02", 100, 10.5, 0.85)
        self.assertNotEqual(id1, id3)

    def test_multiple_zones_produce_separate_events(self) -> None:
        """Verify multiple occupied zones generate separate events for each zone."""
        gen = EventGenerator(
            camera_id="cam-demo",
            temporal_confirmation_frames=1,
            deduplication_cooldown_sec=5.0,
        )
        meta = FrameMetadata(frame_index=10, timestamp=1.0, width=1280, height=720)
        res_north = self._make_zone_result(is_inside=True, zone_id="zone-north", timestamp=1.0)
        res_south = self._make_zone_result(is_inside=True, zone_id="zone-south", timestamp=1.0)

        events = gen.process_zone_results([res_north, res_south], meta)
        self.assertEqual(len(events), 2)
        zone_ids = {e.zone_id for e in events}
        self.assertEqual(zone_ids, {"zone-north", "zone-south"})

    def test_reset_method_clears_state(self) -> None:
        """Verify reset() method clears all internal debounce counters and cooldown state."""
        meta = FrameMetadata(frame_index=1, timestamp=1.0, width=1280, height=720)
        res = self._make_zone_result(is_inside=True, timestamp=1.0)
        self.generator.process_zone_results([res], meta)
        self.assertIn("zone-north", self.generator._zone_consecutive_counts)

        self.generator.reset()
        self.assertEqual(len(self.generator._zone_consecutive_counts), 0)
        self.assertEqual(len(self.generator._zone_last_event_time), 0)


if __name__ == "__main__":
    unittest.main()
