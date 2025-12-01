"""API endpoints for dynamic record CRUD operations."""
from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import UserContext, get_optional_user, require_auth_context
from app.db.session import get_db
from app.schemas.record import (
    BulkDeleteRequest,
    BulkOperationResponse,
    BulkUpdateRequest,
    RecordCreate,
    RecordListResponse,
    RecordResponse,
    RecordUpdate,
)
from app.services.record_service import RecordService
from app.services.csv_service import CSVService
from app.utils.query_parser import QueryParser
from app.db.repositories.collection import CollectionRepository
from app.utils.field_types import FieldSchema
from app.core.exceptions import NotFoundException, ValidationException

router = APIRouter()


@router.post(
    "/collections/{collection_name}/records",
    response_model=RecordResponse,
    status_code=201,
    summary="Create a record",
)
async def create_record(
    collection_name: str = Path(..., description="Collection name"),
    data: RecordCreate = ...,
    db: AsyncSession = Depends(get_db),
    user_context: UserContext = Depends(require_auth_context),
):
    """Create a new record in the specified collection."""
    service = RecordService(db, collection_name, user_context)
    return await service.create_record(data)


@router.get(
    "/collections/{collection_name}/records",
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
    "/collections/{collection_name}/records/export/csv",
    summary="Export records to CSV",
    response_class=Response,
)
async def export_records_csv(
    collection_name: str = Path(..., description="Collection name"),
    filter: Optional[str] = Query(None, description="Filter expression"),
    sort: Optional[str] = Query(None, description="Sort field"),
    db: AsyncSession = Depends(get_db),
    user_context: Optional[UserContext] = Depends(get_optional_user),
):
    """
    Export all records from a collection to CSV format.

    The CSV will include all fields defined in the collection schema plus system fields (id, created, updated).
    """
    # Get collection schema
    collection_repo = CollectionRepository(db)
    collection = await collection_repo.get_by_name(collection_name)
    if not collection:
        raise NotFoundException(f"Collection '{collection_name}' not found")

    # Get records using record service
    service = RecordService(db, collection_name, user_context)

    # Parse filters and sort
    filters = QueryParser.parse_filter(filter) if filter else None
    sort_field, sort_order = QueryParser.parse_sort(sort) if sort else (None, "asc")

    # Get all records (no pagination for export)
    result = await service.list_records(
        page=1,
        per_page=10000,  # Max records to export
        filters=filters,
        sort=sort_field,
        order=sort_order,
    )

    # Extract field schemas
    fields = collection.schema.get("fields", [])
    field_schemas = [FieldSchema(**field) for field in fields]

    # Convert records to list of dicts
    records_data = [record.data for record in result.items]

    # Generate CSV
    csv_content = CSVService.export_to_csv(records_data, field_schemas)

    # Return as downloadable file
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={collection_name}_export.csv"
        },
    )


@router.post(
    "/collections/{collection_name}/records/import/csv",
    summary="Import records from CSV",
    status_code=201,
)
async def import_records_csv(
    collection_name: str = Path(..., description="Collection name"),
    file: UploadFile = File(..., description="CSV file to import"),
    skip_validation: bool = Query(
        False, description="Skip type validation (import as strings)"
    ),
    db: AsyncSession = Depends(get_db),
    user_context: UserContext = Depends(require_auth_context),
):
    """
    Import records from a CSV file.

    The CSV file should have headers matching the collection's field names.
    System fields (id, created, updated) will be ignored if present.

    Returns:
        - imported: Number of records successfully imported
        - errors: List of any errors encountered (if partial import)
    """
    # Validate file type
    if not file.filename.endswith(".csv"):
        raise ValidationException("File must be a CSV file")

    # Get collection schema
    collection_repo = CollectionRepository(db)
    collection = await collection_repo.get_by_name(collection_name)
    if not collection:
        raise NotFoundException(f"Collection '{collection_name}' not found")

    # Read CSV content
    csv_content = await file.read()
    csv_text = csv_content.decode("utf-8")

    # Extract field schemas
    fields = collection.schema.get("fields", [])
    field_schemas = [FieldSchema(**field) for field in fields]

    # Parse CSV
    records_data = CSVService.parse_csv(csv_text, field_schemas, skip_validation)

    # Import records using record service
    service = RecordService(db, collection_name, user_context)
    imported_count = 0
    errors = []

    for i, record_data in enumerate(records_data, start=1):
        try:
            from app.schemas.record import RecordCreate
            await service.create_record(RecordCreate(data=record_data))
            imported_count += 1
        except Exception as e:
            errors.append({"row": i, "error": str(e)})

    await db.commit()

    return {
        "imported": imported_count,
        "total": len(records_data),
        "errors": errors if errors else None,
    }


@router.get(
    "/collections/{collection_name}/records/{record_id}",
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
    "/collections/{collection_name}/records/{record_id}",
    response_model=RecordResponse,
    summary="Update a record",
)
async def update_record(
    collection_name: str = Path(..., description="Collection name"),
    record_id: str = Path(..., description="Record ID"),
    data: RecordUpdate = ...,
    db: AsyncSession = Depends(get_db),
    user_context: UserContext = Depends(require_auth_context),
):
    """Update a specific record."""
    service = RecordService(db, collection_name, user_context)
    return await service.update_record(record_id, data)


@router.delete(
    "/collections/{collection_name}/records/{record_id}",
    status_code=204,
    summary="Delete a record",
)
async def delete_record(
    collection_name: str = Path(..., description="Collection name"),
    record_id: str = Path(..., description="Record ID"),
    db: AsyncSession = Depends(get_db),
    user_context: UserContext = Depends(require_auth_context),
):
    """Delete a specific record."""
    service = RecordService(db, collection_name, user_context)
    await service.delete_record(record_id)
    return None


@router.post(
    "/collections/{collection_name}/records/bulk-delete",
    response_model=BulkOperationResponse,
    summary="Bulk delete records",
)
async def bulk_delete_records(
    collection_name: str = Path(..., description="Collection name"),
    request: BulkDeleteRequest = ...,
    db: AsyncSession = Depends(get_db),
    user_context: UserContext = Depends(require_auth_context),
):
    """
    Delete multiple records at once.

    Returns a summary of successful and failed deletions.
    Maximum 100 records per request.
    """
    service = RecordService(db, collection_name, user_context)

    success = 0
    failed = 0
    errors = []

    for record_id in request.record_ids:
        try:
            await service.delete_record(record_id)
            success += 1
        except Exception as e:
            failed += 1
            errors.append({
                "record_id": record_id,
                "error": str(e)
            })

    await db.commit()

    return BulkOperationResponse(
        success=success,
        failed=failed,
        errors=errors if errors else None
    )


@router.post(
    "/collections/{collection_name}/records/bulk-update",
    response_model=BulkOperationResponse,
    summary="Bulk update records",
)
async def bulk_update_records(
    collection_name: str = Path(..., description="Collection name"),
    request: BulkUpdateRequest = ...,
    db: AsyncSession = Depends(get_db),
    user_context: UserContext = Depends(require_auth_context),
):
    """
    Update multiple records at once with the same data.

    Returns a summary of successful and failed updates.
    Maximum 100 records per request.
    """
    service = RecordService(db, collection_name, user_context)

    success = 0
    failed = 0
    errors = []

    update_data = RecordUpdate(data=request.data)

    for record_id in request.record_ids:
        try:
            await service.update_record(record_id, update_data)
            success += 1
        except Exception as e:
            failed += 1
            errors.append({
                "record_id": record_id,
                "error": str(e)
            })

    await db.commit()

    return BulkOperationResponse(
        success=success,
        failed=failed,
        errors=errors if errors else None
    )
