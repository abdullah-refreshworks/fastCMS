"""
API endpoints for API Key management.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_auth
from app.db.session import get_db
from app.services.api_key_service import APIKeyService

router = APIRouter()


# ===== Schemas =====

class APIKeyCreate(BaseModel):
    """Schema for creating an API key."""

    name: str = Field(..., min_length=1, max_length=255, description="Key name")
    scopes: Optional[str] = Field("*", description="Comma-separated scopes or * for all")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration datetime")


class APIKeyUpdate(BaseModel):
    """Schema for updating an API key."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    scopes: Optional[str] = None
    active: Optional[bool] = None
    expires_at: Optional[datetime] = None


class APIKeyResponse(BaseModel):
    """API key response (without secret)."""

    id: str
    name: str
    key_prefix: str
    scopes: Optional[str]
    active: bool
    expires_at: Optional[str]
    last_used_at: Optional[str]
    last_used_ip: Optional[str]
    created: str


class APIKeyCreateResponse(BaseModel):
    """Response after creating an API key (includes full key)."""

    id: str
    name: str
    key: str = Field(..., description="Full API key - save this, it won't be shown again!")
    key_prefix: str
    scopes: Optional[str]
    expires_at: Optional[str]
    created: str
    message: str


# ===== Endpoints =====

@router.post(
    "",
    response_model=APIKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create API key",
    description="Create a new API key. The full key is only shown once!",
)
async def create_api_key(
    data: APIKeyCreate,
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new API key."""
    service = APIKeyService(db)
    return await service.create_key(
        user_id=user_id,
        name=data.name,
        scopes=data.scopes,
        expires_at=data.expires_at,
    )


@router.get(
    "",
    response_model=List[APIKeyResponse],
    summary="List API keys",
    description="List all API keys for the authenticated user.",
)
async def list_api_keys(
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """List all API keys."""
    service = APIKeyService(db)
    return await service.list_keys(user_id)


@router.get(
    "/{key_id}",
    response_model=APIKeyResponse,
    summary="Get API key",
    description="Get details for a specific API key.",
)
async def get_api_key(
    key_id: str,
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a specific API key."""
    service = APIKeyService(db)
    return await service.get_key(user_id, key_id)


@router.patch(
    "/{key_id}",
    response_model=APIKeyResponse,
    summary="Update API key",
    description="Update an API key's name, scopes, or status.",
)
async def update_api_key(
    key_id: str,
    data: APIKeyUpdate,
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update an API key."""
    service = APIKeyService(db)
    return await service.update_key(
        user_id=user_id,
        key_id=key_id,
        name=data.name,
        scopes=data.scopes,
        active=data.active,
        expires_at=data.expires_at,
    )


@router.delete(
    "/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete API key",
    description="Permanently delete an API key.",
)
async def delete_api_key(
    key_id: str,
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an API key."""
    service = APIKeyService(db)
    await service.delete_key(user_id, key_id)


@router.post(
    "/revoke-all",
    summary="Revoke all API keys",
    description="Disable all API keys for the authenticated user.",
)
async def revoke_all_api_keys(
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Revoke all API keys."""
    service = APIKeyService(db)
    count = await service.revoke_all_keys(user_id)
    return {"revoked": count, "message": f"Revoked {count} API keys"}
