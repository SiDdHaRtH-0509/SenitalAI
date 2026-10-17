"""Restricted Zones endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.zone import RestrictedZoneCreate, RestrictedZoneResponse
from app.services.zone_service import get_all_zones, register_zone

router = APIRouter()


@router.get("/zones", response_model=List[RestrictedZoneResponse], tags=["Restricted Zones"])
def list_zones(db: Session = Depends(get_db)) -> List[RestrictedZoneResponse]:
    """Retrieve all configured restricted boundary polygons."""
    return get_all_zones(db)


@router.post("/zones", response_model=RestrictedZoneResponse, status_code=status.HTTP_201_CREATED, tags=["Restricted Zones"])
def add_zone(zone_in: RestrictedZoneCreate, db: Session = Depends(get_db)) -> RestrictedZoneResponse:
    """Register or update a calibrated restricted zone boundary."""
    return register_zone(db, zone_in)
