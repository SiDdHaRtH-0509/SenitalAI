"""Health probe schema."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Liveness probe response model."""

    status: str = Field("ok", description="Service operational status indicator")
    service: str = Field("sentinel-api", description="Service identifier")
