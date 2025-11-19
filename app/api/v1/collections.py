"""
API endpoints for collection management.
"""

from typing import Any
import json

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io

from app.core.dependencies import require_auth, require_admin
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
    return await service.create_collection(data)


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

    return CollectionListResponse(
        items=collections,
        total=total,
        page=page,
        per_page=per_page,
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
    return await service.get_collection(collection_id)


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
    return await service.update_collection(collection_id, data)


@router.delete(
    "/{collection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a collection",
    description="Delete a collection and its associated table. Requires authentication.",
)
async def delete_collection(
    collection_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
) -> None:
    """
    Delete a collection.

    Args:
        collection_id: Collection ID
        db: Database session
        user_id: Authenticated user ID
    """
    service = CollectionService(db)
    await service.delete_collection(collection_id)


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
    return await service.get_collection_by_name(collection_name)


@router.get(
    "/{collection_id}/export",
    summary="Export collection",
    description="Export collection schema and optionally data as JSON. Admin only.",
)
async def export_collection(
    collection_id: str,
    include_data: bool = Query(False, description="Include collection records in export"),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    """
    Export a collection as JSON.

    - Exports collection schema
    - Optionally exports all records
    - Returns downloadable JSON file
    """
    service = CollectionService(db)
    collection = await service.get_collection(collection_id)

    export_data = {
        "name": collection.name,
        "type": collection.type,
        "schema": collection.schema,
        "list_rule": collection.list_rule,
        "view_rule": collection.view_rule,
        "create_rule": collection.create_rule,
        "update_rule": collection.update_rule,
        "delete_rule": collection.delete_rule,
        "indexes": collection.indexes or [],
        "system": collection.system,
    }

    # Include records if requested
    if include_data:
        from app.services.record_service import RecordService

        record_service = RecordService(db)
        records_response = await record_service.list_records(
            collection_name=collection.name,
            page=1,
            per_page=10000,  # Export up to 10k records
        )
        export_data["records"] = [
            {
                "id": record.id,
                "data": record.data,
                "created": record.created.isoformat() if record.created else None,
                "updated": record.updated.isoformat() if record.updated else None,
            }
            for record in records_response.items
        ]

    # Create JSON response
    json_str = json.dumps(export_data, indent=2)
    buffer = io.BytesIO(json_str.encode())

    return StreamingResponse(
        buffer,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={collection.name}_export.json"
        },
    )


@router.post(
    "/import",
    response_model=CollectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import collection",
    description="Import a collection from JSON export. Admin only.",
)
async def import_collection(
    data: dict,
    import_records: bool = Query(
        False, description="Import records along with collection"
    ),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    """
    Import a collection from JSON export.

    - Creates collection from schema
    - Optionally imports records
    - Returns created collection
    """
    service = CollectionService(db)

    # Extract collection data
    collection_data = CollectionCreate(
        name=data["name"],
        type=data.get("type", "base"),
        schema=data["schema"],
        list_rule=data.get("list_rule"),
        view_rule=data.get("view_rule"),
        create_rule=data.get("create_rule"),
        update_rule=data.get("update_rule"),
        delete_rule=data.get("delete_rule"),
        indexes=data.get("indexes", []),
    )

    # Create collection
    collection = await service.create_collection(collection_data)

    # Import records if requested
    if import_records and "records" in data:
        from app.services.record_service import RecordService

        record_service = RecordService(db)

        for record in data["records"]:
            try:
                await record_service.create_record(
                    collection_name=collection.name, data=record["data"]
                )
            except Exception as e:
                # Log but continue importing other records
                print(f"Failed to import record: {str(e)}")
                continue

    return collection
