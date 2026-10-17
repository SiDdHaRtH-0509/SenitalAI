"""Service for Restricted Zones management."""

import json
from typing import List
from sqlalchemy.orm import Session
from app.models.zone import ZoneModel
from app.schemas.zone import RestrictedZoneCreate


DEFAULT_CONFIGURED_ZONES = [
    {
        "zone_id": "zone-restricted-01",
        "name": "Perimeter Primary Buffer (Default CV Zone)",
        "camera_id": "cam-north-01",
        "status": "ACTIVE",
        "vertices": [
            [0.30, 0.50],
            [0.70, 0.50],
            [0.70, 0.90],
            [0.30, 0.90],
        ],
        "reference_strategy": "bottom_center",
        "incursions_today": 0,
        "description": "Calibrated boundary configured in sentinel_cv.config.",
    },
    {
        "zone_id": "zone-restricted-perimeter-a",
        "name": "Sector Alpha North Ridge Buffer",
        "camera_id": "cam-north-01",
        "status": "ACTIVE",
        "vertices": [
            [0.25, 0.40],
            [0.85, 0.40],
            [0.85, 0.85],
            [0.25, 0.85],
        ],
        "reference_strategy": "bottom_center",
        "incursions_today": 0,
        "description": "North ridge approach corridor boundary zone.",
    },
    {
        "zone_id": "zone-restricted-buffer-east",
        "name": "Sector Bravo East Valley Corridor",
        "camera_id": "cam-east-02",
        "status": "ACTIVE",
        "vertices": [
            [0.50, 0.30],
            [0.95, 0.30],
            [0.95, 0.80],
            [0.50, 0.80],
        ],
        "reference_strategy": "bottom_center",
        "incursions_today": 0,
        "description": "Secondary buffer line between fence boundary and outer road.",
    },
    {
        "zone_id": "zone-restricted-service-gate",
        "name": "Sector Delta Checkpoint Service Gate",
        "camera_id": "cam-south-04",
        "status": "ACTIVE",
        "vertices": [
            [0.15, 0.50],
            [0.45, 0.50],
            [0.45, 0.90],
            [0.15, 0.90],
        ],
        "reference_strategy": "bottom_center",
        "incursions_today": 0,
        "description": "Controlled maintenance corridor restricting unauthorized personnel traversal.",
    },
]


def get_all_zones(db: Session) -> List[ZoneModel]:
    """Retrieve all restricted zones from database."""
    return db.query(ZoneModel).order_by(ZoneModel.zone_id).all()


def register_zone(db: Session, zone_in: RestrictedZoneCreate) -> ZoneModel:
    """Register or update a restricted zone boundary."""
    existing = db.query(ZoneModel).filter(ZoneModel.zone_id == zone_in.zone_id).first()
    if existing:
        existing.name = zone_in.name
        existing.camera_id = zone_in.camera_id
        existing.status = zone_in.status
        existing.vertices_json = json.dumps(zone_in.vertices)
        existing.reference_strategy = zone_in.reference_strategy
        existing.description = zone_in.description
        db.commit()
        db.refresh(existing)
        return existing

    new_zone = ZoneModel(
        zone_id=zone_in.zone_id,
        name=zone_in.name,
        camera_id=zone_in.camera_id,
        status=zone_in.status,
        vertices_json=json.dumps(zone_in.vertices),
        reference_strategy=zone_in.reference_strategy,
        incursions_today=0,
        description=zone_in.description,
    )
    db.add(new_zone)
    db.commit()
    db.refresh(new_zone)
    return new_zone


def seed_default_zones(db: Session) -> None:
    """Seed initial configured restricted zones if table is empty."""
    if db.query(ZoneModel).count() == 0:
        for z_data in DEFAULT_CONFIGURED_ZONES:
            db.add(
                ZoneModel(
                    zone_id=z_data["zone_id"],
                    name=z_data["name"],
                    camera_id=z_data["camera_id"],
                    status=z_data["status"],
                    vertices_json=json.dumps(z_data["vertices"]),
                    reference_strategy=z_data["reference_strategy"],
                    incursions_today=z_data["incursions_today"],
                    description=z_data["description"],
                )
            )
        db.commit()
