"""SentinelAI FastAPI Backend Application.

Main entry point providing REST API services for border surveillance,
connecting the React dashboard, Computer Vision engine, and persistent
event storage per API_CONTRACT.md.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.services.camera_service import seed_default_cameras
from app.services.zone_service import seed_default_zones


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle context manager.

    Initializes database schema and conditionally seeds configured camera
    and restricted-zone definitions if tables are empty.
    """
    # 1. Ensure all database tables exist
    Base.metadata.create_all(bind=engine)

    # 2. Seed initial configured assets if enabled
    if settings.SEED_CONFIGURED_ASSETS:
        db = SessionLocal()
        try:
            seed_default_cameras(db)
            seed_default_zones(db)
        finally:
            db.close()

    yield


app = FastAPI(
    title="SentinelAI Surveillance Operations API",
    description=(
        "Intelligent Video Analytics Platform API for Border Surveillance "
        "using existing CCTV infrastructure. Provides real-time event ingestion, "
        "incident triage, camera registry, and situational analytics."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Enable Cross-Origin Resource Sharing (CORS) for frontend development servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom validation error handler for friendly, readable 422 errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Format Pydantic schema validation errors with clean, actionable details."""
    errors = []
    for err in exc.errors():
        field_path = " -> ".join(str(loc) for loc in err.get("loc", []))
        msg = err.get("msg", "Invalid value")
        errors.append(f"{field_path}: {msg}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Request validation failed",
            "errors": errors,
        },
    )


# Mount main API router under /api
app.include_router(api_router, prefix="/api")


@app.get("/", tags=["Root"])
def root_info():
    """Root metadata endpoint providing links to API documentation."""
    return {
        "service": "SentinelAI Backend API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/api/health",
        "contract": "API_CONTRACT.md v1.0",
    }
