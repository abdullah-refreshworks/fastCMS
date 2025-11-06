"""
Admin API endpoints for managing users, collections, and system.
Requires admin role for all operations.
"""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import UserContext, require_admin
from app.db.models.collection import Collection
from app.db.models.user import User
from app.db.repositories.collection import CollectionRepository
from app.db.repositories.user import UserRepository
from app.db.session import get_db
from app.schemas.auth import UserResponse
from app.schemas.collection import CollectionResponse

router = APIRouter()


@router.get("/stats", summary="Get system statistics")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _: UserContext = Depends(require_admin),
) -> dict[str, Any]:
    """
    Get system statistics (admin only).

    Returns:
        System statistics including user count, collection count, etc.
    """
    user_repo = UserRepository(db)
    collection_repo = CollectionRepository(db)

    # Count users
    total_users = await user_repo.count()

    # Count collections
    total_collections = await collection_repo.count()

    # Count admin users
    result = await db.execute(select(func.count(User.id)).where(User.role == "admin"))
    admin_users = result.scalar_one()

    # Get recent users (last 7 days)
    from datetime import datetime, timedelta

    seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    result = await db.execute(
        select(func.count(User.id)).where(User.created >= seven_days_ago)
    )
    recent_users = result.scalar_one()

    return {
        "users": {
            "total": total_users,
            "admins": admin_users,
            "recent": recent_users,
        },
        "collections": {
            "total": total_collections,
        },
    }


@router.get("/users", response_model=dict[str, Any], summary="List all users")
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: UserContext = Depends(require_admin),
) -> dict[str, Any]:
    """
    List all users with pagination (admin only).

    Args:
        page: Page number
        per_page: Items per page
        db: Database session
        _: Admin user context

    Returns:
        Paginated list of users
    """
    user_repo = UserRepository(db)

    skip = (page - 1) * per_page
    users = await user_repo.get_all(skip=skip, limit=per_page)
    total = await user_repo.count()

    import math

    total_pages = math.ceil(total / per_page) if total > 0 else 0

    return {
        "items": [UserResponse.model_validate(user) for user in users],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


@router.get("/users/{user_id}", response_model=UserResponse, summary="Get user details")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: UserContext = Depends(require_admin),
) -> UserResponse:
    """
    Get user details by ID (admin only).

    Args:
        user_id: User ID
        db: Database session
        _: Admin user context

    Returns:
        User details
    """
    from app.core.exceptions import NotFoundException

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise NotFoundException(f"User {user_id} not found")

    return UserResponse.model_validate(user)


@router.patch("/users/{user_id}/role", response_model=UserResponse, summary="Update user role")
async def update_user_role(
    user_id: str,
    role: str = Query(..., pattern="^(user|admin)$"),
    db: AsyncSession = Depends(get_db),
    admin: UserContext = Depends(require_admin),
) -> UserResponse:
    """
    Update user role (admin only).

    Args:
        user_id: User ID
        role: New role (user or admin)
        db: Database session
        admin: Admin user context

    Returns:
        Updated user
    """
    from app.core.exceptions import BadRequestException, NotFoundException

    if admin.user_id == user_id:
        raise BadRequestException("Cannot change your own role")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise NotFoundException(f"User {user_id} not found")

    user.role = role
    await user_repo.update(user)
    await db.commit()

    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}", status_code=204, summary="Delete user")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin: UserContext = Depends(require_admin),
) -> None:
    """
    Delete user (admin only).

    Args:
        user_id: User ID
        db: Database session
        admin: Admin user context
    """
    from app.core.exceptions import BadRequestException, NotFoundException

    if admin.user_id == user_id:
        raise BadRequestException("Cannot delete your own account")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise NotFoundException(f"User {user_id} not found")

    await user_repo.delete(user)
    await db.commit()


@router.get(
    "/collections", response_model=dict[str, Any], summary="List all collections (admin view)"
)
async def list_collections_admin(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: UserContext = Depends(require_admin),
) -> dict[str, Any]:
    """
    List all collections with full details (admin only).

    Args:
        page: Page number
        per_page: Items per page
        db: Database session
        _: Admin user context

    Returns:
        Paginated list of collections
    """
    collection_repo = CollectionRepository(db)

    skip = (page - 1) * per_page
    collections = await collection_repo.get_all(skip=skip, limit=per_page)
    total = await collection_repo.count()

    import math

    total_pages = math.ceil(total / per_page) if total > 0 else 0

    return {
        "items": [CollectionResponse.model_validate(col) for col in collections],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


@router.delete("/collections/{collection_id}", status_code=204, summary="Delete collection")
async def delete_collection_admin(
    collection_id: str,
    db: AsyncSession = Depends(get_db),
    _: UserContext = Depends(require_admin),
) -> None:
    """
    Delete a collection (admin only).

    Args:
        collection_id: Collection ID
        db: Database session
        _: Admin user context
    """
    from app.core.exceptions import BadRequestException, NotFoundException

    collection_repo = CollectionRepository(db)
    collection = await collection_repo.get_by_id(collection_id)

    if not collection:
        raise NotFoundException(f"Collection {collection_id} not found")

    if collection.system:
        raise BadRequestException("Cannot delete system collection")

    await collection_repo.delete(collection)
    await db.commit()
