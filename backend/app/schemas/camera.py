"""Pydantic schemas for Camera edge devices and real-time processing workers."""

import re
from typing import Optional
import urllib.parse
from pydantic import BaseModel, ConfigDict, Field, field_validator


def redact_uri(v: Optional[str]) -> Optional[str]:
    """Redact passwords from stream URIs for safe API delivery."""
    if not v or not isinstance(v, str):
        return v
    try:
        p = urllib.parse.urlsplit(v)
        if p.password:
            netloc = f"{p.username}:***@{p.hostname}"
            if p.port:
                netloc += f":{p.port}"
            return urllib.parse.urlunsplit((p.scheme, netloc, p.path, p.query, p.fragment))
        return v
    except Exception:
        return re.sub(r"://([^:@]+):([^@]+)@", r"://\1:***@", v)


class CameraWorkerStatus(BaseModel):
    """Real-time operational metrics and connection state for a camera worker."""

    camera_id: str
    is_running: bool = False
    connection_state: str = "STOPPED"
    fps: float = 0.0
    latency_ms: float = 0.0
    frames_processed: int = 0
    events_emitted: int = 0
    reconnect_count: int = 0
    last_frame_timestamp: Optional[str] = None
    error_message: Optional[str] = None
    stream_uri_redacted: Optional[str] = None
    is_demo: bool = False

    model_config = ConfigDict(from_attributes=True)


class CameraStartRequest(BaseModel):
    """Payload to start a camera processing worker."""

    replay_mode: bool = Field(
        False,
        description="Whether to execute in synthetic replay/demo mode if live RTSP is unreachable"
    )


class CameraCreate(BaseModel):
    """Payload schema to register or configure a camera device."""

    camera_id: str = Field(..., min_length=1, description="Unique camera hardware identifier")
    name: str = Field(..., min_length=1, description="Friendly camera label or sector name")
    location: str = Field(..., min_length=1, description="Physical installation site description")
    status: str = Field("ONLINE", description="Operational state (ONLINE, OFFLINE, DISCONNECTED)")
    resolution: str = Field("1920x1080", description="Sensor frame dimensions (e.g. 1920x1080)")
    fps: float = Field(15.0, gt=0.0, description="Capture frame rate")
    zone_id: str = Field(..., min_length=1, description="Primary restricted zone ID monitored")
    stream_uri: Optional[str] = Field(None, description="RTSP or live stream endpoint URI")
    last_ping: Optional[str] = Field(None, description="ISO timestamp of last heartbeat")


class CameraResponse(BaseModel):
    """Schema returned to frontend and monitoring components with sanitized credentials."""

    camera_id: str
    name: str
    location: str
    status: str
    resolution: str
    fps: float
    zone_id: str
    stream_uri: Optional[str] = None
    last_ping: Optional[str] = None
    worker_status: Optional[CameraWorkerStatus] = None

    @field_validator("stream_uri", mode="before")
    @classmethod
    def mask_stream_uri(cls, v: Optional[str]) -> Optional[str]:
        return redact_uri(v)

    model_config = ConfigDict(from_attributes=True)
