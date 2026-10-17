"""Audit Logging Service for SentinelAI.

Provides append-only recording, cryptographic SHA-256 hash chaining,
and integrity verification of immutable security audit logs.
Modification and deletion of audit records are strictly prohibited by architecture.
"""

from datetime import datetime, timezone
import hashlib
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.audit import AuditLog

logger = logging.getLogger(__name__)

GENESIS_PREV_HASH: str = "0" * 64


def format_timestamp_canonical(ts: datetime) -> str:
    """Format datetime into a deterministic, canonical UTC string for hashing."""
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def compute_audit_hash(
    prev_hash: str,
    action: str,
    target_type: str,
    target_id: Optional[str],
    actor_username: str,
    actor_role: Optional[str],
    outcome: str,
    timestamp_canonical: str,
    details: Optional[str],
    ip_address: Optional[str],
) -> str:
    """Compute canonical SHA-256 hash for an audit log entry in the chain."""
    canonical_repr = (
        f"{prev_hash}|"
        f"{action}|"
        f"{target_type}|"
        f"{target_id or ''}|"
        f"{actor_username}|"
        f"{actor_role or ''}|"
        f"{outcome}|"
        f"{timestamp_canonical}|"
        f"{details or ''}|"
        f"{ip_address or ''}"
    )
    return hashlib.sha256(canonical_repr.encode("utf-8")).hexdigest()


def record_audit(
    db: Session,
    action: str,
    target_type: str,
    actor_username: str,
    actor_role: Optional[str] = None,
    target_id: Optional[str] = None,
    outcome: str = "SUCCESS",
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """Append a security audit record with cryptographic hash chaining.
    
    This function operates with append-only semantics. Audit records are never updated
    or deleted. Each record links cryptographically to the preceding record via SHA-256.
    """
    try:
        now = datetime.now(timezone.utc)
        ts_canonical = format_timestamp_canonical(now)

        # Retrieve the latest record to obtain the previous hash in the chain
        last_entry = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
        prev_hash = last_entry.record_hash if (last_entry and last_entry.record_hash) else GENESIS_PREV_HASH

        # Calculate cryptographic record hash
        record_hash = compute_audit_hash(
            prev_hash=prev_hash,
            action=action,
            target_type=target_type,
            target_id=target_id,
            actor_username=actor_username,
            actor_role=actor_role,
            outcome=outcome,
            timestamp_canonical=ts_canonical,
            details=details,
            ip_address=ip_address,
        )

        audit_entry = AuditLog(
            timestamp=now,
            action=action,
            target_type=target_type,
            actor_username=actor_username,
            actor_role=actor_role,
            target_id=target_id,
            outcome=outcome,
            details=details,
            ip_address=ip_address,
            prev_hash=prev_hash,
            record_hash=record_hash,
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        logger.info(
            "AUDIT [%s] actor='%s' action='%s' target='%s:%s' outcome='%s' hash=%.12s...",
            audit_entry.id,
            actor_username,
            action,
            target_type,
            target_id or "-",
            outcome,
            record_hash,
        )
        return audit_entry
    except Exception as exc:
        logger.error("Failed to persist audit log: %s", exc)
        db.rollback()
        raise


def verify_audit_trail_integrity(db: Session) -> Dict[str, Any]:
    """Verify cryptographic hash chaining across all stored audit records.
    
    Returns:
        dict: {
            "valid": bool,
            "total_records": int,
            "message": str,
            "tampered_record_id": Optional[int],
            "reason": Optional[str],
        }
    """
    records = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
    if not records:
        return {
            "valid": True,
            "total_records": 0,
            "message": "Audit trail is empty. No tampering detected.",
            "tampered_record_id": None,
            "reason": None,
        }

    prev_record: Optional[AuditLog] = None
    for idx, record in enumerate(records):
        # 1. Check previous hash linkage
        if idx == 0:
            if record.prev_hash != GENESIS_PREV_HASH:
                return {
                    "valid": False,
                    "total_records": len(records),
                    "message": f"Genesis record {record.id} has invalid prev_hash.",
                    "tampered_record_id": record.id,
                    "reason": "INVALID_GENESIS_LINK",
                }
        else:
            assert prev_record is not None
            if record.prev_hash != prev_record.record_hash:
                return {
                    "valid": False,
                    "total_records": len(records),
                    "message": f"Record {record.id} broken chain linkage (prev_hash does not match record {prev_record.id} hash).",
                    "tampered_record_id": record.id,
                    "reason": "BROKEN_CHAIN_LINK",
                }

        # 2. Recompute expected hash and check against record_hash
        ts_canonical = format_timestamp_canonical(record.timestamp)
        expected_hash = compute_audit_hash(
            prev_hash=record.prev_hash,
            action=record.action,
            target_type=record.target_type,
            target_id=record.target_id,
            actor_username=record.actor_username,
            actor_role=record.actor_role,
            outcome=record.outcome,
            timestamp_canonical=ts_canonical,
            details=record.details,
            ip_address=record.ip_address,
        )

        if record.record_hash != expected_hash:
            return {
                "valid": False,
                "total_records": len(records),
                "message": f"Record {record.id} content was tampered: hash mismatch.",
                "tampered_record_id": record.id,
                "reason": "CONTENT_HASH_MISMATCH",
            }

        prev_record = record

    return {
        "valid": True,
        "total_records": len(records),
        "message": f"Audit trail verified: all {len(records)} records conform to unbroken SHA-256 cryptographic chain.",
        "tampered_record_id": None,
        "reason": None,
    }


def get_audit_logs(
    db: Session,
    limit: int = 50,
    offset: int = 0,
    action: Optional[str] = None,
    actor_username: Optional[str] = None,
    target_type: Optional[str] = None,
) -> List[AuditLog]:
    """Retrieve audit logs ordered newest-first with optional filtering."""
    query = db.query(AuditLog)

    if action:
        query = query.filter(AuditLog.action == action)
    if actor_username:
        query = query.filter(AuditLog.actor_username == actor_username)
    if target_type:
        query = query.filter(AuditLog.target_type == target_type)

    return query.order_by(AuditLog.timestamp.desc(), AuditLog.id.desc()).offset(offset).limit(limit).all()
