"""
API endpoints for view collections.
View collections are read-only virtual collections that compute data from other collections.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_auth
from app.db.session import get_db
from app.schemas.view import ViewResultList
from app.services.view_service import ViewService

router = APIRouter()


@router.get(
    "/{view_name}/records",
    response_model=ViewResultList,
    summary="Query a view collection",
    description="Execute a view collection query and return computed results. View collections are read-only.",
)
async def query_view(
    view_name: str,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(30, ge=1, le=200, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> ViewResultList:
    """
    Query a view collection.

    View collections don't store data - they compute it on-the-fly from other collections.
    Results are cached for performance.

    Args:
        view_name: Name of the view collection
        page: Page number (1-indexed)
        per_page: Items per page (max 200)
        db: Database session

    Returns:
        Computed results from the view
    """
    service = ViewService(db)
    results, total = await service.execute_view(
        view_name=view_name,
        page=page,
        per_page=per_page,
    )

    return ViewResultList(
        items=results,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post(
    "/{view_name}/refresh",
    summary="Refresh view cache",
    description="Invalidate cached results for a view collection. Requires authentication.",
)
async def refresh_view(
    view_name: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth),
) -> Dict[str, str]:
    """
    Refresh (invalidate) the cache for a view collection.

    This will force the next query to re-compute results.

    Args:
        view_name: Name of the view collection
        db: Database session
        user_id: Authenticated user ID

    Returns:
        Success message
    """
    service = ViewService(db)
    await service.invalidate_view_cache(view_name)

    return {"message": f"Cache refreshed for view '{view_name}'"}
