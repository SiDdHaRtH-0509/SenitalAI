"""Command-line interface (CLI) for SentinelAI Computer Vision Engine.

Allows running video processing and person detection on local video files
or live camera inputs with concise diagnostic summaries.

Usage:
    python -m sentinel_cv.cli --video sample-data/demo.mp4 --max-frames 100
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


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CV engine CLI."""
    parser = argparse.ArgumentParser(
        prog="sentinel_cv",
        description="SentinelAI CV Engine — Video Ingestion and Person Detection CLI",
    )
    parser.add_argument(
        "--video",
        type=str,
        default="sample-data/demo.mp4",
        help="Path to input video file or camera device index (default: sample-data/demo.mp4)",
    )
    parser.add_argument(
        "--model",
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
        help="Output structured per-frame detections (for testing/integration)",
    )
    return parser


def run_cli(args: Optional[List[str]] = None) -> int:
    """Execute the CLI with provided arguments.

    Returns:
        int: Exit status code (0 for success, non-zero for error).
    """
    parser = build_parser()
    parsed = parser.parse_args(args)

    setup_logging(log_level=parsed.log_level)
    logger = get_logger("cli")

    # Build config
    model_type = "mock" if parsed.model.lower() in {"mock", "test"} else "yolo"
    try:
        config = CVConfig(
            input_source_type="file",
            video_source=parsed.video,
            camera_id=parsed.camera_id,
            log_level=parsed.log_level,
            model_type=model_type,
            model_path=parsed.model,
            confidence_threshold=parsed.confidence,
        )
    except ConfigurationError as cfg_err:
        logger.error("Configuration error: %s", cfg_err)
        return 1

    # Wire pipeline components
    try:
        source = OpenCVVideoSource(
            source=parsed.video,
            source_id=parsed.camera_id,
            fallback_fps=parsed.fps,
        )
        detector = create_detector(config)
        pipeline = CVPipeline(config=config, video_source=source, detector=detector)
        pipeline.initialize()
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

    try:
        for result in pipeline.process_stream(max_frames=parsed.max_frames):
            frames_processed += 1
            person_count = len(result.detections)
            total_person_detections += person_count

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
        "model_type": config.model_type,
        "model_path": config.model_path,
        "confidence_threshold": config.confidence_threshold,
        "frames_processed": frames_processed,
        "total_person_detections": total_person_detections,
        "elapsed_seconds": round(elapsed_time, 3),
        "average_fps": round(avg_fps, 2),
    }

    if parsed.json:
        print(json.dumps(summary, indent=2))
    else:
        print("\n========================================================")
        print(" SENTINELAI CV ENGINE — VIDEO PROCESSING SUMMARY")
        print("========================================================")
        print(f" Video Source:            {summary['video_source']}")
        print(f" Camera ID:               {summary['camera_id']}")
        print(f" Model Type:              {summary['model_type']} ({summary['model_path']})")
        print(f" Confidence Threshold:    {summary['confidence_threshold']}")
        print(f" Frames Processed:        {summary['frames_processed']}")
        print(f" Total Person Detections: {summary['total_person_detections']}")
        print(f" Processing Time:         {summary['elapsed_seconds']}s")
        print(f" Average Processing FPS:  {summary['average_fps']} FPS")
        print("========================================================\n")

    return 0


if __name__ == "__main__":
    sys.exit(run_cli())
