"""Backend HTTP client for SentinelAI CV Engine.

Transmits structured SecurityEvents to the shared SentinelAI backend service
conforming strictly to API_CONTRACT.md.

Key Features & Reliability Controls:
1. Standard Library Only: Built using standard Python urllib.request (zero third-party
   network dependencies), ensuring 100% portability to IBM LinuxONE (s390x).
2. Explicit Timeouts: Prevents hanging threads with configurable connection and read timeouts.
3. Bounded Retries: Bounded exponential backoff for transient network drops and 5xx server
   errors; client errors (4xx) are never retried.
4. Idempotency Support: Treats duplicate event responses (HTTP 409 or acknowledged duplicates)
   as successful idempotent submissions per contract rules.
5. Injected Transport: Supports custom transport injection for 100% deterministic, offline
   automated unit tests without live network sockets.
6. Safe Logging: Never logs sensitive credentials or authorization headers.
"""

import json
import logging
import os
from pathlib import Path
import socket
import time
from typing import Any, Callable, Dict, Optional, Tuple
import urllib.error
import urllib.request

from sentinel_cv.interfaces import IBackendClient
from sentinel_cv.logging_config import get_logger
from sentinel_cv.models import EventSubmissionResult, SecurityEvent


def _load_dotenv_if_present() -> None:
    """Load environment variables from .env if present without external dependencies."""
    search_paths = [Path.cwd() / ".env"] + [p / ".env" for p in Path(__file__).resolve().parents]
    for env_path in search_paths:
        if env_path.is_file():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip("'\"")
                        if key and key not in os.environ:
                            os.environ[key] = val
                break
            except Exception:
                pass


_load_dotenv_if_present()

# Transport callable signature: (Request, timeout) -> (status_code, response_bytes, headers_dict)
TransportFunc = Callable[[urllib.request.Request, float], Tuple[int, bytes, Dict[str, str]]]


def default_urllib_transport(
    request: urllib.request.Request,
    timeout: float,
) -> Tuple[int, bytes, Dict[str, str]]:
    """Default transport executing HTTP requests via urllib.request.urlopen."""
    with urllib.request.urlopen(request, timeout=timeout) as response:
        status_code = getattr(response, "status", 200)
        body = response.read()
        headers = dict(response.headers)
        return status_code, body, headers


class BackendClient(IBackendClient):
    """Client for transmitting security events to the SentinelAI backend API."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout_seconds: float = 5.0,
        max_retries: int = 2,
        retry_backoff_seconds: float = 0.5,
        events_enabled: bool = True,
        api_key: Optional[str] = None,
        transport: Optional[TransportFunc] = None,
    ) -> None:
        """Initialize the backend client.

        Args:
            base_url: Base URL of backend service (e.g., 'http://localhost:8000').
            timeout_seconds: Network connection and read timeout in seconds.
            max_retries: Maximum number of bounded retries for transient errors.
            retry_backoff_seconds: Initial backoff duration between retries.
            events_enabled: If False, event submission is disabled and returns early.
            api_key: Optional explicit M2M service key.
            transport: Optional custom transport function for deterministic testing.
        """
        if not base_url or not str(base_url).strip():
            raise ValueError("base_url must be a non-empty string.")
        if timeout_seconds <= 0.0:
            raise ValueError("timeout_seconds must be a positive number.")
        if max_retries < 0:
            raise ValueError("max_retries must be an integer >= 0.")
        if retry_backoff_seconds < 0.0:
            raise ValueError("retry_backoff_seconds must be non-negative.")

        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds
        self.events_enabled = events_enabled
        self.api_key = (
            api_key
            or os.getenv("SENTINEL_SERVICE_API_KEY")
            or os.getenv("SENTINEL_API_KEY")
            or os.getenv("SENTINEL_SERVICE_TOKEN")
            or ""
        )
        self._transport = transport or default_urllib_transport
        self.logger = get_logger("backend_client")

    def check_health(self) -> Tuple[bool, str]:
        """Check backend service connectivity via GET /api/health.

        Returns:
            Tuple[bool, str]: (is_healthy, status_message)
        """
        url = f"{self.base_url}/api/health"
        req = urllib.request.Request(url, method="GET")
        req.add_header("Accept", "application/json")
        req.add_header("User-Agent", "SentinelAI-CV-Engine/1.0")
        if self.api_key:
            req.add_header("Authorization", f"Bearer {self.api_key}")
            req.add_header("X-API-Key", self.api_key)

        try:
            status_code, body, _ = self._transport(req, self.timeout_seconds)
            if status_code == 200:
                try:
                    data = json.loads(body.decode("utf-8"))
                    if data.get("status") == "ok":
                        return True, "Backend healthy (status=ok)"
                except Exception:
                    pass
                return True, f"Backend responsive (HTTP {status_code})"
            return False, f"Backend health returned HTTP {status_code}"
        except urllib.error.HTTPError as http_err:
            return False, f"Backend health HTTP error: {http_err.code}"
        except urllib.error.URLError as url_err:
            return False, f"Backend connection failed: {url_err.reason}"
        except Exception as exc:
            return False, f"Backend health check error: {exc}"

    def submit_event(self, event: SecurityEvent) -> EventSubmissionResult:
        """Submit a single SecurityEvent to POST /api/events.

        Args:
            event: Validated SecurityEvent instance.

        Returns:
            EventSubmissionResult: Result of the submission attempt.
        """
        if not isinstance(event, SecurityEvent):
            raise ValueError(f"event must be a SecurityEvent instance, got: {type(event).__name__}")

        if not self.events_enabled:
            self.logger.debug(
                "Event submission disabled by configuration. Event '%s' retained locally.",
                event.event_id,
            )
            return EventSubmissionResult(
                event_id=event.event_id,
                success=True,
                status_code=0,
                error_message="Event submission disabled by configuration",
            )

        url = f"{self.base_url}/api/events"
        payload_bytes = json.dumps(event.to_dict()).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "SentinelAI-CV-Engine/1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["X-API-Key"] = self.api_key

        req = urllib.request.Request(
            url,
            data=payload_bytes,
            headers=headers,
            method="POST",
        )

        last_status = 0
        last_error: Optional[str] = None
        backoff = self.retry_backoff_seconds

        for attempt in range(self.max_retries + 1):
            try:
                status_code, body, _ = self._transport(req, self.timeout_seconds)
                last_status = status_code

                # Parse response body
                response_data = None
                if body:
                    try:
                        response_data = json.loads(body.decode("utf-8"))
                    except Exception:
                        response_data = {"raw_response": body.decode("utf-8", errors="replace")}

                # 200 OK or 201 Created -> Success
                if status_code in {200, 201}:
                    self.logger.info(
                        "Event '%s' successfully submitted to backend (HTTP %d).",
                        event.event_id,
                        status_code,
                    )
                    return EventSubmissionResult(
                        event_id=event.event_id,
                        success=True,
                        status_code=status_code,
                        response_data=response_data,
                    )

                # 409 Conflict -> Idempotent duplicate handled per contract
                if status_code == 409:
                    self.logger.info(
                        "Event '%s' already recorded by backend (HTTP 409 idempotent duplicate).",
                        event.event_id,
                    )
                    return EventSubmissionResult(
                        event_id=event.event_id,
                        success=True,
                        status_code=status_code,
                        response_data=response_data,
                        idempotent_duplicate=True,
                    )

                # 4xx Client Errors -> Do NOT retry (malformed request, rejected schema)
                if 400 <= status_code < 500:
                    err_msg = f"Backend rejected event with client error HTTP {status_code}"
                    self.logger.error("Client error submitting event '%s': %s", event.event_id, err_msg)
                    return EventSubmissionResult(
                        event_id=event.event_id,
                        success=False,
                        status_code=status_code,
                        response_data=response_data,
                        error_message=err_msg,
                    )

                # 5xx Server Errors -> Transient candidate for bounded retry
                last_error = f"Backend server error HTTP {status_code}"
                self.logger.warning(
                    "Attempt %d/%d failed with HTTP %d for event '%s'.",
                    attempt + 1,
                    self.max_retries + 1,
                    status_code,
                    event.event_id,
                )

            except urllib.error.HTTPError as http_err:
                last_status = http_err.code
                err_body = http_err.read().decode("utf-8", errors="replace") if hasattr(http_err, "read") else ""
                
                # Check for 409 idempotent duplicate
                if http_err.code == 409:
                    self.logger.info(
                        "Event '%s' recognized as idempotent duplicate (HTTP 409).",
                        event.event_id,
                    )
                    return EventSubmissionResult(
                        event_id=event.event_id,
                        success=True,
                        status_code=409,
                        error_message=err_body,
                        idempotent_duplicate=True,
                    )

                # 4xx Non-retryable
                if 400 <= http_err.code < 500:
                    err_msg = f"HTTP {http_err.code}: {http_err.reason} - {err_body}"
                    self.logger.error("Non-retryable HTTP error for event '%s': %s", event.event_id, err_msg)
                    return EventSubmissionResult(
                        event_id=event.event_id,
                        success=False,
                        status_code=http_err.code,
                        error_message=err_msg,
                    )

                last_error = f"HTTP {http_err.code}: {http_err.reason}"
                self.logger.warning(
                    "Attempt %d/%d failed with HTTP %d for event '%s'.",
                    attempt + 1,
                    self.max_retries + 1,
                    http_err.code,
                    event.event_id,
                )

            except (urllib.error.URLError, socket.timeout, TimeoutError) as net_err:
                last_error = f"Network connection error: {net_err}"
                self.logger.warning(
                    "Attempt %d/%d network error for event '%s': %s",
                    attempt + 1,
                    self.max_retries + 1,
                    event.event_id,
                    net_err,
                )

            except Exception as unk_err:
                last_error = f"Unexpected submission error: {unk_err}"
                self.logger.error(
                    "Unexpected error submitting event '%s': %s",
                    event.event_id,
                    unk_err,
                )
                break

            # Bounded retry backoff sleep
            if attempt < self.max_retries:
                time.sleep(backoff)
                backoff *= 2.0

        fail_summary = f"Event submission failed after {self.max_retries + 1} attempts: {last_error}"
        self.logger.error("Final submission failure for '%s': %s", event.event_id, fail_summary)
        return EventSubmissionResult(
            event_id=event.event_id,
            success=False,
            status_code=last_status,
            error_message=fail_summary,
        )
