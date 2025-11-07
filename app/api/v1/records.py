"""API endpoints for dynamic record CRUD operations."""
from typing import Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import UserContext, get_optional_user, require_auth
from app.db.session import get_db
from app.schemas.record import (
    RecordCreate,
    RecordListResponse,
    RecordResponse,
    RecordUpdate,
)
from app.services.record_service import RecordService
from app.utils.query_parser import QueryParser

router = APIRouter()


@router.post(
    "/{collection_name}/records",
    response_model=RecordResponse,
    status_code=201,
    summary="Create a record",
)
async def create_record(
    collection_name: str = Path(..., description="Collection name"),
    data: RecordCreate = ...,
    db: AsyncSession = Depends(get_db),
    user_context: UserContext = Depends(require_auth),
):
    """Create a new record in the specified collection."""
    service = RecordService(db, collection_name, user_context)
    return await service.create_record(data)


@router.get(
    "/{collection_name}/records",
    response_model=RecordListResponse,
    summary="List records",
)
async def list_records(
    collection_name: str = Path(..., description="Collection name"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    filter: Optional[str] = Query(
        None, description="Filter expression (e.g., age>=18&&status=active)"
    ),
    sort: Optional[str] = Query(None, description="Sort field (prefix with - for desc)"),
    expand: Optional[str] = Query(None, description="Comma-separated relation fields to expand"),
    db: AsyncSession = Depends(get_db),
    user_context: Optional[UserContext] = Depends(get_optional_user),
):
    """
    List records with advanced filtering and sorting.

    Filter examples:
    - ?filter=age>=18
    - ?filter=status=active&&verified=true
    - ?filter=email~gmail.com

    Sort examples:
    - ?sort=created (ascending)
    - ?sort=-created (descending)

    Expand examples:
    - ?expand=author
    - ?expand=author,category
    """
    service = RecordService(db, collection_name, user_context)

    # Parse filters
    filters = QueryParser.parse_filter(filter) if filter else None

    # Parse sort
    sort_field, sort_order = QueryParser.parse_sort(sort) if sort else (None, "asc")

    # Parse expand
    expand_fields = expand.split(",") if expand else None

    return await service.list_records(
        page=page,
        per_page=per_page,
        filters=filters,
        sort=sort_field,
        order=sort_order,
        expand=expand_fields,
    )


@router.get(
    "/{collection_name}/records/{record_id}",
    response_model=RecordResponse,
    summary="Get a record",
)
async def get_record(
    collection_name: str = Path(..., description="Collection name"),
    record_id: str = Path(..., description="Record ID"),
    expand: Optional[str] = Query(None, description="Comma-separated relation fields to expand"),
    db: AsyncSession = Depends(get_db),
    user_context: Optional[UserContext] = Depends(get_optional_user),
):
    """Get a specific record by ID with optional relation expansion."""
    service = RecordService(db, collection_name, user_context)
    expand_fields = expand.split(",") if expand else None
    return await service.get_record(record_id, expand=expand_fields)


@router.patch(
    "/{collection_name}/records/{record_id}",
    response_model=RecordResponse,
    summary="Update a record",
)
async def update_record(
    collection_name: str = Path(..., description="Collection name"),
    record_id: str = Path(..., description="Record ID"),
    data: RecordUpdate = ...,
    db: AsyncSession = Depends(get_db),
    user_context: UserContext = Depends(require_auth),
):
    """Update a specific record."""
    service = RecordService(db, collection_name, user_context)
    return await service.update_record(record_id, data)


@router.delete(
    "/{collection_name}/records/{record_id}",
    status_code=204,
    summary="Delete a record",
)
async def delete_record(
    collection_name: str = Path(..., description="Collection name"),
    record_id: str = Path(..., description="Record ID"),
    db: AsyncSession = Depends(get_db),
    user_context: UserContext = Depends(require_auth),
):
    """Delete a specific record."""
    service = RecordService(db, collection_name, user_context)
    await service.delete_record(record_id)
    return None
