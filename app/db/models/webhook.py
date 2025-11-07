"""Webhook model for event subscriptions."""

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel


class Webhook(BaseModel):
    """Webhook subscription model."""

    __tablename__ = "webhooks"

    url: Mapped[str] = mapped_column(Text, nullable=False)

    collection_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    events: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # Comma-separated: create,update,delete

    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    secret: Mapped[str] = mapped_column(String(255), nullable=True)

    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    last_triggered_at: Mapped[str] = mapped_column(String(50), nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<Webhook(collection={self.collection_name}, url={self.url}, active={self.active})>"
