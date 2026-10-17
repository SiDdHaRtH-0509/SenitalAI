"""Pydantic schemas package for SentinelAI."""

from app.schemas.health import HealthResponse
from app.schemas.stats import DashboardStatsResponse
from app.schemas.event import (
    SecurityEventCreate,
    SecurityEventResponse,
    EventStatusUpdateRequest,
    BatchEventCreate,
    BatchEventResponse,
    normalize_status,
    CANONICAL_STATUSES,
)
from app.schemas.camera import CameraCreate, CameraResponse
from app.schemas.zone import RestrictedZoneCreate, RestrictedZoneResponse

__all__ = [
    "HealthResponse",
    "DashboardStatsResponse",
    "SecurityEventCreate",
    "SecurityEventResponse",
    "EventStatusUpdateRequest",
    "BatchEventCreate",
    "BatchEventResponse",
    "normalize_status",
    "CANONICAL_STATUSES",
    "CameraCreate",
    "CameraResponse",
    "RestrictedZoneCreate",
    "RestrictedZoneResponse",
]
