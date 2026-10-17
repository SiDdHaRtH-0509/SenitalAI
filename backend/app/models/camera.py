"""SQLAlchemy ORM model for Camera edge devices."""

from sqlalchemy import Column, Float, String
from app.database import Base


class CameraModel(Base):
    """Database model for registered CCTV surveillance edge camera devices."""

    __tablename__ = "cameras"

    camera_id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    location = Column(String(256), nullable=False)
    status = Column(String(24), nullable=False, default="ONLINE")
    resolution = Column(String(32), nullable=False, default="1920x1080")
    fps = Column(Float, nullable=False, default=15.0)
    zone_id = Column(String(64), nullable=False)
    stream_uri = Column(String(256), nullable=True)
    last_ping = Column(String(64), nullable=True)
