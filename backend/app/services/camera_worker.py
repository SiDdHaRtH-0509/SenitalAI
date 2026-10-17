"""Continuous video processing worker service for SentinelAI.

Manages background camera workers that ingest live RTSP or video feeds,
perform person detection (YOLOv8n / replay fallback), evaluate restricted-zone
incursions, and transmit structured security events to the FastAPI backend.

Features:
- Thread-safe decoupled architecture: Frame acquisition and inference run asynchronously.
- Bounded queue with frame-dropping policy (Queue maxsize=2) preventing memory accumulation and lag.
- Exception isolation: Any stream failure or inference crash is isolated and never crashes the backend.
- Comprehensive telemetry: FPS, inference latency, frames processed, events emitted, reconnect count.
- Deterministic replay fallback mode for testing and offline environments.
"""

from datetime import datetime, timezone
import logging
from pathlib import Path
import queue
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

try:
    import cv2
except ImportError:
    cv2 = None

# Ensure cv-engine/src is available on sys.path
for _parent in Path(__file__).resolve().parents:
    _candidate = _parent / "cv-engine" / "src"
    if _candidate.is_dir() and str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))
        break

from app.config import settings
from app.models.camera import CameraModel
from app.models.zone import ZoneModel
from app.schemas.camera import CameraWorkerStatus, redact_uri

try:
    from sentinel_cv.backend_client import BackendClient
    from sentinel_cv.detector import create_detector, create_replay_detector
    from sentinel_cv.event_generator import EventGenerator
    from sentinel_cv.models import BoundingBox, Detection, FrameMetadata, SecurityEvent
    from sentinel_cv.rtsp_source import RTSPConnectionState, RTSPVideoSource, is_rtsp_url, redact_stream_url
    from sentinel_cv.video_source import OpenCVVideoSource, ReplayVideoSource
    from sentinel_cv.zone import PolygonZone, ZoneAnalyzer
except ImportError as imp_err:
    logging.getLogger("sentinel.worker").error("Could not import sentinel_cv components: %s", imp_err)

logger = logging.getLogger("sentinel.camera_worker")


class CameraWorker:
    """Active background worker for a single surveillance camera stream."""

    def __init__(
        self,
        camera_id: str,
        stream_uri: Optional[str] = None,
        zone_id: Optional[str] = None,
        zone_vertices: Optional[List[List[float]]] = None,
        reference_strategy: str = "bottom_center",
        backend_url: Optional[str] = None,
        api_key: Optional[str] = None,
        replay_mode: bool = False,
        target_fps: float = 15.0,
    ) -> None:
        self.camera_id: str = camera_id
        self.stream_uri: Optional[str] = stream_uri
        self.stream_uri_redacted: Optional[str] = redact_uri(stream_uri) if stream_uri else None
        self.zone_id: Optional[str] = zone_id
        self.zone_vertices: List[List[float]] = zone_vertices or [[0.2, 0.4], [0.8, 0.4], [0.8, 0.85], [0.2, 0.85]]
        self.reference_strategy: str = reference_strategy
        self.backend_url: str = (backend_url or "http://127.0.0.1:8000").rstrip("/")
        self.api_key: str = api_key or settings.SERVICE_API_KEY
        self.replay_mode: bool = replay_mode
        self.target_fps: float = target_fps

        # Concurrency & queue controls
        self._stop_event = threading.Event()
        self._frame_queue: queue.Queue = queue.Queue(maxsize=2)
        self._capture_thread: Optional[threading.Thread] = None
        self._inference_thread: Optional[threading.Thread] = None

        # Metrics (thread-safe updates)
        self._lock = threading.Lock()
        self._is_running: bool = False
        self._connection_state: str = "STOPPED"
        self._frames_processed: int = 0
        self._events_emitted: int = 0
        self._reconnect_count: int = 0
        self._fps: float = 0.0
        self._latency_ms: float = 0.0
        self._last_frame_timestamp: Optional[str] = None
        self._error_message: Optional[str] = None
        self._last_snapshot_jpeg: Optional[bytes] = None

        # Internal video source handle
        self._video_source: Optional[Any] = None

    def get_snapshot(self) -> Optional[bytes]:
        """Return the most recent JPEG frame snapshot if available."""
        with self._lock:
            return self._last_snapshot_jpeg

    def start(self) -> None:
        """Start acquisition and processing worker threads."""
        with self._lock:
            if self._is_running:
                logger.info("Camera worker for %s is already active.", self.camera_id)
                return

            self._stop_event.clear()
            # Drain any stale frames
            while not self._frame_queue.empty():
                try:
                    self._frame_queue.get_nowait()
                except queue.Empty:
                    break

            self._is_running = True
            self._connection_state = "CONNECTING"
            self._error_message = None

            # Launch capture thread
            self._capture_thread = threading.Thread(
                target=self._run_capture_loop,
                name=f"Worker-Capture-{self.camera_id}",
                daemon=True,
            )
            # Launch inference thread
            self._inference_thread = threading.Thread(
                target=self._run_inference_loop,
                name=f"Worker-Inference-{self.camera_id}",
                daemon=True,
            )

            self._capture_thread.start()
            self._inference_thread.start()
            logger.info("Started background processing worker for camera %s", self.camera_id)

    def stop(self, timeout: float = 3.0) -> None:
        """Gracefully stop worker threads and release resources."""
        with self._lock:
            if not self._is_running:
                self._connection_state = "STOPPED"
                return

            logger.info("Stopping camera worker for %s...", self.camera_id)
            self._stop_event.set()
            self._is_running = False

        # Close video source to unblock any waiting reads
        if self._video_source is not None:
            try:
                self._video_source.close()
            except Exception as close_err:
                logger.debug("Error closing video source on stop: %s", close_err)

        # Wait for threads to terminate
        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=timeout)
        if self._inference_thread and self._inference_thread.is_alive():
            self._inference_thread.join(timeout=timeout)

        with self._lock:
            self._connection_state = "STOPPED"
            self._fps = 0.0
            logger.info("Camera worker for %s stopped successfully.", self.camera_id)

    def get_status(self) -> CameraWorkerStatus:
        """Get current operational metrics snapshot."""
        with self._lock:
            # Sync reconnect count from source if active
            reconnects = self._reconnect_count
            if self._video_source and hasattr(self._video_source, "reconnect_count"):
                reconnects = self._video_source.reconnect_count

            return CameraWorkerStatus(
                camera_id=self.camera_id,
                is_running=self._is_running,
                connection_state=self._connection_state,
                fps=round(self._fps, 2),
                latency_ms=round(self._latency_ms, 2),
                frames_processed=self._frames_processed,
                events_emitted=self._events_emitted,
                reconnect_count=reconnects,
                last_frame_timestamp=self._last_frame_timestamp,
                error_message=self._error_message,
                stream_uri_redacted=self.stream_uri_redacted,
                is_demo=self.replay_mode,
            )

    def _init_video_source(self) -> Any:
        """Initialize appropriate video source based on configuration."""
        if self.replay_mode or not self.stream_uri:
            logger.info("Using ReplayVideoSource for camera %s (replay_mode=%s)",
                        self.camera_id, self.replay_mode)
            return ReplayVideoSource(
                total_frames=1000000,
                fps=self.target_fps,
                width=1280,
                height=720,
                source_id=self.camera_id,
            )

        if is_rtsp_url(self.stream_uri):
            logger.info("Initializing RTSPVideoSource for camera %s: %s",
                        self.camera_id, self.stream_uri_redacted)
            return RTSPVideoSource(
                url=self.stream_uri,
                source_id=self.camera_id,
                fallback_fps=self.target_fps,
                synthetic_fallback=self.replay_mode,
            )

        return OpenCVVideoSource(
            source=self.stream_uri,
            source_id=self.camera_id,
            fallback_fps=self.target_fps,
        )

    def _run_capture_loop(self) -> None:
        """Decoupled frame capture loop running on dedicated thread."""
        try:
            self._video_source = self._init_video_source()
            if not self._video_source.open():
                with self._lock:
                    self._connection_state = "FAILED"
                    self._error_message = f"Failed to open stream: {self.stream_uri_redacted}"
                return

            with self._lock:
                self._connection_state = "CONNECTED"

            target_interval = 1.0 / self.target_fps if self.target_fps > 0 else 0.05

            while not self._stop_event.is_set():
                t_start = time.monotonic()
                ok, frame, metadata = self._video_source.read_frame()

                if not ok or frame is None or metadata is None:
                    # Update connection state from source if RTSP
                    if hasattr(self._video_source, "connection_state"):
                        src_state = str(self._video_source.connection_state.value if hasattr(self._video_source.connection_state, "value") else self._video_source.connection_state)
                        with self._lock:
                            self._connection_state = src_state
                    time.sleep(0.1)
                    continue

                with self._lock:
                    self._connection_state = "CONNECTED"

                # Enqueue frame with non-blocking drop policy
                try:
                    self._frame_queue.put_nowait((frame, metadata))
                except queue.Full:
                    # Discard oldest frame to preserve real-time low latency
                    try:
                        self._frame_queue.get_nowait()
                    except queue.Empty:
                        pass
                    try:
                        self._frame_queue.put_nowait((frame, metadata))
                    except queue.Full:
                        pass

                # Rate limiting for file or replay sources
                elapsed = time.monotonic() - t_start
                if elapsed < target_interval:
                    time.sleep(target_interval - elapsed)

        except Exception as exc:
            logger.error("Capture loop error for camera %s: %s", self.camera_id, exc, exc_info=True)
            with self._lock:
                self._connection_state = "ERROR"
                self._error_message = str(exc)
        finally:
            if self._video_source:
                try:
                    self._video_source.close()
                except Exception:
                    pass

    def _run_inference_loop(self) -> None:
        """Inference and event detection loop running on dedicated thread."""
        # 1. Initialize detector
        detector = None
        try:
            if self.replay_mode:
                detector = create_replay_detector()
            else:
                try:
                    from sentinel_cv.config import CVConfig
                    cfg = CVConfig(model_type="yolo", model_path="yolov8n.pt", confidence_threshold=0.45)
                    detector = create_detector(cfg)
                    if hasattr(detector, "load_model") and not detector.is_ready():
                        detector.load_model()
                except Exception as det_err:
                    logger.warning("Could not load YOLO detector for camera %s: %s. Using replay detector.",
                                   self.camera_id, det_err)
                    detector = create_replay_detector()
        except Exception as e:
            logger.error("Detector initialization failure: %s", e)
            detector = create_replay_detector()

        # 2. Initialize zone analyzer
        scaled_vertices = []
        for pt in self.zone_vertices:
            vx, vy = float(pt[0]), float(pt[1])
            # If coordinates are normalized in [0.0, 1.0], scale to standard 1280x720 frame space
            if vx <= 1.0 and vy <= 1.0:
                scaled_vertices.append((vx * 1280.0, vy * 720.0))
            else:
                scaled_vertices.append((vx, vy))

        zone_obj = PolygonZone(
            zone_id=self.zone_id or f"zone-{self.camera_id}",
            name=f"Zone for {self.camera_id}",
            vertices=tuple(scaled_vertices),
            enabled=True,
        )
        zone_analyzer = ZoneAnalyzer(zones=[zone_obj], reference_point_strategy=self.reference_strategy)

        # 3. Initialize event generator & backend client
        event_gen = EventGenerator(
            camera_id=self.camera_id,
            severity="HIGH",
            temporal_confirmation_frames=2,
            deduplication_cooldown_sec=5.0,
        )
        backend_client = BackendClient(
            base_url=self.backend_url,
            timeout_seconds=3.0,
            api_key=self.api_key,
        )

        # Telemetry tracking window
        last_metric_time = time.monotonic()
        frames_since_metric = 0

        try:
            while not self._stop_event.is_set():
                try:
                    frame, metadata = self._frame_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                t0 = time.monotonic()

                # Generate lightweight JPEG snapshot for live operator inspection
                if frame is not None and cv2 is not None and hasattr(frame, "shape"):
                    try:
                        ok_enc, enc = cv2.imencode(".jpg", frame)
                        if ok_enc:
                            with self._lock:
                                self._last_snapshot_jpeg = enc.tobytes()
                    except Exception:
                        pass

                # A. Object detection
                detections = detector.detect(frame, metadata)

                # B. Zone spatial intersection
                zone_results = []
                if detections:
                    zone_results = zone_analyzer.evaluate(detections, metadata)

                # C. Event generation & deduplication
                events: List[SecurityEvent] = []
                if zone_results:
                    events = event_gen.process_zone_results(zone_results, metadata)

                # D. Submit events to backend
                if events:
                    for ev in events:
                        try:
                            res = backend_client.submit_event(ev)
                            if res.success:
                                logger.info("Event submitted for %s: %s", self.camera_id, ev.event_id)
                        except Exception as sub_err:
                            logger.warning("Failed to submit event: %s", sub_err)

                inference_time_ms = (time.monotonic() - t0) * 1000.0

                # E. Update metrics
                with self._lock:
                    self._frames_processed += 1
                    frames_since_metric += 1
                    self._events_emitted += len(events)
                    self._last_frame_timestamp = datetime.now(timezone.utc).isoformat()
                    # Exponential smoothing for latency
                    self._latency_ms = (
                        inference_time_ms
                        if self._latency_ms == 0.0
                        else 0.8 * self._latency_ms + 0.2 * inference_time_ms
                    )

                    now = time.monotonic()
                    elapsed = now - last_metric_time
                    if elapsed >= 1.0:
                        self._fps = frames_since_metric / elapsed
                        frames_since_metric = 0
                        last_metric_time = now

        except Exception as exc:
            logger.error("Inference loop error for camera %s: %s", self.camera_id, exc, exc_info=True)
            with self._lock:
                self._connection_state = "ERROR"
                self._error_message = str(exc)


class CameraWorkerManager:
    """Singleton registry coordinating camera worker lifecycles."""

    def __init__(self) -> None:
        self._workers: Dict[str, CameraWorker] = {}
        self._lock = threading.Lock()

    def start_camera(
        self,
        camera: CameraModel,
        zone: Optional[ZoneModel] = None,
        replay_mode: bool = False,
    ) -> CameraWorkerStatus:
        """Start or restart a camera worker thread."""
        with self._lock:
            cid = camera.camera_id
            if cid in self._workers and self._workers[cid]._is_running:
                logger.info("Worker for %s is already running.", cid)
                return self._workers[cid].get_status()

            # Extract zone configuration
            zone_vertices = zone.vertices if zone else [[0.2, 0.4], [0.8, 0.4], [0.8, 0.85], [0.2, 0.85]]
            ref_strategy = zone.reference_strategy if zone else "bottom_center"
            zid = zone.zone_id if zone else camera.zone_id

            worker = CameraWorker(
                camera_id=cid,
                stream_uri=camera.stream_uri,
                zone_id=zid,
                zone_vertices=zone_vertices,
                reference_strategy=ref_strategy,
                backend_url="http://127.0.0.1:8000",
                api_key=settings.SERVICE_API_KEY,
                replay_mode=replay_mode,
                target_fps=camera.fps or 15.0,
            )
            worker.start()
            self._workers[cid] = worker
            return worker.get_status()

    def stop_camera(self, camera_id: str) -> CameraWorkerStatus:
        """Stop an active camera worker."""
        with self._lock:
            worker = self._workers.get(camera_id)
            if worker:
                worker.stop()
                status = worker.get_status()
                return status

            return CameraWorkerStatus(
                camera_id=camera_id,
                is_running=False,
                connection_state="STOPPED",
            )

    def get_status(self, camera_id: str) -> CameraWorkerStatus:
        """Get the current operational status for a camera worker."""
        with self._lock:
            worker = self._workers.get(camera_id)
            if worker:
                return worker.get_status()
            return CameraWorkerStatus(
                camera_id=camera_id,
                is_running=False,
                connection_state="STOPPED",
            )

    def get_all_statuses(self) -> Dict[str, CameraWorkerStatus]:
        """Get status dictionary for all registered workers."""
        with self._lock:
            return {cid: worker.get_status() for cid, worker in self._workers.items()}

    def get_camera_snapshot(self, camera_id: str) -> Optional[bytes]:
        """Retrieve latest JPEG snapshot bytes for a camera worker."""
        with self._lock:
            worker = self._workers.get(camera_id)
            if worker:
                return worker.get_snapshot()
            return None

    def stop_all(self) -> None:
        """Stop all running camera workers during shutdown."""
        with self._lock:
            workers = list(self._workers.values())

        for worker in workers:
            try:
                worker.stop()
            except Exception as e:
                logger.error("Error stopping worker %s: %s", worker.camera_id, e)


# Global singleton instance
worker_manager = CameraWorkerManager()
