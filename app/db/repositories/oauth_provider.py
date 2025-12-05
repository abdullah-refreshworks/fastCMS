"""Repository for OAuth provider configurations."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.oauth_provider import OAuthProvider


class OAuthProviderRepository:
    """Repository for OAuth provider CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, enabled_only: bool = False) -> List[OAuthProvider]:
        """Get all OAuth providers, optionally filtering to enabled only."""
        query = select(OAuthProvider).order_by(OAuthProvider.display_order)
        if enabled_only:
            query = query.where(OAuthProvider.enabled == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, provider_id: str) -> Optional[OAuthProvider]:
        """Get provider by ID."""
        result = await self.db.execute(
            select(OAuthProvider).where(OAuthProvider.id == provider_id)
        )
        return result.scalar_one_or_none()

    async def get_by_type(self, provider_type: str) -> Optional[OAuthProvider]:
        """Get provider by type (e.g., 'google', 'github')."""
        result = await self.db.execute(
            select(OAuthProvider).where(OAuthProvider.provider_type == provider_type)
        )
        return result.scalar_one_or_none()

    async def get_enabled_by_type(self, provider_type: str) -> Optional[OAuthProvider]:
        """Get enabled provider by type."""
        result = await self.db.execute(
            select(OAuthProvider)
            .where(OAuthProvider.provider_type == provider_type)
            .where(OAuthProvider.enabled == True)
        )
        return result.scalar_one_or_none()

    async def get_for_collection(
        self, collection_id: Optional[str] = None
    ) -> List[OAuthProvider]:
        """Get enabled providers available for a collection."""
        query = select(OAuthProvider).where(OAuthProvider.enabled == True)

        if collection_id:
            # Get providers that are either global (no collection restriction)
            # or specifically assigned to this collection
            query = query.where(
                (OAuthProvider.collection_id == None) |
                (OAuthProvider.collection_id == collection_id)
            )
        else:
            # For system users, only get global providers
            query = query.where(OAuthProvider.collection_id == None)

        query = query.order_by(OAuthProvider.display_order)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, provider: OAuthProvider) -> OAuthProvider:
        """Create a new OAuth provider configuration."""
        self.db.add(provider)
        await self.db.flush()
        await self.db.refresh(provider)
        return provider

    async def update(self, provider: OAuthProvider) -> OAuthProvider:
        """Update an OAuth provider configuration."""
        await self.db.flush()
        await self.db.refresh(provider)
        return provider

    async def delete(self, provider: OAuthProvider) -> bool:
        """Delete an OAuth provider configuration."""
        await self.db.delete(provider)
        await self.db.flush()
        return True

    async def reorder(self, provider_ids: List[str]) -> bool:
        """Reorder providers by setting display_order based on list position."""
        for i, provider_id in enumerate(provider_ids):
            result = await self.db.execute(
                select(OAuthProvider).where(OAuthProvider.id == provider_id)
            )
            provider = result.scalar_one_or_none()
            if provider:
                provider.display_order = i
        await self.db.flush()
        return True
