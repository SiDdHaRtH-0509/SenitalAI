"""Database persistence and query service for Security Events."""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.event import EventModel
from app.models.camera import CameraModel
from app.models.zone import ZoneModel
from app.schemas.event import SecurityEventCreate
from app.schemas.stats import DashboardStatsResponse
from app.services.risk_engine import RiskEngine


def create_security_event(
    db: Session,
    event_in: SecurityEventCreate,
) -> Tuple[EventModel, bool]:
    """Persist a new security event or return existing idempotent duplicate.

    Returns:
        Tuple[EventModel, bool]: (event_record, is_duplicate)
    """
    # 1. Check for existing event to ensure strict idempotency
    existing = db.query(EventModel).filter(EventModel.event_id == event_in.event_id).first()
    if existing:
        return existing, True

    # 2. Evaluate risk if not provided explicitly by caller
    if event_in.risk_score is None or not event_in.risk_level:
        score, level, reasons, action = RiskEngine.evaluate(
            severity=event_in.severity,
            confidence=event_in.confidence,
            zone_id=event_in.zone_id,
            evidence=event_in.evidence,
        )
        risk_score = event_in.risk_score if event_in.risk_score is not None else score
        risk_level = event_in.risk_level or level
        explanation_reasons = event_in.reasons or reasons
        recommended_action = event_in.recommended_action or action
    else:
        risk_score = event_in.risk_score
        risk_level = event_in.risk_level
        explanation_reasons = event_in.reasons or ["Declared by producer"]
        recommended_action = event_in.recommended_action or "Review incident"

    # 3. Create persistent database record
    now_utc = datetime.now(timezone.utc).isoformat()
    db_event = EventModel(
        event_id=event_in.event_id,
        camera_id=event_in.camera_id,
        event_type=event_in.event_type,
        timestamp=event_in.timestamp,
        severity=event_in.severity,
        confidence=round(float(event_in.confidence), 4),
        zone_id=event_in.zone_id,
        description=event_in.description,
        evidence_json=json.dumps(event_in.evidence or {}),
        risk_score=risk_score,
        risk_level=risk_level,
        reasons_json=json.dumps(explanation_reasons),
        recommended_action=recommended_action,
        status=event_in.status or "NEW",
        operator_notes=None,
        created_at=now_utc,
    )

    db.add(db_event)

    # 4. If zone is known, increment zone incursion counter
    if event_in.zone_id:
        zone = db.query(ZoneModel).filter(ZoneModel.zone_id == event_in.zone_id).first()
        if zone:
            zone.incursions_today += 1

    db.commit()
    db.refresh(db_event)
    return db_event, False


def get_security_events(
    db: Session,
    limit: int = 50,
    offset: int = 0,
    camera_id: Optional[str] = None,
    risk_level: Optional[str] = None,
    status: Optional[str] = None,
    event_type: Optional[str] = None,
) -> List[EventModel]:
    """Retrieve security events ordered newest-first with optional filtering."""
    query = db.query(EventModel)

    if camera_id:
        query = query.filter(EventModel.camera_id == camera_id)
    if risk_level:
        query = query.filter(EventModel.risk_level == risk_level.upper())
    if status:
        query = query.filter(EventModel.status == status.upper())
    if event_type:
        query = query.filter(EventModel.event_type == event_type)

    return (
        query.order_by(EventModel.timestamp.desc())
        .offset(max(0, offset))
        .limit(max(1, min(200, limit)))
        .all()
    )


def get_security_event_by_id(db: Session, event_id: str) -> Optional[EventModel]:
    """Retrieve a single event record by ID."""
    return db.query(EventModel).filter(EventModel.event_id == event_id).first()


def update_event_status(
    db: Session,
    event_id: str,
    target_status: str,
    notes: Optional[str] = None,
) -> Optional[EventModel]:
    """Update event review status and append optional operator notes."""
    db_event = db.query(EventModel).filter(EventModel.event_id == event_id).first()
    if not db_event:
        return None

    db_event.status = target_status
    if notes and notes.strip():
        now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        note_entry = f"[{now_ts}] {notes.strip()}"
        if db_event.operator_notes:
            db_event.operator_notes = f"{db_event.operator_notes}\n{note_entry}"
        else:
            db_event.operator_notes = note_entry

    db.commit()
    db.refresh(db_event)
    return db_event


def get_dashboard_statistics(db: Session) -> DashboardStatsResponse:
    """Compute aggregate surveillance statistics directly from persisted records."""
    total_events = db.query(EventModel).count()

    # Risk level counts
    risk_counts: Dict[str, int] = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    rows = (
        db.query(EventModel.risk_level, func.count(EventModel.event_id))
        .group_by(EventModel.risk_level)
        .all()
    )
    for level, count in rows:
        if level in risk_counts:
            risk_counts[level] = count

    active_cameras = db.query(CameraModel).filter(CameraModel.status == "ONLINE").count()
    total_cameras = db.query(CameraModel).count()

    return DashboardStatsResponse(
        total_events=total_events,
        by_risk_level=risk_counts,
        active_cameras=active_cameras,
        total_cameras=total_cameras,
    )
