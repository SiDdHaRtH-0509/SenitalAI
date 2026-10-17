"""Liveness health check endpoint."""

from fastapi import APIRouter
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
def get_health() -> HealthResponse:
    """Return operational liveness indicator of the FastAPI service.

    Does NOT claim cameras or CV models are operational merely because
    the backend HTTP process is active.
    """
    return HealthResponse(status="ok", service="sentinel-api")
