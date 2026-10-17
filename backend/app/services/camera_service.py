"""Service for Camera edge device registry."""

from typing import List
from sqlalchemy.orm import Session
from app.models.camera import CameraModel
from app.schemas.camera import CameraCreate


DEFAULT_CONFIGURED_CAMERAS = [
    {
        "camera_id": "cam-north-01",
        "name": "Sector Alpha — North Ridge Primary PTZ",
        "location": "North Perimeter Observation Tower Alpha",
        "status": "ONLINE",
        "resolution": "1920x1080",
        "fps": 20.0,
        "zone_id": "zone-restricted-01",
        "stream_uri": "rtsp://edge-node-01.local:554/live/north_ridge",
        "last_ping": "2026-10-17T12:00:00Z",
    },
    {
        "camera_id": "cam-east-02",
        "name": "Sector Bravo — East Valley IR Fence",
        "location": "East Sector Perimeter Fence",
        "status": "ONLINE",
        "resolution": "1920x1080",
        "fps": 15.0,
        "zone_id": "zone-restricted-buffer-east",
        "stream_uri": "rtsp://edge-node-02.local:554/live/east_valley",
        "last_ping": "2026-10-17T12:00:00Z",
    },
    {
        "camera_id": "cam-west-03",
        "name": "Sector Charlie — River Crossing IR",
        "location": "River Bed Watchtower",
        "status": "OFFLINE",
        "resolution": "1920x1080",
        "fps": 15.0,
        "zone_id": "zone-restricted-01",
        "stream_uri": "rtsp://edge-node-03.local:554/live/river_ir",
        "last_ping": "2026-10-17T10:00:00Z",
    },
    {
        "camera_id": "cam-south-04",
        "name": "Sector Delta — South Gate Overview",
        "location": "Border Checkpoint Service Road",
        "status": "ONLINE",
        "resolution": "1280x720",
        "fps": 10.0,
        "zone_id": "zone-restricted-service-gate",
        "stream_uri": "rtsp://edge-node-04.local:554/live/south_gate",
        "last_ping": "2026-10-17T12:00:00Z",
    },
]


def get_all_cameras(db: Session) -> List[CameraModel]:
    """Retrieve all configured camera records from database."""
    return db.query(CameraModel).order_by(CameraModel.camera_id).all()


def register_camera(db: Session, camera_in: CameraCreate) -> CameraModel:
    """Register or update a camera device."""
    existing = db.query(CameraModel).filter(CameraModel.camera_id == camera_in.camera_id).first()
    if existing:
        existing.name = camera_in.name
        existing.location = camera_in.location
        existing.status = camera_in.status
        existing.resolution = camera_in.resolution
        existing.fps = camera_in.fps
        existing.zone_id = camera_in.zone_id
        existing.stream_uri = camera_in.stream_uri
        existing.last_ping = camera_in.last_ping
        db.commit()
        db.refresh(existing)
        return existing

    new_cam = CameraModel(
        camera_id=camera_in.camera_id,
        name=camera_in.name,
        location=camera_in.location,
        status=camera_in.status,
        resolution=camera_in.resolution,
        fps=camera_in.fps,
        zone_id=camera_in.zone_id,
        stream_uri=camera_in.stream_uri,
        last_ping=camera_in.last_ping,
    )
    db.add(new_cam)
    db.commit()
    db.refresh(new_cam)
    return new_cam


def seed_default_cameras(db: Session) -> None:
    """Seed initial configured camera devices if the table is currently empty."""
    if db.query(CameraModel).count() == 0:
        for cam_data in DEFAULT_CONFIGURED_CAMERAS:
            db.add(CameraModel(**cam_data))
        db.commit()
