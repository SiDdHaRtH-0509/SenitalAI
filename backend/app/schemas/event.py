"""Pydantic schemas for Security Events."""

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

CANONICAL_STATUSES = {"NEW", "ACKNOWLEDGED", "RESOLVED"}
VALID_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
STATUS_ALIASES = {
    "UNREVIEWED": "NEW",
    "NEW": "NEW",
    "INVESTIGATING": "ACKNOWLEDGED",
    "ACKNOWLEDGED": "ACKNOWLEDGED",
    "RESOLVED": "RESOLVED",
    "FALSE_POSITIVE": "RESOLVED",
}


def normalize_status(raw: str) -> str:
    """Normalize review status to canonical enum (NEW, ACKNOWLEDGED, RESOLVED).

    Supports backward compatibility with frontend/legacy draft values:
    UNREVIEWED -> NEW
    INVESTIGATING -> ACKNOWLEDGED
    FALSE_POSITIVE -> RESOLVED
    """
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("Status must be a non-empty string.")
    cleaned = raw.strip().upper()
    if cleaned in STATUS_ALIASES:
        return STATUS_ALIASES[cleaned]
    raise ValueError(
        f"Invalid status '{raw}'. Must be one of: {sorted(CANONICAL_STATUSES)} "
        f"(or recognized aliases: {sorted(STATUS_ALIASES.keys())})"
    )


class SecurityEventCreate(BaseModel):
    """Payload schema for submitting a security event to POST /api/events."""

    event_id: str = Field(..., min_length=1, description="Unique identifier for the incident")
    camera_id: str = Field(..., min_length=1, description="Identifier of the capturing camera")
    event_type: str = Field(
        "RESTRICTED_ZONE_ENTRY", description="Categorical classification of the event"
    )
    timestamp: str = Field(..., description="ISO-8601 UTC timestamp with timezone indication")
    severity: str = Field("HIGH", description="Inferred incident severity (LOW, MEDIUM, HIGH, CRITICAL)")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Statistical detector confidence in [0.0, 1.0]",
    )
    zone_id: Optional[str] = Field(None, description="Restricted zone identifier breached")
    description: str = Field(
        "Restricted zone entry detected", description="Factual textual summary"
    )
    evidence: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Computer vision detection metadata"
    )

    # Optional fields if precomputed or overridden
    risk_score: Optional[int] = Field(None, ge=0, le=100, description="Optional heuristic risk score")
    risk_level: Optional[str] = Field(None, description="Optional risk classification")
    reasons: Optional[List[str]] = Field(None, description="Optional explanation reasons")
    recommended_action: Optional[str] = Field(None, description="Optional action recommendation")
    status: Optional[str] = Field("NEW", description="Review triage status")

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Verify timestamp conforms to ISO-8601 with timezone."""
        if not v or not v.strip():
            raise ValueError("timestamp must not be empty")
        ts = v.strip()
        # Ensure contains 'T' and ends with 'Z' or timezone offset
        if "T" not in ts or not (ts.endswith("Z") or "+" in ts or bool(re.search(r"-\d{2}:\d{2}$", ts))):
            raise ValueError(
                f"timestamp must be a valid ISO-8601 string with timezone (e.g., '2026-10-17T09:30:00Z'), got: '{v}'"
            )
        return ts

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if cleaned not in VALID_SEVERITIES:
            raise ValueError(f"Invalid severity '{v}'. Must be one of: {sorted(VALID_SEVERITIES)}")
        return cleaned

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> str:
        if v is None:
            return "NEW"
        return normalize_status(v)


class EventStatusUpdateRequest(BaseModel):
    """Payload schema for PATCH /api/events/{event_id}/status."""

    status: str = Field(..., description="Target review status (NEW, ACKNOWLEDGED, RESOLVED)")
    notes: Optional[str] = Field(None, description="Optional operator review commentary")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        return normalize_status(v)


class SecurityEventResponse(BaseModel):
    """Complete security event schema returned to the frontend and API clients."""

    event_id: str
    camera_id: str
    event_type: str
    timestamp: str
    severity: str
    confidence: float
    zone_id: Optional[str] = None
    description: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    risk_score: int
    risk_level: str
    reasons: List[str] = Field(default_factory=list)
    recommended_action: str
    status: str
    operator_notes: Optional[str] = None
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class BatchEventCreate(BaseModel):
    """Payload for submitting multiple events in a single batch."""

    events: List[SecurityEventCreate] = Field(..., min_length=1, description="List of events to persist")


class BatchEventResponse(BaseModel):
    """Response returned from batch event creation."""

    total: int
    created: int
    duplicates: int
    errors: List[str] = Field(default_factory=list)
    events: List[SecurityEventResponse] = Field(default_factory=list)
