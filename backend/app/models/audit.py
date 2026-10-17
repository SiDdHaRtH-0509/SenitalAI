"""AuditLog database model for tamper-evident security tracking."""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, String, Text
from app.database import Base


class AuditLog(Base):
    """Immutable audit record for tracking security-relevant actions.

    Records actor, action, target, timestamp, outcome, and contextual details.
    Deletion and modification of these records are strictly prohibited by API design.
    """

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    actor_username = Column(String(64), nullable=False, index=True)
    actor_role = Column(String(32), nullable=True)
    ip_address = Column(String(64), nullable=True)
    action = Column(String(64), nullable=False, index=True)
    target_type = Column(String(64), nullable=False, index=True)
    target_id = Column(String(128), nullable=True, index=True)
    outcome = Column(String(32), nullable=False)  # SUCCESS, FAILURE, DENIED, DUPLICATE
    details = Column(Text, nullable=True)
    prev_hash = Column(String(64), nullable=False, default="0" * 64)
    record_hash = Column(String(64), nullable=False, index=True)

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} timestamp='{self.timestamp}' "
            f"actor='{self.actor_username}' action='{self.action}' outcome='{self.outcome}'>"
        )
