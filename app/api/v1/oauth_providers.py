"""OAuth Provider management API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_admin, UserContext
from app.db.session import get_db
from app.db.models.oauth_provider import OAuthProvider, OAuthProviderType, PROVIDER_METADATA
from app.db.repositories.oauth_provider import OAuthProviderRepository
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# Pydantic models for API
class OAuthProviderCreate(BaseModel):
    """Create OAuth provider request."""
    provider_type: str = Field(..., description="Provider type (e.g., 'google', 'github')")
    name: Optional[str] = Field(None, description="Display name (uses default if not provided)")
    client_id: str = Field(..., description="OAuth client ID")
    client_secret: str = Field(..., description="OAuth client secret")
    enabled: bool = Field(True, description="Enable this provider")
    extra_config: Optional[dict] = Field(default_factory=dict, description="Additional config (custom_url, team_id, etc.)")
    custom_scopes: Optional[str] = Field(None, description="Custom scopes (comma-separated)")
    collection_id: Optional[str] = Field(None, description="Restrict to specific collection")


class OAuthProviderUpdate(BaseModel):
    """Update OAuth provider request."""
    name: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    enabled: Optional[bool] = None
    extra_config: Optional[dict] = None
    custom_scopes: Optional[str] = None
    collection_id: Optional[str] = None


class OAuthProviderResponse(BaseModel):
    """OAuth provider response."""
    id: str
    provider_type: str
    name: str
    enabled: bool
    client_id: str
    has_secret: bool
    extra_config: dict
    custom_scopes: Optional[str]
    collection_id: Optional[str]
    display_order: int
    created: Optional[str]
    updated: Optional[str]

    class Config:
        from_attributes = True


class ProviderMetadataResponse(BaseModel):
    """Provider metadata response."""
    type: str
    name: str
    required_fields: List[str]
    optional_fields: List[str] = []
    scopes: List[str] = []


class ReorderRequest(BaseModel):
    """Reorder providers request."""
    provider_ids: List[str]


@router.get("/types", response_model=List[ProviderMetadataResponse])
async def list_provider_types():
    """List all available OAuth provider types with their required fields."""
    result = []
    for provider_type in OAuthProviderType.all_types():
        metadata = PROVIDER_METADATA.get(provider_type, {})
        result.append(ProviderMetadataResponse(
            type=provider_type,
            name=metadata.get("name", provider_type.title()),
            required_fields=metadata.get("required_fields", ["client_id", "client_secret"]),
            optional_fields=metadata.get("optional_fields", []),
            scopes=metadata.get("scopes", []),
        ))
    return result


@router.get("", response_model=List[OAuthProviderResponse])
async def list_providers(
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_admin),
):
    """List all configured OAuth providers (admin only)."""
    repo = OAuthProviderRepository(db)
    providers = await repo.get_all(enabled_only=enabled_only)
    return [
        OAuthProviderResponse(
            id=p.id,
            provider_type=p.provider_type,
            name=p.name,
            enabled=p.enabled,
            client_id=p.client_id[:8] + "..." if len(p.client_id) > 8 else p.client_id,  # Mask
            has_secret=bool(p.client_secret),
            extra_config={k: v for k, v in (p.extra_config or {}).items()
                         if k not in ("private_key",)},
            custom_scopes=p.custom_scopes,
            collection_id=p.collection_id,
            display_order=p.display_order,
            created=p.created.isoformat() if p.created else None,
            updated=p.updated.isoformat() if p.updated else None,
        )
        for p in providers
    ]


@router.get("/enabled")
async def list_enabled_providers(
    collection_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List enabled OAuth providers (public - for login UI)."""
    repo = OAuthProviderRepository(db)
    providers = await repo.get_for_collection(collection_id)
    return [
        {
            "type": p.provider_type,
            "name": p.name,
            "auth_url": p.get_auth_url(),
        }
        for p in providers
    ]


@router.get("/{provider_id}", response_model=OAuthProviderResponse)
async def get_provider(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_admin),
):
    """Get OAuth provider by ID (admin only)."""
    repo = OAuthProviderRepository(db)
    provider = await repo.get_by_id(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    return OAuthProviderResponse(
        id=provider.id,
        provider_type=provider.provider_type,
        name=provider.name,
        enabled=provider.enabled,
        client_id=provider.client_id,
        has_secret=bool(provider.client_secret),
        extra_config=provider.extra_config or {},
        custom_scopes=provider.custom_scopes,
        collection_id=provider.collection_id,
        display_order=provider.display_order,
        created=provider.created.isoformat() if provider.created else None,
        updated=provider.updated.isoformat() if provider.updated else None,
    )


@router.post("", response_model=OAuthProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(
    data: OAuthProviderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_admin),
):
    """Create a new OAuth provider configuration (admin only)."""
    repo = OAuthProviderRepository(db)

    # Check if provider type already exists
    existing = await repo.get_by_type(data.provider_type)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{data.provider_type}' already configured"
        )

    # Validate provider type
    if data.provider_type not in OAuthProviderType.all_types():
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider type: {data.provider_type}"
        )

    # Get display name from metadata if not provided
    metadata = PROVIDER_METADATA.get(data.provider_type, {})
    name = data.name or metadata.get("name", data.provider_type.title())

    provider = OAuthProvider(
        provider_type=data.provider_type,
        name=name,
        client_id=data.client_id,
        client_secret=data.client_secret,
        enabled=data.enabled,
        extra_config=data.extra_config or {},
        custom_scopes=data.custom_scopes,
        collection_id=data.collection_id,
    )

    provider = await repo.create(provider)
    await db.commit()

    logger.info(f"Created OAuth provider: {data.provider_type}")

    return OAuthProviderResponse(
        id=provider.id,
        provider_type=provider.provider_type,
        name=provider.name,
        enabled=provider.enabled,
        client_id=provider.client_id[:8] + "...",
        has_secret=bool(provider.client_secret),
        extra_config=provider.extra_config or {},
        custom_scopes=provider.custom_scopes,
        collection_id=provider.collection_id,
        display_order=provider.display_order,
        created=provider.created.isoformat() if provider.created else None,
        updated=provider.updated.isoformat() if provider.updated else None,
    )


@router.patch("/{provider_id}", response_model=OAuthProviderResponse)
async def update_provider(
    provider_id: str,
    data: OAuthProviderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_admin),
):
    """Update an OAuth provider configuration (admin only)."""
    repo = OAuthProviderRepository(db)
    provider = await repo.get_by_id(provider_id)

    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    # Update fields
    if data.name is not None:
        provider.name = data.name
    if data.client_id is not None:
        provider.client_id = data.client_id
    if data.client_secret is not None:
        provider.client_secret = data.client_secret
    if data.enabled is not None:
        provider.enabled = data.enabled
    if data.extra_config is not None:
        provider.extra_config = data.extra_config
    if data.custom_scopes is not None:
        provider.custom_scopes = data.custom_scopes
    if data.collection_id is not None:
        provider.collection_id = data.collection_id

    provider = await repo.update(provider)
    await db.commit()

    logger.info(f"Updated OAuth provider: {provider.provider_type}")

    return OAuthProviderResponse(
        id=provider.id,
        provider_type=provider.provider_type,
        name=provider.name,
        enabled=provider.enabled,
        client_id=provider.client_id[:8] + "...",
        has_secret=bool(provider.client_secret),
        extra_config=provider.extra_config or {},
        custom_scopes=provider.custom_scopes,
        collection_id=provider.collection_id,
        display_order=provider.display_order,
        created=provider.created.isoformat() if provider.created else None,
        updated=provider.updated.isoformat() if provider.updated else None,
    )


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_admin),
):
    """Delete an OAuth provider configuration (admin only)."""
    repo = OAuthProviderRepository(db)
    provider = await repo.get_by_id(provider_id)

    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    await repo.delete(provider)
    await db.commit()

    logger.info(f"Deleted OAuth provider: {provider.provider_type}")


@router.post("/reorder", status_code=status.HTTP_200_OK)
async def reorder_providers(
    data: ReorderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_admin),
):
    """Reorder OAuth providers (admin only)."""
    repo = OAuthProviderRepository(db)
    await repo.reorder(data.provider_ids)
    await db.commit()

    return {"message": "Providers reordered successfully"}
