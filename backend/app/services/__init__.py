"""Services package for SentinelAI."""

from app.services.risk_engine import RiskEngine
from app.services.event_service import (
    create_security_event,
    get_security_events,
    get_security_event_by_id,
    update_event_status,
    get_dashboard_statistics,
)
from app.services.camera_service import get_all_cameras, register_camera, seed_default_cameras
from app.services.zone_service import get_all_zones, register_zone, seed_default_zones

__all__ = [
    "RiskEngine",
    "create_security_event",
    "get_security_events",
    "get_security_event_by_id",
    "update_event_status",
    "get_dashboard_statistics",
    "get_all_cameras",
    "register_camera",
    "seed_default_cameras",
    "get_all_zones",
    "register_zone",
    "seed_default_zones",
]
