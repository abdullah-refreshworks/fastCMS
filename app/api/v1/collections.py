"""
API endpoints for collection management.
"""

from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_auth
from app.db.session import get_db
from app.schemas.collection import (
    CollectionCreate,
    CollectionListResponse,
    CollectionResponse,
    CollectionUpdate,
)
from app.services.collection_service import CollectionService

router = APIRouter()


@router.post(
    "",
    response_model=CollectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new collection",
    description="Create a new collection with dynamic schema. Requires authentication.",
)
async def create_collection(
    data: CollectionCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
) -> CollectionResponse:
    """
    Create a new collection.

    Args:
        data: Collection creation data
        db: Database session
        user_id: Authenticated user ID

    Returns:
        Created collection
    """
    service = CollectionService(db)
    collection = await service.create_collection(data)
    collection.message = f"✅ Collection '{collection.name}' created successfully! You can now start adding records."
    return collection


@router.get(
    "",
    response_model=CollectionListResponse,
    summary="List all collections",
    description="Get a paginated list of all collections.",
)
async def list_collections(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(30, ge=1, le=200, description="Items per page"),
    include_system: bool = Query(False, description="Include system collections"),
    db: AsyncSession = Depends(get_db),
) -> CollectionListResponse:
    """
    List all collections with pagination.

    Args:
        page: Page number (1-indexed)
        per_page: Items per page (max 200)
        include_system: Include system collections
        db: Database session

    Returns:
        Paginated list of collections
    """
    service = CollectionService(db)
    collections, total = await service.list_collections(
        page=page,
        per_page=per_page,
        include_system=include_system,
    )

    count = len(collections)
    message = f"✅ Retrieved {count} collection{'s' if count != 1 else ''}"
    if total > count:
        message += f" (page {page} of {(total + per_page - 1) // per_page})"

    return CollectionListResponse(
        items=collections,
        total=total,
        page=page,
        per_page=per_page,
        message=message,
    )


@router.get(
    "/{collection_id}",
    response_model=CollectionResponse,
    summary="Get a collection by ID",
    description="Retrieve a single collection by its ID.",
)
async def get_collection(
    collection_id: str,
    db: AsyncSession = Depends(get_db),
) -> CollectionResponse:
    """
    Get collection by ID.

    Args:
        collection_id: Collection ID
        db: Database session

    Returns:
        Collection data
    """
    service = CollectionService(db)
    collection = await service.get_collection(collection_id)
    collection.message = f"✅ Collection '{collection.name}' retrieved successfully!"
    return collection


@router.patch(
    "/{collection_id}",
    response_model=CollectionResponse,
    summary="Update a collection",
    description="Update collection schema, rules, or options. Requires authentication.",
)
async def update_collection(
    collection_id: str,
    data: CollectionUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
) -> CollectionResponse:
    """
    Update a collection.

    Args:
        collection_id: Collection ID
        data: Update data
        db: Database session
        user_id: Authenticated user ID

    Returns:
        Updated collection
    """
    service = CollectionService(db)
    collection = await service.update_collection(collection_id, data)
    collection.message = f"✅ Collection '{collection.name}' updated successfully!"
    return collection


@router.delete(
    "/{collection_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a collection",
    description="Delete a collection and its associated table. Requires authentication.",
)
async def delete_collection(
    collection_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
) -> dict[str, str]:
    """
    Delete a collection.

    Args:
        collection_id: Collection ID
        db: Database session
        user_id: Authenticated user ID

    Returns:
        Success message
    """
    service = CollectionService(db)
    collection = await service.get_collection(collection_id)  # Get name before deletion
    collection_name = collection.name
    await service.delete_collection(collection_id)
    return {"message": f"✅ Collection '{collection_name}' and all its records have been deleted successfully."}


@router.get(
    "/name/{collection_name}",
    response_model=CollectionResponse,
    summary="Get a collection by name",
    description="Retrieve a single collection by its name.",
)
async def get_collection_by_name(
    collection_name: str,
    db: AsyncSession = Depends(get_db),
) -> CollectionResponse:
    """
    Get collection by name.

    Args:
        collection_name: Collection name
        db: Database session

    Returns:
        Collection data
    """
    service = CollectionService(db)
    collection = await service.get_collection_by_name(collection_name)
    collection.message = f"✅ Collection '{collection.name}' retrieved successfully!"
    return collection
