"""Batch operations API"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Path
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_auth_context, UserContext
from app.db.models.user import User
from app.db.session import get_db
from app.services.batch_service import BatchService
from app.services.record_service import RecordService
from app.schemas.record import RecordCreate, RecordResponse
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


class BatchRequest(BaseModel):
    method: str
    url: str
    body: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None


class BatchRequestBody(BaseModel):
    requests: List[BatchRequest]


class BatchRecordCreate(BaseModel):
    """Schema for batch record creation."""
    records: List[Dict[str, Any]] = Field(..., description="List of record data objects", min_length=1, max_length=100)


class BatchRecordUpsert(BaseModel):
    """Schema for batch record upsert (create or update)."""
    records: List[Dict[str, Any]] = Field(..., description="List of record data objects (include 'id' to update)", min_length=1, max_length=100)


class BatchCreateResponse(BaseModel):
    """Response for batch create operation."""
    created: int
    failed: int
    records: List[RecordResponse]
    errors: Optional[List[Dict[str, Any]]] = None


class BatchUpsertResponse(BaseModel):
    """Response for batch upsert operation."""
    created: int
    updated: int
    failed: int
    records: List[RecordResponse]
    errors: Optional[List[Dict[str, Any]]] = None


@router.post("/batch")
async def execute_batch(
    request: Request,
    body: BatchRequestBody,
    user: User = Depends(get_current_user),
):
    """
    Execute multiple API requests in a single batch

    Example:
    ```json
    {
      "requests": [
        {"method": "POST", "url": "/api/v1/posts/records", "body": {"title": "Post 1"}},
        {"method": "POST", "url": "/api/v1/posts/records", "body": {"title": "Post 2"}}
      ]
    }
    ```
    """
    if len(body.requests) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 requests per batch")

    service = BatchService()

    # Get auth token from request
    auth_header = request.headers.get("authorization")
    auth_token = auth_header.split(" ")[1] if auth_header and " " in auth_header else None

    base_url = str(request.base_url).rstrip("/")

    results = await service.execute_batch(
        requests=[req.dict() for req in body.requests],
        base_url=base_url,
        auth_token=auth_token,
    )

    return {"results": results, "count": len(results)}


@router.post(
    "/collections/{collection_name}/records/batch",
    response_model=BatchCreateResponse,
    status_code=201,
    summary="Batch create records",
)
async def batch_create_records(
    collection_name: str = Path(..., description="Collection name"),
    body: BatchRecordCreate = ...,
    db: AsyncSession = Depends(get_db),
    user_context: UserContext = Depends(require_auth_context),
):
    """
    Create multiple records in a single request.

    Maximum 100 records per request.

    Example:
    ```json
    {
      "records": [
        {"title": "Post 1", "content": "Content 1"},
        {"title": "Post 2", "content": "Content 2"},
        {"title": "Post 3", "content": "Content 3"}
      ]
    }
    ```
    """
    service = RecordService(db, collection_name, user_context)

    created_records = []
    errors = []
    created_count = 0
    failed_count = 0

    for i, record_data in enumerate(body.records):
        try:
            record = await service.create_record(RecordCreate(data=record_data))
            created_records.append(record)
            created_count += 1
        except Exception as e:
            failed_count += 1
            errors.append({
                "index": i,
                "data": record_data,
                "error": str(e)
            })

    await db.commit()

    return BatchCreateResponse(
        created=created_count,
        failed=failed_count,
        records=created_records,
        errors=errors if errors else None
    )


@router.post(
    "/collections/{collection_name}/records/upsert",
    response_model=BatchUpsertResponse,
    status_code=200,
    summary="Batch upsert records",
)
async def batch_upsert_records(
    collection_name: str = Path(..., description="Collection name"),
    body: BatchRecordUpsert = ...,
    db: AsyncSession = Depends(get_db),
    user_context: UserContext = Depends(require_auth_context),
):
    """
    Create or update multiple records in a single request.

    Include 'id' in a record to update it, otherwise a new record is created.
    Maximum 100 records per request.

    Example:
    ```json
    {
      "records": [
        {"title": "New Post"},
        {"id": "existing-id-123", "title": "Updated Post"}
      ]
    }
    ```
    """
    from app.schemas.record import RecordUpdate

    service = RecordService(db, collection_name, user_context)

    result_records = []
    errors = []
    created_count = 0
    updated_count = 0
    failed_count = 0

    for i, record_data in enumerate(body.records):
        try:
            record_id = record_data.pop("id", None)

            if record_id:
                # Update existing record
                try:
                    record = await service.update_record(record_id, RecordUpdate(data=record_data))
                    result_records.append(record)
                    updated_count += 1
                except Exception:
                    # If update fails (record not found), create new
                    record = await service.create_record(RecordCreate(data=record_data))
                    result_records.append(record)
                    created_count += 1
            else:
                # Create new record
                record = await service.create_record(RecordCreate(data=record_data))
                result_records.append(record)
                created_count += 1
        except Exception as e:
            failed_count += 1
            errors.append({
                "index": i,
                "data": record_data,
                "error": str(e)
            })

    await db.commit()

    return BatchUpsertResponse(
        created=created_count,
        updated=updated_count,
        failed=failed_count,
        records=result_records,
        errors=errors if errors else None
    )
