"""Pydantic schemas for Restricted Zones."""

from typing import List
from pydantic import BaseModel, ConfigDict, Field


class RestrictedZoneCreate(BaseModel):
    """Payload schema to define or register a restricted boundary polygon."""

    zone_id: str = Field(..., min_length=1, description="Unique zone identifier")
    name: str = Field(..., min_length=1, description="Descriptive zone name")
    camera_id: str = Field(..., min_length=1, description="Camera viewing this zone")
    status: str = Field("ACTIVE", description="Zone monitoring status (ACTIVE, INACTIVE)")
    vertices: List[List[float]] = Field(..., min_length=3, description="Ordered polygon vertices [x, y]")
    reference_strategy: str = Field("bottom_center", description="Point-in-polygon reference anchor")
    description: str = Field("Configured restricted zone", description="Purpose and operational rules")


class RestrictedZoneResponse(BaseModel):
    """Schema returned to frontend and CV engine clients."""

    zone_id: str
    name: str
    camera_id: str
    status: str
    vertices: List[List[float]]
    reference_strategy: str
    incursions_today: int = 0
    description: str

    model_config = ConfigDict(from_attributes=True)
