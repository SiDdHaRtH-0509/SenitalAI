"""Pydantic schemas for AuditLog records."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    """Schema for returning audit log records with cryptographic chain hashes."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    actor_username: str
    actor_role: Optional[str] = None
    ip_address: Optional[str] = None
    action: str
    target_type: str
    target_id: Optional[str] = None
    outcome: str
    details: Optional[str] = None
    prev_hash: Optional[str] = None
    record_hash: Optional[str] = None


class AuditIntegrityResponse(BaseModel):
    """Schema for audit trail cryptographic integrity verification results."""

    valid: bool
    total_records: int
    message: str
    tampered_record_id: Optional[int] = None
    reason: Optional[str] = None
