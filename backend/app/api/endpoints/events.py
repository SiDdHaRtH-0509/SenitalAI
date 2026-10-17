"""Security Events endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import require_roles
from app.core.security import ROLE_ADMIN, ROLE_OPERATOR, ROLE_SERVICE
from app.models.user import User
from app.schemas.event import (
    SecurityEventCreate,
    SecurityEventResponse,
    EventStatusUpdateRequest,
    BatchEventCreate,
    BatchEventResponse,
)
from app.services.event_service import (
    create_security_event,
    get_security_events,
    get_security_event_by_id,
    update_event_status,
)
from app.services.audit_service import record_audit

router = APIRouter()


@router.get(
    "/events",
    response_model=List[SecurityEventResponse],
    tags=["Events"],
    summary="List security events",
)
def list_events(
    limit: int = Query(50, ge=1, le=200, description="Max events to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level (LOW, MEDIUM, HIGH, CRITICAL)"),
    status: Optional[str] = Query(None, description="Filter by review status (NEW, ACKNOWLEDGED, RESOLVED)"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    current_user: User = Depends(require_roles([ROLE_OPERATOR, ROLE_ADMIN, ROLE_SERVICE])),
    db: Session = Depends(get_db),
) -> List[SecurityEventResponse]:
    """Retrieve stored security events ordered newest-first with filtering and pagination.
    
    Protected: Requires authenticated OPERATOR, ADMIN, or SERVICE identity.
    """
    events = get_security_events(
        db=db,
        limit=limit,
        offset=offset,
        camera_id=camera_id,
        risk_level=risk_level,
        status=status,
        event_type=event_type,
    )
    return [
        SecurityEventResponse(
            event_id=e.event_id,
            camera_id=e.camera_id,
            event_type=e.event_type,
            timestamp=e.timestamp,
            severity=e.severity,
            confidence=e.confidence,
            zone_id=e.zone_id,
            description=e.description,
            evidence=e.evidence,
            risk_score=e.risk_score,
            risk_level=e.risk_level,
            reasons=e.reasons,
            recommended_action=e.recommended_action,
            status=e.status,
            operator_notes=e.operator_notes,
            created_at=e.created_at,
        )
        for e in events
    ]


@router.post(
    "/events",
    response_model=SecurityEventResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Events"],
    summary="Submit security event",
)
def submit_event(
    event_in: SecurityEventCreate,
    current_user: User = Depends(require_roles([ROLE_SERVICE, ROLE_ADMIN])),
    db: Session = Depends(get_db),
):
    """Ingest a validated security event from the Computer Vision engine.

    Evaluates explainable risk heuristic if not precomputed, stores the record
    in persistent storage, enforces strict idempotency against duplicate submissions,
    and appends an immutable security audit record.
    """
    db_event, is_duplicate = create_security_event(db, event_in)

    record_audit(
        db=db,
        action="EVENT_INGESTED",
        target_type="security_event",
        actor_username=current_user.username,
        actor_role=current_user.role,
        target_id=db_event.event_id,
        outcome="DUPLICATE" if is_duplicate else "SUCCESS",
        details=f"Camera: {db_event.camera_id}, Risk: {db_event.risk_level} ({db_event.risk_score})",
    )

    if is_duplicate:
        # Idempotent response per API_CONTRACT.md and CV client integration
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "event_id": db_event.event_id,
                "status": db_event.status,
                "message": "Duplicate event ID acknowledged",
                "detail": f"Event '{db_event.event_id}' already recorded; no duplicate created.",
                "risk_score": db_event.risk_score,
                "risk_level": db_event.risk_level,
            },
        )

    return SecurityEventResponse(
        event_id=db_event.event_id,
        camera_id=db_event.camera_id,
        event_type=db_event.event_type,
        timestamp=db_event.timestamp,
        severity=db_event.severity,
        confidence=db_event.confidence,
        zone_id=db_event.zone_id,
        description=db_event.description,
        evidence=db_event.evidence,
        risk_score=db_event.risk_score,
        risk_level=db_event.risk_level,
        reasons=db_event.reasons,
        recommended_action=db_event.recommended_action,
        status=db_event.status,
        operator_notes=db_event.operator_notes,
        created_at=db_event.created_at,
    )


@router.get(
    "/events/{event_id}",
    response_model=SecurityEventResponse,
    tags=["Events"],
    summary="Get event by ID",
)
def get_event(
    event_id: str,
    current_user: User = Depends(require_roles([ROLE_OPERATOR, ROLE_ADMIN, ROLE_SERVICE])),
    db: Session = Depends(get_db),
) -> SecurityEventResponse:
    """Retrieve full details of a single security event by its unique ID.
    
    Protected: Requires authenticated OPERATOR, ADMIN, or SERVICE identity.
    """
    db_event = get_security_event_by_id(db, event_id)
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Security event '{event_id}' not found.",
        )

    return SecurityEventResponse(
        event_id=db_event.event_id,
        camera_id=db_event.camera_id,
        event_type=db_event.event_type,
        timestamp=db_event.timestamp,
        severity=db_event.severity,
        confidence=db_event.confidence,
        zone_id=db_event.zone_id,
        description=db_event.description,
        evidence=db_event.evidence,
        risk_score=db_event.risk_score,
        risk_level=db_event.risk_level,
        reasons=db_event.reasons,
        recommended_action=db_event.recommended_action,
        status=db_event.status,
        operator_notes=db_event.operator_notes,
        created_at=db_event.created_at,
    )


@router.patch(
    "/events/{event_id}/status",
    response_model=SecurityEventResponse,
    tags=["Events"],
    summary="Update event review status",
)
def update_status(
    event_id: str,
    status_in: EventStatusUpdateRequest,
    current_user: User = Depends(require_roles([ROLE_OPERATOR, ROLE_ADMIN])),
    db: Session = Depends(get_db),
) -> SecurityEventResponse:
    """Update the triage status and append commentary notes for a security incident.
    
    Appends an immutable audit log recording the operator identity, transition, and commentary.
    """
    operator_note = (
        f"[{current_user.username}] {status_in.notes}"
        if status_in.notes
        else f"Status set by {current_user.username}"
    )
    updated = update_event_status(
        db=db,
        event_id=event_id,
        target_status=status_in.status,
        notes=operator_note,
    )
    if not updated:
        record_audit(
            db=db,
            action="EVENT_STATUS_UPDATE_FAILED",
            target_type="security_event",
            actor_username=current_user.username,
            actor_role=current_user.role,
            target_id=event_id,
            outcome="FAILURE",
            details=f"Target status: {status_in.status}. Event not found.",
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Security event '{event_id}' not found.",
        )

    record_audit(
        db=db,
        action="EVENT_STATUS_UPDATED",
        target_type="security_event",
        actor_username=current_user.username,
        actor_role=current_user.role,
        target_id=event_id,
        outcome="SUCCESS",
        details=f"New status: {status_in.status}, Notes: {status_in.notes or ''}",
    )

    return SecurityEventResponse(
        event_id=updated.event_id,
        camera_id=updated.camera_id,
        event_type=updated.event_type,
        timestamp=updated.timestamp,
        severity=updated.severity,
        confidence=updated.confidence,
        zone_id=updated.zone_id,
        description=updated.description,
        evidence=updated.evidence,
        risk_score=updated.risk_score,
        risk_level=updated.risk_level,
        reasons=updated.reasons,
        recommended_action=updated.recommended_action,
        status=updated.status,
        operator_notes=updated.operator_notes,
        created_at=updated.created_at,
    )


@router.post(
    "/events/batch",
    response_model=BatchEventResponse,
    tags=["Events"],
    summary="Batch submit security events",
)
def submit_events_batch(
    batch_in: BatchEventCreate,
    current_user: User = Depends(require_roles([ROLE_SERVICE, ROLE_ADMIN])),
    db: Session = Depends(get_db),
) -> BatchEventResponse:
    """Ingest a batch of security events from CV pipeline.

    Validates each event, persists non-duplicates, reports detailed outcomes,
    and appends a batch audit log record.
    """
    created_count = 0
    duplicate_count = 0
    errors: List[str] = []
    events_out: List[SecurityEventResponse] = []

    for item in batch_in.events:
        try:
            db_event, is_duplicate = create_security_event(db, item)
            if is_duplicate:
                duplicate_count += 1
            else:
                created_count += 1

            events_out.append(
                SecurityEventResponse(
                    event_id=db_event.event_id,
                    camera_id=db_event.camera_id,
                    event_type=db_event.event_type,
                    timestamp=db_event.timestamp,
                    severity=db_event.severity,
                    confidence=db_event.confidence,
                    zone_id=db_event.zone_id,
                    description=db_event.description,
                    evidence=db_event.evidence,
                    risk_score=db_event.risk_score,
                    risk_level=db_event.risk_level,
                    reasons=db_event.reasons,
                    recommended_action=db_event.recommended_action,
                    status=db_event.status,
                    operator_notes=db_event.operator_notes,
                    created_at=db_event.created_at,
                )
            )
        except Exception as exc:
            errors.append(f"Failed to process '{item.event_id}': {str(exc)}")

    record_audit(
        db=db,
        action="EVENT_BATCH_INGESTED",
        target_type="security_event",
        actor_username=current_user.username,
        actor_role=current_user.role,
        outcome="SUCCESS",
        details=f"Total: {len(batch_in.events)}, Created: {created_count}, Duplicates: {duplicate_count}, Errors: {len(errors)}",
    )

    return BatchEventResponse(
        total=len(batch_in.events),
        created=created_count,
        duplicates=duplicate_count,
        errors=errors,
        events=events_out,
    )
