"""Main API router combining all endpoint modules."""

from fastapi import APIRouter
from app.api.endpoints import health, stats, events, cameras, zones

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(stats.router)
api_router.include_router(events.router)
api_router.include_router(cameras.router)
api_router.include_router(zones.router)
