"""Automated tests for CV Engine command-line interface (CLI)."""

import io
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

from sentinel_cv.cli import build_parser, run_cli


class TestCVCLI(unittest.TestCase):
    """Test suite for SentinelAI CV CLI argument parser and execution."""

    def test_build_parser_defaults(self) -> None:
        """Verify default parser values match system specifications."""
        parser = build_parser()
        args = parser.parse_args([])

        self.assertEqual(args.video, "sample-data/demo.mp4")
        self.assertEqual(args.model, "yolov8n.pt")
        self.assertEqual(args.confidence, 0.50)
        self.assertIsNone(args.max_frames)
        self.assertEqual(args.camera_id, "cam-demo-01")
        self.assertFalse(args.json)
        self.assertFalse(args.per_frame_json)

    def test_build_parser_custom_args(self) -> None:
        """Verify parsing of custom CLI flags."""
        parser = build_parser()
        custom = [
            "--video", "tests/fixtures/sample.mp4",
            "--model", "mock",
            "--confidence", "0.75",
            "--max-frames", "25",
            "--camera-id", "cam-north-01",
            "--json",
        ]
        args = parser.parse_args(custom)

        self.assertEqual(args.video, "tests/fixtures/sample.mp4")
        self.assertEqual(args.model, "mock")
        self.assertEqual(args.confidence, 0.75)
        self.assertEqual(args.max_frames, 25)
        self.assertEqual(args.camera_id, "cam-north-01")
        self.assertTrue(args.json)

    def test_run_cli_configuration_error(self) -> None:
        """Verify invalid confidence returns exit code 1."""
        exit_code = run_cli(["--confidence", "1.5"])
        self.assertEqual(exit_code, 1)

    def test_run_cli_with_mock_model_nonexistent_file(self) -> None:
        """Verify missing video file returns exit code 2."""
        exit_code = run_cli(["--video", "nonexistent_file_12345.mp4", "--model", "mock"])
        self.assertEqual(exit_code, 2)

    def test_run_cli_json_output_mode(self) -> None:
        """Verify CLI produces valid JSON output when --json flag is passed with an open source."""
        # Create a tiny dummy file to satisfy os.path.exists
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tf:
            temp_path = tf.name

        try:
            # Patch OpenCVVideoSource.open and read_frame to return mock data
            with patch("sentinel_cv.cli.OpenCVVideoSource.open", return_value=True), \
                 patch("sentinel_cv.cli.OpenCVVideoSource.read_frame", return_value=(False, None, None)), \
                 patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:

                exit_code = run_cli(["--video", temp_path, "--model", "mock", "--json"])
                self.assertEqual(exit_code, 0)

                output_str = mock_stdout.getvalue()
                parsed_json = json.loads(output_str)
                self.assertEqual(parsed_json["status"], "success")
                self.assertEqual(parsed_json["model_type"], "mock")
                self.assertEqual(parsed_json["frames_processed"], 0)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_run_cli_replay_mode(self) -> None:
        """Verify CLI executes deterministic replay mode and outputs structured summary."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            exit_code = run_cli(["--replay", "--disable-events", "--json", "--max-frames", "5"])
            self.assertEqual(exit_code, 0)

            output_str = mock_stdout.getvalue()
            parsed_json = json.loads(output_str)
            self.assertEqual(parsed_json["status"], "success")
            self.assertTrue(parsed_json["replay_mode"])
            self.assertEqual(parsed_json["model_type"], "replay")
            self.assertEqual(parsed_json["frames_processed"], 5)
            self.assertGreaterEqual(parsed_json["total_person_detections"], 1)


if __name__ == "__main__":
    unittest.main()

