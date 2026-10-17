"""Security event generation and temporal deduplication for SentinelAI CV Engine.

Transforms qualifying zone-analysis results into structured CV security events
conforming strictly to API_CONTRACT.md.

Zone-Entry & Occupancy Policy:
    In surveillance environments without persistent multi-object tracking (e.g. ByteTrack),
    person detections are evaluated per-frame. This component implements an occupancy
    observation policy:
    1. Temporal Confirmation (Debounce): An occupancy observation must persist for a
       configurable number of consecutive frames (temporal_confirmation_frames >= 1)
       to avoid false alarms from single-frame visual flutter or detector noise.
    2. Cooldown Deduplication: Once an event is emitted for a given (camera_id, zone_id),
       a cooldown timer (deduplication_cooldown_sec) prevents emitting duplicate events
       while a subject remains continuously inside the restricted zone.
    3. Zone Clearing: When no person is detected inside a zone, the consecutive occupancy
       counter for that zone resets to 0.
    4. Identity Boundaries: The event generator never fabricates persistent person identities.
       When tracking is not active, evidence.track_id is set to None (null in JSON) per
       API_CONTRACT.md.
    5. Architectural Separation: The CV engine outputs observable facts and detector statistical
       confidence. It never computes risk scores, risk levels, threat probabilities, or reasons;
       those are strictly owned and computed by the backend service.
"""

from datetime import datetime, timedelta, timezone
import hashlib
from typing import Any, Dict, List, Optional, Set

from sentinel_cv.interfaces import IEventGenerator
from sentinel_cv.logging_config import get_logger
from sentinel_cv.models import FrameMetadata, SecurityEvent, ZoneAnalysisResult


class EventGenerator(IEventGenerator):
    """Generates structured SecurityEvent instances from zone analysis results.

    Applies temporal confirmation debouncing, cooldown deduplication, and deterministic
    event ID generation.
    """

    def __init__(
        self,
        camera_id: str = "cam-demo-01",
        severity: str = "HIGH",
        temporal_confirmation_frames: int = 1,
        deduplication_cooldown_sec: float = 5.0,
        base_timestamp: Optional[str] = "2026-10-17T09:30:00Z",
    ) -> None:
        """Initialize the event generator.

        Args:
            camera_id: Camera identifier matching API_CONTRACT.md.
            severity: Observable severity rating ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL').
            temporal_confirmation_frames: Number of consecutive inside frames required to emit.
            deduplication_cooldown_sec: Cooldown window in seconds before repeating for a zone.
            base_timestamp: ISO-8601 base timestamp representing video start time.
        """
        if not camera_id or not str(camera_id).strip():
            raise ValueError("camera_id must be a non-empty string.")
        if temporal_confirmation_frames < 1:
            raise ValueError("temporal_confirmation_frames must be >= 1.")
        if deduplication_cooldown_sec < 0.0:
            raise ValueError("deduplication_cooldown_sec must be non-negative.")

        self.camera_id = camera_id
        self.severity = severity
        self.temporal_confirmation_frames = temporal_confirmation_frames
        self.deduplication_cooldown_sec = deduplication_cooldown_sec
        self.base_timestamp = base_timestamp
        self.logger = get_logger("event_generator")

        # Internal state tracking:
        # zone_id -> consecutive frames with inside detections
        self._zone_consecutive_counts: Dict[str, int] = {}
        # zone_id -> timestamp (in elapsed video seconds) when last event was emitted
        self._zone_last_event_time: Dict[str, float] = {}

    def reset(self) -> None:
        """Reset internal debounce counters and cooldown state."""
        self._zone_consecutive_counts.clear()
        self._zone_last_event_time.clear()
        self.logger.debug("EventGenerator state reset.")

    def format_iso_timestamp(self, elapsed_seconds: float) -> str:
        """Convert elapsed video seconds to an ISO-8601 timestamp with timezone.

        Args:
            elapsed_seconds: Elapsed time in seconds from video start.

        Returns:
            str: ISO-8601 formatted timestamp string ending in 'Z'.
        """
        if self.base_timestamp:
            try:
                # Normalize 'Z' to UTC offset for fromisoformat compatibility
                ts_str = self.base_timestamp.replace("Z", "+00:00")
                base_dt = datetime.fromisoformat(ts_str)
                if base_dt.tzinfo is None:
                    base_dt = base_dt.replace(tzinfo=timezone.utc)
            except Exception:
                base_dt = datetime.now(timezone.utc)
        else:
            base_dt = datetime.now(timezone.utc)

        event_dt = base_dt + timedelta(seconds=float(elapsed_seconds))
        # Ensure UTC and standard Z suffix
        utc_dt = event_dt.astimezone(timezone.utc)
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def generate_event_id(
        self,
        zone_id: str,
        frame_index: int,
        timestamp: float,
        confidence: float,
    ) -> str:
        """Generate a deterministic, stable event identifier.

        Reprocessing identical frame index and observation parameters produces
        the exact same identifier without relying on random UUIDs or Python hash().

        Args:
            zone_id: Zone identifier.
            frame_index: Frame sequence number.
            timestamp: Elapsed video timestamp.
            confidence: Detector confidence score.

        Returns:
            str: Unique, reproducible event identifier (e.g., 'evt-cam01-zone01-a1b2c3d4').
        """
        raw_key = (
            f"{self.camera_id}:{zone_id}:{frame_index}:"
            f"{round(timestamp, 2)}:{round(confidence, 4)}"
        )
        digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:8]
        clean_cam = self.camera_id.replace("_", "-")
        clean_zone = zone_id.replace("_", "-")
        return f"evt-{clean_cam}-{clean_zone}-{digest}"

    def process_zone_results(
        self,
        zone_results: List[ZoneAnalysisResult],
        metadata: FrameMetadata,
    ) -> List[SecurityEvent]:
        """Evaluate zone analysis observations and generate qualifying SecurityEvents.

        Args:
            zone_results: All spatial evaluation results for the current frame.
            metadata: Associated frame sequence and timing metadata.

        Returns:
            List[SecurityEvent]: Structured events emitted according to policy.
        """
        if not zone_results:
            # No zone evaluations in this frame; reset all occupancy counters
            for zid in list(self._zone_consecutive_counts.keys()):
                self._zone_consecutive_counts[zid] = 0
            return []

        # Group inside detections by zone_id
        inside_by_zone: Dict[str, List[ZoneAnalysisResult]] = {}
        for res in zone_results:
            if res.is_inside:
                inside_by_zone.setdefault(res.zone_id, []).append(res)

        # Track active zones in this frame to reset empty zones
        evaluated_zone_ids: Set[str] = {r.zone_id for r in zone_results}
        for zid in evaluated_zone_ids:
            if zid not in inside_by_zone:
                # Zone is clear in this frame -> reset consecutive inside counter
                self._zone_consecutive_counts[zid] = 0

        emitted_events: List[SecurityEvent] = []

        for zone_id, active_results in inside_by_zone.items():
            # 1. Update consecutive occupancy count
            current_count = self._zone_consecutive_counts.get(zone_id, 0) + 1
            self._zone_consecutive_counts[zone_id] = current_count

            # 2. Check temporal confirmation (debounce)
            if current_count < self.temporal_confirmation_frames:
                self.logger.debug(
                    "Zone '%s' occupied (frame %d/%d). Debouncing transient noise.",
                    zone_id,
                    current_count,
                    self.temporal_confirmation_frames,
                )
                continue

            # 3. Check cooldown deduplication
            last_event_time = self._zone_last_event_time.get(zone_id, -float("inf"))
            elapsed_since_last = metadata.timestamp - last_event_time

            if elapsed_since_last < self.deduplication_cooldown_sec:
                self.logger.debug(
                    "Zone '%s' in cooldown (%.2fs < %.2fs). Suppressing duplicate event.",
                    zone_id,
                    elapsed_since_last,
                    self.deduplication_cooldown_sec,
                )
                continue

            # 4. Select primary observation (highest confidence detection in zone)
            primary_res = max(active_results, key=lambda r: r.detection_confidence)

            # 5. Build deterministic event identifier
            event_id = self.generate_event_id(
                zone_id=zone_id,
                frame_index=metadata.frame_index,
                timestamp=metadata.timestamp,
                confidence=primary_res.detection_confidence,
            )

            # 6. Format ISO-8601 timestamp
            iso_timestamp = self.format_iso_timestamp(metadata.timestamp)

            # 7. Construct evidence dictionary adhering to API_CONTRACT.md
            evidence: Dict[str, Any] = {
                "class_name": primary_res.detection.class_name,
                "track_id": primary_res.detection.track_id,  # null per contract when tracking is disabled
                "frame_number": metadata.frame_index,
                "bounding_box": primary_res.detection.bbox.as_dict(),
                "reference_point": (
                    round(primary_res.reference_point[0], 2),
                    round(primary_res.reference_point[1], 2),
                ),
                "zone_name": primary_res.zone_name,
                "elapsed_time_sec": round(float(metadata.timestamp), 3),
                "consecutive_inside_frames": current_count,
            }

            description = (
                f"Observable person detected inside restricted zone '{primary_res.zone_name}' "
                f"at ground-plane position {primary_res.reference_point}"
            )

            event = SecurityEvent(
                event_id=event_id,
                camera_id=self.camera_id,
                event_type="RESTRICTED_ZONE_ENTRY",
                timestamp=iso_timestamp,
                severity=self.severity,
                confidence=round(float(primary_res.detection_confidence), 4),
                zone_id=zone_id,
                description=description,
                evidence=evidence,
            )

            # 8. Record emission timestamp for cooldown tracking
            self._zone_last_event_time[zone_id] = metadata.timestamp
            emitted_events.append(event)

            self.logger.info(
                "Generated SecurityEvent: %s | Zone: %s | Frame: #%d | Conf: %.2f",
                event_id,
                zone_id,
                metadata.frame_index,
                primary_res.detection_confidence,
            )

        return emitted_events
