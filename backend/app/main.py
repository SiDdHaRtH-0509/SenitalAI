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

from sqlalchemy import inspect, text
from app.api.router import api_router
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models.audit import AuditLog
from app.services.camera_service import seed_default_cameras
from app.services.zone_service import seed_default_zones
from app.services.auth_service import seed_default_users
from app.services.audit_service import (
    GENESIS_PREV_HASH,
    compute_audit_hash,
    format_timestamp_canonical,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle context manager.

    Initializes database schema, executes non-destructive schema migrations
    for audit log hash chaining, and conditionally seeds configured camera,
    restricted-zone, and initial RBAC user accounts if tables are empty.
    """
    # 1. Ensure all database tables exist
    Base.metadata.create_all(bind=engine)

    # 1.1 Non-destructive migration: ensure audit_logs has hash chaining columns
    inspector = inspect(engine)
    if "audit_logs" in inspector.get_table_names():
        cols = {c["name"] for c in inspector.get_columns("audit_logs")}
        with engine.begin() as conn:
            if "prev_hash" not in cols:
                conn.execute(text("ALTER TABLE audit_logs ADD COLUMN prev_hash VARCHAR(64) DEFAULT '0000000000000000000000000000000000000000000000000000000000000000'"))
            if "record_hash" not in cols:
                conn.execute(text("ALTER TABLE audit_logs ADD COLUMN record_hash VARCHAR(64)"))

        # Backfill hashes for any legacy pre-existing rows missing record_hash
        mig_db = SessionLocal()
        try:
            unhashed = (
                mig_db.query(AuditLog)
                .filter((AuditLog.record_hash.is_(None)) | (AuditLog.record_hash == ""))
                .order_by(AuditLog.id.asc())
                .all()
            )
            if unhashed:
                prev_h = GENESIS_PREV_HASH
                for row in unhashed:
                    row.prev_hash = prev_h
                    row.record_hash = compute_audit_hash(
                        prev_hash=prev_h,
                        action=row.action,
                        target_type=row.target_type,
                        target_id=row.target_id,
                        actor_username=row.actor_username,
                        actor_role=row.actor_role,
                        outcome=row.outcome,
                        timestamp_canonical=format_timestamp_canonical(row.timestamp),
                        details=row.details,
                        ip_address=row.ip_address,
                    )
                    prev_h = row.record_hash
                mig_db.commit()
        finally:
            mig_db.close()

    # 1.2 Enable SQLite WAL mode and busy timeout for concurrent multi-camera safety
    if settings.DATABASE_URL.startswith("sqlite"):
        try:
            with engine.begin() as conn:
                conn.execute(text("PRAGMA journal_mode=WAL;"))
                conn.execute(text("PRAGMA busy_timeout=5000;"))
        except Exception:
            pass

    # 2. Seed initial configured assets and users if enabled
    if settings.SEED_CONFIGURED_ASSETS:
        db = SessionLocal()
        try:
            seed_default_users(db)
            seed_default_cameras(db)
            seed_default_zones(db)
        finally:
            db.close()

    yield

    # Clean shutdown: Stop all active camera workers
    try:
        from app.services.camera_worker import worker_manager
        worker_manager.stop_all()
    except Exception:
        pass


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
