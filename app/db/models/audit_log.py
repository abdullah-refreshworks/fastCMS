"""
Audit Log model for security event tracking.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel


class AuditLog(BaseModel):
    """
    Audit log for security-relevant events.

    Tracks:
    - Authentication events (login, logout, failed attempts)
    - Authorization changes (role changes, permissions)
    - Security settings (2FA, API keys, password changes)
    - Data access (sensitive data views, exports)
    - Administrative actions
    """

    __tablename__ = "audit_logs"

    # Event categorization
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    event_action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Severity: info, warning, critical
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="info",
        index=True,
    )

    # Actor information
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        index=True,
    )

    user_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
    )

    user_agent: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
    )

    # Target resource
    resource_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    resource_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
    )

    # Event details
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Additional details as JSON string
    details: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Outcome: success, failure, error
    outcome: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="success",
    )

    # Error details if failed
    error_message: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_audit_logs_event_type_action", "event_type", "event_action"),
        Index("ix_audit_logs_user_created", "user_id", "created"),
        Index("ix_audit_logs_severity_created", "severity", "created"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog({self.event_type}.{self.event_action} by {self.user_email})>"
