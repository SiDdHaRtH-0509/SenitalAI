"""Pydantic schemas for Camera edge devices."""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


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
    """Schema returned to frontend and monitoring components."""

    camera_id: str
    name: str
    location: str
    status: str
    resolution: str
    fps: float
    zone_id: str
    stream_uri: Optional[str] = None
    last_ping: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
