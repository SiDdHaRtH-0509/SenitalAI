"""Restricted Zones endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.security import ROLE_ADMIN, ROLE_OPERATOR, ROLE_SERVICE
from app.database import get_db
from app.models.user import User
from app.schemas.zone import RestrictedZoneCreate, RestrictedZoneResponse
from app.services.zone_service import get_all_zones, register_zone
from app.services.audit_service import record_audit

router = APIRouter()


@router.get("/zones", response_model=List[RestrictedZoneResponse], tags=["Restricted Zones"])
def list_zones(
    current_user: User = Depends(require_roles([ROLE_OPERATOR, ROLE_ADMIN, ROLE_SERVICE])),
    db: Session = Depends(get_db),
) -> List[RestrictedZoneResponse]:
    """Retrieve all configured restricted boundary polygons.
    
    Protected: Requires authenticated OPERATOR, ADMIN, or SERVICE identity.
    """
    return get_all_zones(db)


@router.post("/zones", response_model=RestrictedZoneResponse, status_code=status.HTTP_201_CREATED, tags=["Restricted Zones"])
def add_zone(
    zone_in: RestrictedZoneCreate,
    current_admin: User = Depends(require_roles([ROLE_ADMIN])),
    db: Session = Depends(get_db),
) -> RestrictedZoneResponse:
    """Register or update a calibrated restricted zone boundary (Admin only)."""
    zone = register_zone(db, zone_in)
    record_audit(
        db=db,
        action="ZONE_REGISTERED",
        target_type="zone",
        actor_username=current_admin.username,
        actor_role=current_admin.role,
        target_id=zone.zone_id,
        outcome="SUCCESS",
        details=f"Name: {zone.name}, Description: {zone.description or ''}",
    )
    return zone
