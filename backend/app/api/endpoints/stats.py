"""Surveillance statistics endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.stats import DashboardStatsResponse
from app.services.event_service import get_dashboard_statistics

router = APIRouter()


@router.get("/stats", response_model=DashboardStatsResponse, tags=["Statistics"])
def get_stats(db: Session = Depends(get_db)) -> DashboardStatsResponse:
    """Return live aggregate statistics computed from persisted records."""
    return get_dashboard_statistics(db)
