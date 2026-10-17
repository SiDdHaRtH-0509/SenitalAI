"""Automated tests for BackendClient HTTP transmission and reliability controls.

Verifies:
1. Successful event transmission (HTTP 200/201).
2. Idempotent duplicate handling (HTTP 409).
3. Client error handling (HTTP 400) without unbounded retries.
4. Transient server error bounded retries (HTTP 500/503).
5. Network connection failure and timeout handling.
6. Event submission enablement flag (events_enabled=False).
7. Health check endpoint (GET /api/health).
All tests execute deterministically offline using custom mock transport.
"""

import json
import unittest
import urllib.error
import urllib.request

from sentinel_cv.backend_client import BackendClient
from sentinel_cv.models import SecurityEvent


class TestBackendClient(unittest.TestCase):
    """Test suite for BackendClient network transmission and resilience."""

    def setUp(self) -> None:
        self.sample_event = SecurityEvent(
            event_id="evt-cam01-zone01-12345678",
            camera_id="cam-demo-01",
            event_type="RESTRICTED_ZONE_ENTRY",
            timestamp="2026-10-17T09:30:00Z",
            severity="HIGH",
            confidence=0.92,
            zone_id="zone-restricted-01",
            description="Person detected in restricted buffer",
            evidence={"class_name": "person", "track_id": None, "frame_number": 50},
        )

    def test_successful_event_submission_200(self) -> None:
        """Verify successful HTTP 200 response returns success=True and parsed payload."""
        response_body = json.dumps({
            "event_id": "evt-cam01-zone01-12345678",
            "risk_score": 75,
            "risk_level": "HIGH",
            "reasons": ["Restricted zone entry"],
            "status": "NEW",
        }).encode("utf-8")

        def mock_transport(req: urllib.request.Request, timeout: float):
            self.assertEqual(req.get_method(), "POST")
            self.assertIn("/api/events", req.full_url)
            self.assertEqual(req.headers.get("Content-type"), "application/json")
            return 200, response_body, {}

        client = BackendClient(base_url="http://mock-backend:8000", transport=mock_transport)
        result = client.submit_event(self.sample_event)

        self.assertTrue(result.success)
        self.assertEqual(result.status_code, 200)
        self.assertIsNotNone(result.response_data)
        self.assertEqual(result.response_data["risk_score"], 75)
        self.assertFalse(result.idempotent_duplicate)

    def test_idempotent_duplicate_submission_409(self) -> None:
        """Verify HTTP 409 response is recognized as a successful idempotent duplicate."""
        response_body = json.dumps({
            "event_id": "evt-cam01-zone01-12345678",
            "status": "NEW",
            "message": "Duplicate event ID acknowledged",
        }).encode("utf-8")

        def mock_transport(req: urllib.request.Request, timeout: float):
            return 409, response_body, {}

        client = BackendClient(base_url="http://mock-backend:8000", transport=mock_transport)
        result = client.submit_event(self.sample_event)

        self.assertTrue(result.success)
        self.assertEqual(result.status_code, 409)
        self.assertTrue(result.idempotent_duplicate)

    def test_client_error_400_no_retry(self) -> None:
        """Verify HTTP 400 client error fails immediately without retrying."""
        calls = []

        def mock_transport(req: urllib.request.Request, timeout: float):
            calls.append(req)
            return 400, b'{"error":"Invalid payload"}', {}

        client = BackendClient(
            base_url="http://mock-backend:8000",
            max_retries=3,
            transport=mock_transport,
        )
        result = client.submit_event(self.sample_event)

        self.assertFalse(result.success)
        self.assertEqual(result.status_code, 400)
        # MUST only call once (no retries on 4xx)
        self.assertEqual(len(calls), 1)

    def test_server_error_500_bounded_retries(self) -> None:
        """Verify HTTP 500 server error triggers bounded retries up to max_retries."""
        calls = []

        def mock_transport(req: urllib.request.Request, timeout: float):
            calls.append(req)
            return 500, b'{"error":"Internal Server Error"}', {}

        client = BackendClient(
            base_url="http://mock-backend:8000",
            max_retries=2,
            retry_backoff_seconds=0.01,
            transport=mock_transport,
        )
        result = client.submit_event(self.sample_event)

        self.assertFalse(result.success)
        self.assertEqual(result.status_code, 500)
        # initial attempt + 2 retries = 3 calls total
        self.assertEqual(len(calls), 3)

    def test_server_error_retry_success(self) -> None:
        """Verify retry succeeds when server error recovers on second attempt."""
        calls = []

        def mock_transport(req: urllib.request.Request, timeout: float):
            calls.append(req)
            if len(calls) == 1:
                return 503, b"Service Unavailable", {}
            return 201, b'{"status":"NEW"}', {}

        client = BackendClient(
            base_url="http://mock-backend:8000",
            max_retries=2,
            retry_backoff_seconds=0.01,
            transport=mock_transport,
        )
        result = client.submit_event(self.sample_event)

        self.assertTrue(result.success)
        self.assertEqual(result.status_code, 201)
        self.assertEqual(len(calls), 2)

    def test_network_connection_failure(self) -> None:
        """Verify network connection drop fails cleanly with descriptive error."""
        calls = []

        def mock_transport(req: urllib.request.Request, timeout: float):
            calls.append(req)
            raise urllib.error.URLError("Connection refused [Errno 111]")

        client = BackendClient(
            base_url="http://unreachable-host:8000",
            max_retries=1,
            retry_backoff_seconds=0.01,
            transport=mock_transport,
        )
        result = client.submit_event(self.sample_event)

        self.assertFalse(result.success)
        self.assertIn("Connection refused", result.error_message)
        self.assertEqual(len(calls), 2)

    def test_events_disabled_returns_early(self) -> None:
        """Verify events_enabled=False bypasses network calls and returns early."""
        calls = []

        def mock_transport(req: urllib.request.Request, timeout: float):
            calls.append(req)
            return 200, b"{}", {}

        client = BackendClient(
            base_url="http://mock-backend:8000",
            events_enabled=False,
            transport=mock_transport,
        )
        result = client.submit_event(self.sample_event)

        self.assertTrue(result.success)
        self.assertEqual(len(calls), 0)
        self.assertIn("disabled", result.error_message)

    def test_check_health_success_and_failure(self) -> None:
        """Verify check_health queries /api/health and handles success and error codes."""
        # Success
        def success_transport(req: urllib.request.Request, timeout: float):
            self.assertIn("/api/health", req.full_url)
            return 200, b'{"status":"ok"}', {}

        client = BackendClient(base_url="http://mock-backend:8000", transport=success_transport)
        healthy, msg = client.check_health()
        self.assertTrue(healthy)
        self.assertIn("status=ok", msg)

        # Failure 503
        def fail_transport(req: urllib.request.Request, timeout: float):
            return 503, b"Service Unavailable", {}

        client_fail = BackendClient(base_url="http://mock-backend:8000", transport=fail_transport)
        healthy, msg = client_fail.check_health()
        self.assertFalse(healthy)
        self.assertIn("503", msg)


if __name__ == "__main__":
    unittest.main()
