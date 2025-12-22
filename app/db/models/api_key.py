"""
API Key model for service-to-service authentication.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel


class APIKey(BaseModel):
    """
    API Key for programmatic access without user sessions.

    Use cases:
    - Service-to-service authentication
    - CI/CD pipelines
    - External integrations
    - Mobile apps with long-lived tokens
    """

    __tablename__ = "api_keys"

    # Human-readable name for the key
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # The key prefix (first 8 chars) for identification
    key_prefix: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        index=True,
    )

    # Hashed key (SHA-256)
    key_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    # Owner user ID
    user_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )

    # Permissions/scopes (comma-separated or JSON)
    scopes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default="*",  # All permissions by default
    )

    # Whether the key is active
    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Optional expiration
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
    )

    # Last used timestamp
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
    )

    # Last used IP address
    last_used_ip: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        default=None,
    )

    def __repr__(self) -> str:
        return f"<APIKey(name={self.name}, prefix={self.key_prefix}, active={self.active})>"
