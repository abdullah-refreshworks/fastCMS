"""
User model for authentication.
"""

from typing import Optional
from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel


class User(BaseModel):
    """
    User model for email/password authentication.

    Fields:
    - email: Unique email address
    - password_hash: Bcrypt hashed password
    - verified: Email verification status
    - email_visibility: Control email exposure in API
    - token_key: Used to invalidate all user sessions
    - name: Optional display name
    - two_factor_enabled: Whether 2FA is enabled
    - two_factor_secret: TOTP secret key (encrypted)
    - two_factor_backup_codes: JSON array of backup codes
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    email_visibility: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Token key for invalidating all sessions
    token_key: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="",
    )

    # Optional profile fields
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )

    avatar: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="user",
    )

    # Two-Factor Authentication (2FA/TOTP)
    two_factor_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    two_factor_secret: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )

    # Backup codes stored as JSON array (hashed)
    two_factor_backup_codes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(email={self.email}, role={self.role}, verified={self.verified}, 2fa={self.two_factor_enabled})>"


class RefreshToken(BaseModel):
    """
    Refresh token model for token rotation.

    Stores refresh tokens with expiry for secure token refresh.
    """

    __tablename__ = "refresh_tokens"

    user_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )

    token: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
        index=True,
    )

    # Token is valid until this timestamp
    expires_at: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Device/client info for tracking
    user_agent: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    ip_address: Mapped[str] = mapped_column(
        String(45),
        nullable=True,
        default=None,
    )

    revoked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<RefreshToken(user_id={self.user_id}, revoked={self.revoked})>"
