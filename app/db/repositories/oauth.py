"""Repository for OAuth account management."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.oauth import OAuthAccount


class OAuthAccountRepository:
    """Repository for OAuth account CRUD operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, oauth_account: OAuthAccount) -> OAuthAccount:
        """Create a new OAuth account."""
        self.db.add(oauth_account)
        await self.db.flush()
        return oauth_account

    async def get_by_provider_and_user_id(
        self, provider: str, provider_user_id: str
    ) -> Optional[OAuthAccount]:
        """Get OAuth account by provider and provider user ID."""
        stmt = select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == provider_user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: str) -> list[OAuthAccount]:
        """Get all OAuth accounts for a user."""
        stmt = select(OAuthAccount).where(OAuthAccount.user_id == user_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, oauth_account: OAuthAccount) -> OAuthAccount:
        """Update OAuth account."""
        await self.db.flush()
        return oauth_account

    async def delete(self, oauth_account: OAuthAccount) -> None:
        """Delete OAuth account."""
        await self.db.delete(oauth_account)
        await self.db.flush()
