"""Immutable Security Audit Log Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.security import ROLE_ADMIN
from app.database import get_db
from app.models.user import User
from app.schemas.audit import AuditIntegrityResponse, AuditLogResponse
from app.services.audit_service import get_audit_logs, verify_audit_trail_integrity

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get(
    "/verify-integrity",
    response_model=AuditIntegrityResponse,
    summary="Verify cryptographic hash chain integrity of audit trail (Administrator only)",
)
def verify_audit_trail(
    current_admin: User = Depends(require_roles([ROLE_ADMIN])),
    db: Session = Depends(get_db),
) -> AuditIntegrityResponse:
    """Validate unbroken SHA-256 hash chaining across all persistent audit records.
    
    Verifies that no rows have been modified, injected, reordered, or deleted
    from the append-only security log.
    """
    result = verify_audit_trail_integrity(db)
    return AuditIntegrityResponse(**result)


@router.get(
    "",
    response_model=List[AuditLogResponse],
    summary="Query security audit trail (Administrator only)",
)
def list_audit_logs(
    limit: int = Query(50, ge=1, le=500, description="Max audit entries to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    action: Optional[str] = Query(None, description="Filter by action name"),
    actor_username: Optional[str] = Query(None, description="Filter by actor username"),
    target_type: Optional[str] = Query(None, description="Filter by target type"),
    current_admin: User = Depends(require_roles([ROLE_ADMIN])),
    db: Session = Depends(get_db),
) -> List[AuditLogResponse]:
    """Retrieve immutable audit log records.
    
    Access is strictly restricted to authenticated administrators.
    No endpoints exist to modify or delete audit entries.
    """
    logs = get_audit_logs(
        db=db,
        limit=limit,
        offset=offset,
        action=action,
        actor_username=actor_username,
        target_type=target_type,
    )
    return [AuditLogResponse.model_validate(log) for log in logs]
