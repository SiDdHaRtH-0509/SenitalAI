"""SQLAlchemy models package for SentinelAI."""

from app.database import Base
from app.models.event import EventModel
from app.models.camera import CameraModel
from app.models.zone import ZoneModel

__all__ = ["Base", "EventModel", "CameraModel", "ZoneModel"]
