"""Dashboard statistics schemas."""

from typing import Dict
from pydantic import BaseModel, Field


class DashboardStatsResponse(BaseModel):
    """Aggregate surveillance telemetry statistics."""

    total_events: int = Field(..., description="Total number of recorded events in ledger")
    by_risk_level: Dict[str, int] = Field(
        default_factory=lambda: {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
        description="Breakdown of event counts by risk level",
    )
    active_cameras: int = Field(0, description="Count of active online camera devices")
    total_cameras: int = Field(0, description="Total registered camera devices")
