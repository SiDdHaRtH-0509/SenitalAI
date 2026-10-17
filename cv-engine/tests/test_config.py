"""Automated tests for CV Engine configuration and logging setup."""

import logging
import math
import os
import unittest
from unittest.mock import patch

from sentinel_cv.config import CVConfig, ConfigurationError
from sentinel_cv.logging_config import get_logger, setup_logging


class TestCVConfig(unittest.TestCase):
    """Test suite for CVConfig dataclass, environment loading, and validation."""

    def test_default_configuration(self) -> None:
        """Verify default configuration values provide safe local defaults."""
        config = CVConfig()

        self.assertEqual(config.input_source_type, "file")
        self.assertEqual(config.video_source, "sample-data/demo.mp4")
        self.assertEqual(config.camera_id, "cam-demo-01")
        self.assertEqual(config.target_width, 1280)
        self.assertEqual(config.target_height, 720)
        self.assertAlmostEqual(config.target_fps, 10.0)
        self.assertEqual(config.log_level, "INFO")
        self.assertEqual(config.model_type, "placeholder")
        self.assertIsNone(config.model_path)
        self.assertAlmostEqual(config.confidence_threshold, 0.50)
        self.assertAlmostEqual(config.deduplication_cooldown_sec, 5.0)
        self.assertEqual(config.temporal_confirmation_frames, 3)
        self.assertFalse(config.replay_mode)
        self.assertEqual(config.backend_url, "http://localhost:8000")
        self.assertTrue(config.events_enabled)
        self.assertEqual(config.event_severity, "HIGH")
        self.assertEqual(config.api_timeout, 5.0)
        self.assertEqual(config.api_max_retries, 2)
        self.assertEqual(config.base_timestamp, "2026-10-17T09:30:00Z")

    def test_custom_valid_configuration(self) -> None:
        """Verify custom valid configuration parameters."""
        config = CVConfig(
            input_source_type="camera",
            video_source="0",
            camera_id="cam-perimeter-north",
            target_width=1920,
            target_height=1080,
            target_fps=25.0,
            log_level="DEBUG",
            confidence_threshold=0.75,
            deduplication_cooldown_sec=10.0,
            temporal_confirmation_frames=5,
            replay_mode=True,
            backend_url="http://192.168.1.100:8000",
        )

        self.assertEqual(config.input_source_type, "camera")
        self.assertEqual(config.video_source, "0")
        self.assertEqual(config.camera_id, "cam-perimeter-north")
        self.assertEqual(config.target_width, 1920)
        self.assertEqual(config.target_height, 1080)
        self.assertEqual(config.target_fps, 25.0)
        self.assertEqual(config.log_level, "DEBUG")
        self.assertEqual(config.confidence_threshold, 0.75)
        self.assertTrue(config.replay_mode)
        self.assertEqual(config.backend_url, "http://192.168.1.100:8000")

    def test_from_env_loading(self) -> None:
        """Verify configuration loading from environment variables."""
        test_env = {
            "CV_INPUT_SOURCE_TYPE": "stream",
            "CV_VIDEO_SOURCE": "rtsp://10.0.0.1:554/live",
            "CV_CAMERA_ID": "cam-gate-02",
            "CV_TARGET_WIDTH": "640",
            "CV_TARGET_HEIGHT": "480",
            "CV_TARGET_FPS": "15.5",
            "CV_LOG_LEVEL": "WARNING",
            "CV_MODEL_TYPE": "yolov8n",
            "CV_CONFIDENCE_THRESHOLD": "0.65",
            "CV_ZONE_ID": "zone-gate-02",
            "CV_DEDUPLICATION_COOLDOWN_SEC": "8.0",
            "CV_TEMPORAL_CONFIRMATION_FRAMES": "4",
            "CV_REPLAY_MODE": "true",
            "CV_BACKEND_URL": "http://api.sentinel.internal:8000",
        }

        with patch.dict(os.environ, test_env, clear=True):
            config = CVConfig.from_env()

            self.assertEqual(config.input_source_type, "stream")
            self.assertEqual(config.video_source, "rtsp://10.0.0.1:554/live")
            self.assertEqual(config.camera_id, "cam-gate-02")
            self.assertEqual(config.target_width, 640)
            self.assertEqual(config.target_height, 480)
            self.assertAlmostEqual(config.target_fps, 15.5)
            self.assertEqual(config.log_level, "WARNING")
            self.assertEqual(config.model_type, "yolov8n")
            self.assertAlmostEqual(config.confidence_threshold, 0.65)
            self.assertEqual(config.zone_id, "zone-gate-02")
            self.assertAlmostEqual(config.deduplication_cooldown_sec, 8.0)
            self.assertEqual(config.temporal_confirmation_frames, 4)
            self.assertTrue(config.replay_mode)
            self.assertEqual(config.backend_url, "http://api.sentinel.internal:8000")

    def test_invalid_input_source_type(self) -> None:
        """Verify invalid source type raises ConfigurationError."""
        with self.assertRaises(ConfigurationError) as ctx:
            CVConfig(input_source_type="unsupported_source")
        self.assertIn("Invalid input_source_type", str(ctx.exception))

    def test_empty_video_source(self) -> None:
        """Verify empty video source path raises ConfigurationError."""
        with self.assertRaises(ConfigurationError):
            CVConfig(video_source="")
        with self.assertRaises(ConfigurationError):
            CVConfig(video_source="   ")

    def test_empty_camera_id(self) -> None:
        """Verify empty camera ID raises ConfigurationError."""
        with self.assertRaises(ConfigurationError):
            CVConfig(camera_id="")
        with self.assertRaises(ConfigurationError):
            CVConfig(camera_id="   ")

    def test_invalid_target_dimensions(self) -> None:
        """Verify zero, negative, or boolean dimensions raise ConfigurationError."""
        with self.assertRaises(ConfigurationError):
            CVConfig(target_width=0)
        with self.assertRaises(ConfigurationError):
            CVConfig(target_width=-100)
        with self.assertRaises(ConfigurationError):
            CVConfig(target_width=True)  # bool is subclass of int

        with self.assertRaises(ConfigurationError):
            CVConfig(target_height=0)
        with self.assertRaises(ConfigurationError):
            CVConfig(target_height=-50)
        with self.assertRaises(ConfigurationError):
            CVConfig(target_height=False)

    def test_invalid_target_fps(self) -> None:
        """Verify non-positive, NaN, or infinite FPS raise ConfigurationError."""
        with self.assertRaises(ConfigurationError):
            CVConfig(target_fps=0.0)
        with self.assertRaises(ConfigurationError):
            CVConfig(target_fps=-5.0)
        with self.assertRaises(ConfigurationError):
            CVConfig(target_fps=float("nan"))
        with self.assertRaises(ConfigurationError):
            CVConfig(target_fps=float("inf"))
        with self.assertRaises(ConfigurationError):
            CVConfig(target_fps=True)

    def test_invalid_log_level(self) -> None:
        """Verify unknown log level raises ConfigurationError."""
        with self.assertRaises(ConfigurationError):
            CVConfig(log_level="VERBOSE")
        with self.assertRaises(ConfigurationError):
            CVConfig(log_level="TRACE")

    def test_confidence_threshold_boundaries_and_invalid(self) -> None:
        """Verify boundary values [0.0, 1.0] pass and out-of-bounds fail."""
        # Valid boundaries
        c_min = CVConfig(confidence_threshold=0.0)
        self.assertEqual(c_min.confidence_threshold, 0.0)

        c_max = CVConfig(confidence_threshold=1.0)
        self.assertEqual(c_max.confidence_threshold, 1.0)

        # Invalid: < 0
        with self.assertRaises(ConfigurationError):
            CVConfig(confidence_threshold=-0.01)

        # Invalid: > 1
        with self.assertRaises(ConfigurationError):
            CVConfig(confidence_threshold=1.01)

        # Invalid: NaN and Inf
        with self.assertRaises(ConfigurationError):
            CVConfig(confidence_threshold=float("nan"))
        with self.assertRaises(ConfigurationError):
            CVConfig(confidence_threshold=float("inf"))
        with self.assertRaises(ConfigurationError):
            CVConfig(confidence_threshold=float("-inf"))

    def test_invalid_cooldown(self) -> None:
        """Verify negative cooldown raises ConfigurationError."""
        with self.assertRaises(ConfigurationError):
            CVConfig(deduplication_cooldown_sec=-1.0)
        with self.assertRaises(ConfigurationError):
            CVConfig(deduplication_cooldown_sec=float("nan"))

    def test_invalid_temporal_confirmation_frames(self) -> None:
        """Verify frames < 1 or boolean raises ConfigurationError."""
        with self.assertRaises(ConfigurationError):
            CVConfig(temporal_confirmation_frames=0)
        with self.assertRaises(ConfigurationError):
            CVConfig(temporal_confirmation_frames=-2)
        with self.assertRaises(ConfigurationError):
            CVConfig(temporal_confirmation_frames=True)

    def test_empty_backend_url(self) -> None:
        """Verify empty backend URL raises ConfigurationError."""
        with self.assertRaises(ConfigurationError):
            CVConfig(backend_url="")

    def test_invalid_event_severity(self) -> None:
        """Verify unapproved severity raises ConfigurationError."""
        with self.assertRaises(ConfigurationError):
            CVConfig(event_severity="DANGEROUS")

    def test_invalid_api_timeout_and_retries(self) -> None:
        """Verify non-positive timeout or negative retries raise ConfigurationError."""
        with self.assertRaises(ConfigurationError):
            CVConfig(api_timeout=0.0)
        with self.assertRaises(ConfigurationError):
            CVConfig(api_timeout=-5.0)
        with self.assertRaises(ConfigurationError):
            CVConfig(api_max_retries=-1)

    def test_invalid_base_timestamp(self) -> None:
        """Verify invalid ISO base_timestamp raises ConfigurationError."""
        with self.assertRaises(ConfigurationError):
            CVConfig(base_timestamp="2026-10-17 09:30:00")



class TestLoggingConfig(unittest.TestCase):
    """Test suite for logging configuration module."""

    def test_setup_logging_idempotency(self) -> None:
        """Verify setup_logging does not duplicate stream handlers on multiple calls."""
        logger1 = setup_logging(log_level="DEBUG", logger_name="test_logger_1")
        initial_handlers_count = len(logger1.handlers)
        self.assertGreaterEqual(initial_handlers_count, 1)

        # Call again on the same logger
        logger2 = setup_logging(log_level="INFO", logger_name="test_logger_1")
        self.assertEqual(len(logger2.handlers), initial_handlers_count)
        self.assertEqual(logger2.level, logging.INFO)

    def test_get_logger_namespacing(self) -> None:
        """Verify child loggers are namespaced under 'sentinel_cv'."""
        child_logger = get_logger("video_reader")
        self.assertEqual(child_logger.name, "sentinel_cv.video_reader")

        root_logger = get_logger("sentinel_cv")
        self.assertEqual(root_logger.name, "sentinel_cv")


if __name__ == "__main__":
    unittest.main()
