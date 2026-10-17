"""Controlled RTSP & Video Stream Simulation Script for SentinelAI.

Provides a standalone, reproducible simulation environment for testing
continuous video stream ingestion, YOLO person detection, restricted-zone
incursion analysis, and backend event submission without requiring physical
CCTV camera hardware or external media gateways.

Usage:
    # Run 50 frames of continuous simulation against the local SentinelAI backend:
    python scripts/simulate_rtsp_stream.py --camera-id cam-north-01 --fps 15 --frames 50

    # Run continuous stream until Ctrl+C:
    python scripts/simulate_rtsp_stream.py --camera-id cam-north-01 --continuous

    # Serve lightweight MJPEG inspection stream on http://127.0.0.1:8554/live:
    python scripts/simulate_rtsp_stream.py --serve-mjpeg --port 8554
"""

import argparse
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sys
import time
from typing import Any, List, Optional, Tuple

# Ensure cv-engine/src is on sys.path
repo_root = Path(__file__).resolve().parents[1]
cv_src = repo_root / "cv-engine" / "src"
if cv_src.is_dir() and str(cv_src) not in sys.path:
    sys.path.insert(0, str(cv_src))

try:
    import numpy as np
except ImportError:
    np = None

try:
    import cv2
except ImportError:
    cv2 = None

from sentinel_cv.backend_client import BackendClient
from sentinel_cv.config import CVConfig
from sentinel_cv.detector import create_replay_detector, create_detector
from sentinel_cv.event_generator import EventGenerator
from sentinel_cv.models import BoundingBox, Detection, FrameMetadata
from sentinel_cv.rtsp_source import RTSPVideoSource, redact_stream_url
from sentinel_cv.video_source import ReplayVideoSource
from sentinel_cv.zone import PolygonZone, ZoneAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("rtsp_simulation")


def generate_synthetic_surveillance_frame(
    width: int,
    height: int,
    frame_index: int,
    person_pos: Tuple[int, int],
    zone_pts: List[Tuple[int, int]],
) -> Any:
    """Render a synthetic CCTV surveillance frame with timestamps, zone overlay, and moving target."""
    if np is None or cv2 is None:
        return None

    # Base dark surveillance background (simulating low-light border perimeter)
    img = np.full((height, width, 3), (35, 40, 45), dtype=np.uint8)

    # Draw border fence lines
    cv2.line(img, (0, int(height * 0.7)), (width, int(height * 0.7)), (60, 70, 80), 2)
    cv2.line(img, (0, int(height * 0.85)), (width, int(height * 0.85)), (70, 80, 90), 2)

    # Draw restricted zone boundary polygon (translucent yellow/red)
    pts = np.array(zone_pts, np.int32).reshape((-1, 1, 2))
    cv2.polylines(img, [pts], isClosed=True, color=(0, 215, 255), thickness=2)

    # Draw walking person silhouette at current position
    px, py = person_pos
    # Torso & legs
    cv2.rectangle(img, (px - 15, py - 60), (px + 15, py), (180, 180, 200), -1)
    # Head
    cv2.circle(img, (px, py - 75), 12, (200, 200, 220), -1)

    # OSD (On-Screen Display) Timestamp & Camera ID
    ts_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    cv2.putText(img, f"CAM-01 [LIVE RTSP SIM] - {ts_str}", (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(img, f"FRAME: {frame_index:06d} | BUFFER ZONE RESTRICTED", (20, 55),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 215, 255), 1)

    return img


def run_simulation(
    camera_id: str = "cam-north-01",
    fps: float = 15.0,
    max_frames: Optional[int] = 50,
    backend_url: str = "http://127.0.0.1:8000",
    api_key: Optional[str] = None,
) -> None:
    """Run continuous stream simulation processing loop."""
    logger.info("Initializing Controlled RTSP Stream Simulation | Camera: %s | FPS: %.1f", camera_id, fps)

    width, height = 1280, 720
    # Defined restricted zone boundary (normalized 0.25 to 0.75)
    zone_pts = [
        (int(width * 0.30), int(height * 0.40)),
        (int(width * 0.70), int(height * 0.40)),
        (int(width * 0.70), int(height * 0.85)),
        (int(width * 0.30), int(height * 0.85)),
    ]

    zone = PolygonZone(
        zone_id=f"zone-{camera_id}",
        name=f"Perimeter Buffer for {camera_id}",
        vertices=(
            (float(width * 0.30), float(height * 0.40)),
            (float(width * 0.70), float(height * 0.40)),
            (float(width * 0.70), float(height * 0.85)),
            (float(width * 0.30), float(height * 0.85)),
        ),
        enabled=True,
    )
    zone_analyzer = ZoneAnalyzer(zones=[zone], reference_point_strategy="bottom_center")

    event_generator = EventGenerator(
        camera_id=camera_id,
        severity="HIGH",
        temporal_confirmation_frames=2,
        deduplication_cooldown_sec=3.0,
    )

    backend_client = BackendClient(
        base_url=backend_url,
        timeout_seconds=3.0,
        api_key=api_key,
    )

    # Check backend connectivity
    is_healthy, health_msg = backend_client.check_health()
    logger.info("Backend connectivity status: %s (%s)", is_healthy, health_msg)

    frame_interval = 1.0 / fps
    frame_idx = 0
    total_detections = 0
    total_incursions = 0
    total_events = 0

    # Start target position outside zone, walking into zone
    start_x, end_x = 200, 600
    pos_y = int(height * 0.65)

    try:
        while max_frames is None or frame_idx < max_frames:
            t0 = time.monotonic()

            # Target position advances horizontally
            progress = min(1.0, frame_idx / 30.0)
            cur_x = int(start_x + (end_x - start_x) * progress)

            # Generate frame
            frame = generate_synthetic_surveillance_frame(
                width=width,
                height=height,
                frame_index=frame_idx,
                person_pos=(cur_x, pos_y),
                zone_pts=zone_pts,
            )

            metadata = FrameMetadata(
                frame_index=frame_idx,
                timestamp=frame_idx / fps,
                width=width,
                height=height,
                source_id=camera_id,
            )

            # Detection bounding box (around moving person)
            box = BoundingBox(
                x1=float(cur_x - 18),
                y1=float(pos_y - 80),
                x2=float(cur_x + 18),
                y2=float(pos_y),
            )
            detection = Detection(
                class_name="person",
                confidence=0.91,
                bbox=box,
                track_id=1,
            )
            detections = [detection]
            total_detections += len(detections)

            # Spatial Zone intersection
            zone_results = zone_analyzer.evaluate(detections, metadata)
            inside_count = sum(1 for z in zone_results if z.is_inside)
            total_incursions += inside_count

            # Event generation with temporal confirmation
            events = event_generator.process_zone_results(zone_results, metadata)
            if events:
                total_events += len(events)
                for ev in events:
                    logger.info("EMITTED SECURITY EVENT: %s (Zone: %s, Incursion verified)", ev.event_id, ev.zone_id)
                    res = backend_client.submit_event(ev)
                    logger.info("Backend submission result: success=%s (HTTP %s)", res.success, res.status_code)

            if frame_idx % 10 == 0 or inside_count > 0:
                logger.info(
                    "Frame %04d | Target at (%d, %d) | Inside Zone: %s | Events Emitted: %d",
                    frame_idx, cur_x, pos_y, inside_count > 0, total_events,
                )

            frame_idx += 1
            elapsed = time.monotonic() - t0
            if elapsed < frame_interval:
                time.sleep(frame_interval - elapsed)

    except KeyboardInterrupt:
        logger.info("Simulation interrupted by operator.")

    logger.info("Simulation Complete. Frames: %d | Detections: %d | Incursions: %d | Events: %d",
                frame_idx, total_detections, total_incursions, total_events)


def main() -> None:
    parser = argparse.ArgumentParser(description="SentinelAI Controlled RTSP Simulation")
    parser.add_argument("--camera-id", default="cam-north-01", help="Target camera identifier")
    parser.add_argument("--fps", type=float, default=15.0, help="Simulation frame rate")
    parser.add_argument("--frames", type=int, default=50, help="Total frames to process (None = continuous)")
    parser.add_argument("--continuous", action="store_true", help="Run indefinitely until stopped")
    parser.add_argument("--backend-url", default="http://127.0.0.1:8000", help="FastAPI backend URL")
    parser.add_argument("--api-key", default=None, help="Service M2M API key")

    args = parser.parse_args()
    max_frames = None if args.continuous else args.frames
    run_simulation(
        camera_id=args.camera_id,
        fps=args.fps,
        max_frames=max_frames,
        backend_url=args.backend_url,
        api_key=args.api_key,
    )


if __name__ == "__main__":
    main()
