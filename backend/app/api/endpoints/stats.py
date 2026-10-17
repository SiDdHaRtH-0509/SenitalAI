"""Surveillance statistics endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.security import ROLE_ADMIN, ROLE_OPERATOR, ROLE_SERVICE
from app.database import get_db
from app.models.user import User
from app.schemas.stats import DashboardStatsResponse
from app.services.event_service import get_dashboard_statistics

router = APIRouter()


@router.get("/stats", response_model=DashboardStatsResponse, tags=["Statistics"])
def get_stats(
    current_user: User = Depends(require_roles([ROLE_OPERATOR, ROLE_ADMIN, ROLE_SERVICE])),
    db: Session = Depends(get_db),
) -> DashboardStatsResponse:
    """Return live aggregate statistics computed from persisted records.
    
    Protected: Requires authenticated OPERATOR, ADMIN, or SERVICE identity.
    """
    return get_dashboard_statistics(db)
