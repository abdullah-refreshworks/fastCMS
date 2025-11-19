"""Batch operations API"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from app.core.dependencies import get_current_user
from app.db.models.user import User
from app.services.batch_service import BatchService
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
