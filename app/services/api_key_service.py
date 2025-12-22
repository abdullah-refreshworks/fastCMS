"""
API Key Service for managing API keys.

Provides secure generation, validation, and management of API keys
for service-to-service authentication.
"""

import hashlib
import secrets
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException, UnauthorizedException
from app.core.logging import get_logger
from app.db.models.api_key import APIKey

logger = get_logger(__name__)

# API Key format: fastcms_XXXX_YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY
# Prefix: fastcms_XXXX (12 chars) - visible part for identification
# Secret: 32 random hex chars - never stored, only shown once


class APIKeyService:
    """Service for managing API keys."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_key(
        self,
        user_id: str,
        name: str,
        scopes: Optional[str] = "*",
        expires_at: Optional[datetime] = None,
    ) -> dict:
        """
        Create a new API key.

        Args:
            user_id: Owner user ID
            name: Human-readable name
            scopes: Comma-separated permissions (default: "*" for all)
            expires_at: Optional expiration datetime

        Returns:
            Dict with key details including the full key (shown only once)
        """
        # Generate key: prefix_secret
        prefix = secrets.token_hex(4)  # 8 chars
        secret = secrets.token_hex(16)  # 32 chars
        full_key = f"fcms_{prefix}_{secret}"

        # Hash the full key for storage
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()

        # Create the API key record
        api_key = APIKey(
            name=name,
            key_prefix=prefix,
            key_hash=key_hash,
            user_id=user_id,
            scopes=scopes,
            active=True,
            expires_at=expires_at,
        )

        self.db.add(api_key)
        await self.db.commit()
        await self.db.refresh(api_key)

        logger.info(f"API key created: {name} (prefix: {prefix}) for user {user_id}")

        return {
            "id": api_key.id,
            "name": api_key.name,
            "key": full_key,  # Only returned on creation!
            "key_prefix": f"fcms_{prefix}_****",
            "scopes": api_key.scopes,
            "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
            "created": api_key.created.isoformat(),
            "message": "Save this key securely. It will not be shown again.",
        }

    async def validate_key(self, key: str, ip_address: Optional[str] = None) -> dict:
        """
        Validate an API key and return user info.

        Args:
            key: The full API key
            ip_address: Optional IP address for tracking

        Returns:
            Dict with user_id and scopes

        Raises:
            UnauthorizedException: If key is invalid, expired, or inactive
        """
        # Hash the provided key
        key_hash = hashlib.sha256(key.encode()).hexdigest()

        # Find the key
        result = await self.db.execute(
            select(APIKey).where(APIKey.key_hash == key_hash)
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            raise UnauthorizedException("Invalid API key")

        if not api_key.active:
            raise UnauthorizedException("API key is disabled")

        if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
            raise UnauthorizedException("API key has expired")

        # Update last used
        api_key.last_used_at = datetime.now(timezone.utc)
        if ip_address:
            api_key.last_used_ip = ip_address
        await self.db.commit()

        return {
            "user_id": api_key.user_id,
            "scopes": api_key.scopes,
            "key_id": api_key.id,
            "key_name": api_key.name,
        }

    async def list_keys(self, user_id: str) -> List[dict]:
        """
        List all API keys for a user.

        Args:
            user_id: Owner user ID

        Returns:
            List of API key details (without the actual key)
        """
        result = await self.db.execute(
            select(APIKey)
            .where(APIKey.user_id == user_id)
            .order_by(APIKey.created.desc())
        )
        keys = result.scalars().all()

        return [
            {
                "id": k.id,
                "name": k.name,
                "key_prefix": f"fcms_{k.key_prefix}_****",
                "scopes": k.scopes,
                "active": k.active,
                "expires_at": k.expires_at.isoformat() if k.expires_at else None,
                "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
                "last_used_ip": k.last_used_ip,
                "created": k.created.isoformat(),
            }
            for k in keys
        ]

    async def get_key(self, user_id: str, key_id: str) -> dict:
        """
        Get a single API key by ID.

        Args:
            user_id: Owner user ID
            key_id: API key ID

        Returns:
            API key details
        """
        result = await self.db.execute(
            select(APIKey)
            .where(APIKey.id == key_id, APIKey.user_id == user_id)
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            raise NotFoundException("API key not found")

        return {
            "id": api_key.id,
            "name": api_key.name,
            "key_prefix": f"fcms_{api_key.key_prefix}_****",
            "scopes": api_key.scopes,
            "active": api_key.active,
            "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
            "last_used_at": api_key.last_used_at.isoformat() if api_key.last_used_at else None,
            "last_used_ip": api_key.last_used_ip,
            "created": api_key.created.isoformat(),
        }

    async def update_key(
        self,
        user_id: str,
        key_id: str,
        name: Optional[str] = None,
        scopes: Optional[str] = None,
        active: Optional[bool] = None,
        expires_at: Optional[datetime] = None,
    ) -> dict:
        """
        Update an API key.

        Args:
            user_id: Owner user ID
            key_id: API key ID
            name: New name
            scopes: New scopes
            active: Enable/disable
            expires_at: New expiration

        Returns:
            Updated API key details
        """
        result = await self.db.execute(
            select(APIKey)
            .where(APIKey.id == key_id, APIKey.user_id == user_id)
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            raise NotFoundException("API key not found")

        if name is not None:
            api_key.name = name
        if scopes is not None:
            api_key.scopes = scopes
        if active is not None:
            api_key.active = active
        if expires_at is not None:
            api_key.expires_at = expires_at

        await self.db.commit()
        await self.db.refresh(api_key)

        logger.info(f"API key updated: {api_key.name} (id: {key_id})")

        return await self.get_key(user_id, key_id)

    async def delete_key(self, user_id: str, key_id: str) -> None:
        """
        Delete an API key.

        Args:
            user_id: Owner user ID
            key_id: API key ID
        """
        result = await self.db.execute(
            select(APIKey)
            .where(APIKey.id == key_id, APIKey.user_id == user_id)
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            raise NotFoundException("API key not found")

        await self.db.delete(api_key)
        await self.db.commit()

        logger.info(f"API key deleted: {api_key.name} (id: {key_id})")

    async def revoke_all_keys(self, user_id: str) -> int:
        """
        Revoke all API keys for a user (set active=False).

        Args:
            user_id: Owner user ID

        Returns:
            Number of keys revoked
        """
        result = await self.db.execute(
            select(APIKey)
            .where(APIKey.user_id == user_id, APIKey.active == True)
        )
        keys = result.scalars().all()

        count = 0
        for key in keys:
            key.active = False
            count += 1

        await self.db.commit()

        logger.info(f"Revoked {count} API keys for user {user_id}")
        return count
