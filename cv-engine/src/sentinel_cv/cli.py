"""Command-line interface (CLI) for SentinelAI Computer Vision Engine.

Allows running video processing, person detection, and restricted-zone analysis
on local video files or live camera inputs with concise diagnostic summaries.

Usage:
    python -m sentinel_cv --video sample-data/demo.mp4 --max-frames 100
"""

import argparse
import json
import sys
import time
from typing import List, Optional

from sentinel_cv.config import CVConfig, ConfigurationError
from sentinel_cv.detector import ModelLoadingError, YOLOPersonDetector, create_detector
from sentinel_cv.logging_config import get_logger, setup_logging
from sentinel_cv.pipeline import CVPipeline
from sentinel_cv.video_source import OpenCVVideoSource, VideoSourceError
from sentinel_cv.zone import ZoneAnalyzer


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CV engine CLI."""
    parser = argparse.ArgumentParser(
        prog="sentinel_cv",
        description="SentinelAI CV Engine — Video Ingestion, Person Detection & Zone Analysis CLI",
    )
    parser.add_argument(
        "--video",
        "--video-source",
        dest="video",
        type=str,
        default="sample-data/demo.mp4",
        help="Path to input video file or camera device index (default: sample-data/demo.mp4)",
    )
    parser.add_argument(
        "--model",
        "--model-type",
        dest="model",
        type=str,
        default="yolov8n.pt",
        help="Model path or model identifier (default: yolov8n.pt). Use 'mock' for synthetic testing.",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.50,
        help="Confidence threshold for person detection [0.0 - 1.0] (default: 0.50)",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="Maximum number of frames to process (default: process entire source)",
    )
    parser.add_argument(
        "--camera-id",
        type=str,
        default="cam-demo-01",
        help="Camera identifier matching API contract (default: cam-demo-01)",
    )
    parser.add_argument(
        "--zone-id",
        type=str,
        default="zone-restricted-01",
        help="Restricted zone identifier (default: zone-restricted-01)",
    )
    parser.add_argument(
        "--zone-vertices",
        type=str,
        default=None,
        help="Polygon vertices formatted as JSON or Python list of (x, y) tuples (e.g. '[(0,0),(100,0),(100,100),(0,100)]')",
    )
    parser.add_argument(
        "--zones-file",
        type=str,
        default=None,
        help="Path to JSON file containing zone configuration",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        default="bottom_center",
        choices=["bottom_center", "center"],
        help="Reference point strategy for zone analysis (default: bottom_center)",
    )
    parser.add_argument(
        "--backend-url",
        type=str,
        default="http://localhost:8000",
        help="Base URL of SentinelAI backend service (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--disable-events",
        action="store_true",
        help="Disable structured security event generation and backend submission",
    )
    parser.add_argument(
        "--severity",
        type=str,
        default="HIGH",
        choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        help="Observable severity rating for generated events (default: HIGH)",
    )
    parser.add_argument(
        "--debounce",
        type=int,
        default=1,
        help="Temporal confirmation frames required before emitting event (default: 1)",
    )
    parser.add_argument(
        "--cooldown",
        type=float,
        default=5.0,
        help="Cooldown deduplication window in seconds per zone (default: 5.0)",
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=25.0,
        help="Fallback FPS if video container FPS is invalid (default: 25.0)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity level (default: INFO)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output final execution summary in JSON format",
    )
    parser.add_argument(
        "--per-frame-json",
        action="store_true",
        help="Output structured per-frame detections and zone evaluations",
    )
    return parser


def run_cli(args: Optional[List[str]] = None) -> int:
    """Execute the CLI with provided arguments.

    Returns:
        int: Exit status code (0 for success, non-zero for error).
    """
    import ast

    parser = build_parser()
    parsed = parser.parse_args(args)

    setup_logging(log_level=parsed.log_level)
    logger = get_logger("cli")

    # Parse zone parameters if provided
    zone_vertices = None
    if parsed.zone_vertices:
        try:
            raw_pts = ast.literal_eval(parsed.zone_vertices)
            zone_vertices = [(float(pt[0]), float(pt[1])) for pt in raw_pts]
        except Exception as exc:
            logger.error("Failed to parse --zone-vertices: %s", exc)
            return 1

    zones_json = None
    if parsed.zones_file:
        try:
            with open(parsed.zones_file, "r", encoding="utf-8") as f:
                zones_json = f.read()
        except Exception as exc:
            logger.error("Failed to read --zones-file: %s", exc)
            return 1

    # Build config
    model_type = "mock" if parsed.model.lower() in {"mock", "test"} else "yolo"
    try:
        config = CVConfig(
            input_source_type="file",
            video_source=parsed.video,
            camera_id=parsed.camera_id,
            zone_id=parsed.zone_id,
            zone_vertices=zone_vertices,
            zones_json=zones_json,
            reference_point_strategy=parsed.strategy,
            log_level=parsed.log_level,
            model_type=model_type,
            model_path=parsed.model,
            confidence_threshold=parsed.confidence,
            backend_url=parsed.backend_url,
            events_enabled=not parsed.disable_events,
            event_severity=parsed.severity,
            temporal_confirmation_frames=parsed.debounce,
            deduplication_cooldown_sec=parsed.cooldown,
        )
    except ConfigurationError as cfg_err:
        logger.error("Configuration error: %s", cfg_err)
        return 1

    # Wire pipeline components
    try:
        pipeline = CVPipeline.from_config(config=config, auto_init=True)
    except (ModelLoadingError, VideoSourceError) as init_err:
        logger.error("Initialization failure: %s", init_err)
        return 2
    except Exception as exc:
        logger.error("Unexpected setup error: %s", exc)
        return 2

    # Execute stream
    start_time = time.perf_counter()
    frames_processed = 0
    total_person_detections = 0
    total_zone_incursions = 0
    total_events_emitted = 0

    try:
        for result in pipeline.process_stream(max_frames=parsed.max_frames):
            frames_processed += 1
            total_person_detections += len(result.detections)
            total_zone_incursions += len(result.inside_zone_results)
            total_events_emitted += len(result.events)

            if parsed.per_frame_json:
                print(json.dumps(result.to_dict()))

    except VideoSourceError as src_err:
        logger.error("Video source error during processing: %s", src_err)
        return 2
    except Exception as run_err:
        logger.error("Error during video processing loop: %s", run_err)
        return 2

    elapsed_time = max(0.001, time.perf_counter() - start_time)
    avg_fps = frames_processed / elapsed_time

    summary = {
        "status": "success",
        "video_source": parsed.video,
        "camera_id": parsed.camera_id,
        "zone_id": parsed.zone_id,
        "reference_point_strategy": config.reference_point_strategy,
        "model_type": config.model_type,
        "model_path": config.model_path,
        "confidence_threshold": config.confidence_threshold,
        "backend_url": config.backend_url,
        "events_enabled": config.events_enabled,
        "frames_processed": frames_processed,
        "total_person_detections": total_person_detections,
        "total_zone_incursions": total_zone_incursions,
        "total_events_emitted": total_events_emitted,
        "elapsed_seconds": round(elapsed_time, 3),
        "average_fps": round(avg_fps, 2),
    }

    if parsed.json:
        print(json.dumps(summary, indent=2))
    else:
        print("\n========================================================")
        print(" SENTINELAI CV ENGINE — VIDEO & EVENT PROCESSING SUMMARY")
        print("========================================================")
        print(f" Video Source:            {summary['video_source']}")
        print(f" Camera ID:               {summary['camera_id']}")
        print(f" Monitored Zone ID:       {summary['zone_id']}")
        print(f" Ground Contact Strategy: {summary['reference_point_strategy']}")
        print(f" Model Type:              {summary['model_type']} ({summary['model_path']})")
        print(f" Confidence Threshold:    {summary['confidence_threshold']}")
        print(f" Backend URL:             {summary['backend_url']}")
        print(f" Events Enabled:          {summary['events_enabled']}")
        print(f" Frames Processed:        {summary['frames_processed']}")
        print(f" Total Person Detections: {summary['total_person_detections']}")
        print(f" Total Zone Incursions:   {summary['total_zone_incursions']}")
        print(f" Total Events Emitted:    {summary['total_events_emitted']}")
        print(f" Processing Time:         {summary['elapsed_seconds']}s")
        print(f" Average Processing FPS:  {summary['average_fps']} FPS")
        print("========================================================\n")

    return 0


if __name__ == "__main__":
    sys.exit(run_cli())
