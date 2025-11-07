"""Repository for webhook management."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.webhook import Webhook


class WebhookRepository:
    """Repository for webhook CRUD operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, webhook: Webhook) -> Webhook:
        """Create a new webhook."""
        self.db.add(webhook)
        await self.db.flush()
        return webhook

    async def get_by_id(self, webhook_id: str) -> Optional[Webhook]:
        """Get webhook by ID."""
        stmt = select(Webhook).where(Webhook.id == webhook_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_collection(
        self, collection_name: str, active_only: bool = True
    ) -> List[Webhook]:
        """Get all webhooks for a collection."""
        stmt = select(Webhook).where(Webhook.collection_name == collection_name)

        if active_only:
            stmt = stmt.where(Webhook.active == True)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Webhook]:
        """Get all webhooks with pagination."""
        stmt = select(Webhook).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, webhook: Webhook) -> Webhook:
        """Update webhook."""
        await self.db.flush()
        return webhook

    async def delete(self, webhook_id: str) -> bool:
        """Delete webhook."""
        webhook = await self.get_by_id(webhook_id)
        if webhook:
            await self.db.delete(webhook)
            await self.db.flush()
            return True
        return False

    async def count(self, collection_name: Optional[str] = None) -> int:
        """Count webhooks optionally filtered by collection."""
        stmt = select(Webhook)

        if collection_name:
            stmt = stmt.where(Webhook.collection_name == collection_name)

        result = await self.db.execute(stmt)
        return len(list(result.scalars().all()))
