"""OAuth2 account model for social authentication."""

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel


class OAuthAccount(BaseModel):
    """OAuth account linked to a user."""

    __tablename__ = "oauth_accounts"

    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    collection_name: Mapped[str] = mapped_column(String(50), nullable=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    access_token: Mapped[str] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=True)
    expires_at: Mapped[str] = mapped_column(String(50), nullable=True)
    token_type: Mapped[str] = mapped_column(String(50), nullable=True)
    scope: Mapped[str] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<OAuthAccount(provider={self.provider}, user_id={self.user_id})>"
