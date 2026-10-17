"""SQLAlchemy ORM model for Security Events."""

import json
from typing import Any, Dict, List, Optional
from sqlalchemy import Column, Float, Integer, String, Text
from app.database import Base


class EventModel(Base):
    """Database model for security incidents detected by the CV pipeline."""

    __tablename__ = "security_events"

    event_id = Column(String(64), primary_key=True, index=True)
    camera_id = Column(String(64), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, default="RESTRICTED_ZONE_ENTRY")
    timestamp = Column(String(64), nullable=False, index=True)
    severity = Column(String(16), nullable=False)
    confidence = Column(Float, nullable=False)
    zone_id = Column(String(64), nullable=True, index=True)
    description = Column(Text, nullable=False)

    # Serialized JSON structures
    evidence_json = Column(Text, nullable=False, default="{}")
    reasons_json = Column(Text, nullable=False, default="[]")

    # Risk assessment
    risk_score = Column(Integer, nullable=False, default=50)
    risk_level = Column(String(16), nullable=False, default="MEDIUM", index=True)
    recommended_action = Column(Text, nullable=False, default="Request human verification")

    # Review lifecycle
    status = Column(String(24), nullable=False, default="NEW", index=True)
    operator_notes = Column(Text, nullable=True)
    created_at = Column(String(64), nullable=False)

    @property
    def evidence(self) -> Dict[str, Any]:
        """Parsed evidence dictionary."""
        if not self.evidence_json:
            return {}
        try:
            return json.loads(self.evidence_json)
        except Exception:
            return {}

    @evidence.setter
    def evidence(self, val: Optional[Dict[str, Any]]) -> None:
        self.evidence_json = json.dumps(val or {})

    @property
    def reasons(self) -> List[str]:
        """Parsed explanation reasons list."""
        if not self.reasons_json:
            return []
        try:
            return json.loads(self.reasons_json)
        except Exception:
            return []

    @reasons.setter
    def reasons(self, val: Optional[List[str]]) -> None:
        self.reasons_json = json.dumps(val or [])
