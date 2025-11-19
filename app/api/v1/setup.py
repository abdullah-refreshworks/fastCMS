"""
Initial setup API endpoints.
Allows creating the first admin user when database is empty.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.session import get_db
from app.schemas.auth import UserRegister, AuthResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.get("/check")
async def check_setup_needed(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Check if initial setup is needed.

    Returns:
        Dictionary with needs_setup boolean
    """
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    needs_setup = user is None

    return {"needs_setup": needs_setup}


@router.post("", response_model=AuthResponse)
async def create_initial_admin(
    data: UserRegister,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """
    Create the first admin user.
    Only works if database has no users.

    Args:
        data: User registration data
        db: Database session

    Returns:
        AuthResponse with user and tokens

    Raises:
        HTTPException: If setup is already completed or validation fails
    """
    # Check if any users exist
    result = await db.execute(select(User).limit(1))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Setup already completed. Users exist in database.",
        )

    # Create the user with admin role
    auth_service = AuthService(db)

    # Register the user (returns AuthResponse)
    response = await auth_service.register(
        data=data,
        user_agent=None,
        ip_address=None,
    )

    # Upgrade to admin - need to fetch fresh from DB after commit in register
    user_id = response.user.id

    # Use a new query to get the user object that's attached to this session
    result = await db.execute(select(User).where(User.id == user_id))
    user_obj = result.scalar_one_or_none()

    if not user_obj:
        raise HTTPException(status_code=500, detail="Failed to create user")

    user_obj.role = "admin"
    user_obj.verified = True  # First admin is auto-verified
    await db.commit()
    await db.refresh(user_obj)

    # Update response with admin role
    response.user.role = "admin"
    response.user.verified = True

    return response
