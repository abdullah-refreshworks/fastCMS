"""
FastAPI dependencies for dependency injection.
"""

from dataclasses import dataclass
from typing import Optional

from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException
from app.core.security import decode_token, verify_token_type
from app.db.session import get_db


@dataclass
class UserContext:
    """User context for authenticated requests."""

    user_id: str
    role: str = "user"


async def get_current_user(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db),
) -> Optional[UserContext]:
    """
    Get current authenticated user context from JWT token.
    Checks both Authorization header and access_token cookie.

    Args:
        authorization: Authorization header with Bearer token
        access_token: JWT token from cookie
        db: Database session

    Returns:
        UserContext with user_id and role, or None if not authenticated

    Raises:
        UnauthorizedException: If token is invalid
    """
    token = None

    # Check Authorization header first
    if authorization:
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                token = None
        except ValueError:
            token = None

    # Fall back to cookie if no header token
    if not token and access_token:
        token = access_token

    # No token found anywhere
    if not token:
        return None

    try:
        payload = decode_token(token)
        if not payload:
            raise UnauthorizedException("Invalid or expired token")

        if not verify_token_type(payload, "access"):
            raise UnauthorizedException("Invalid token type")

        user_id: str = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Invalid token payload")

        # Fetch user role from database
        from app.db.repositories.user import UserRepository

        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)

        if not user:
            raise UnauthorizedException("User not found")

        return UserContext(user_id=user_id, role=user.role)

    except (ValueError, UnauthorizedException):
        return None


async def get_current_user_id(
    user_context: Optional[UserContext] = Depends(get_current_user),
) -> Optional[str]:
    """
    Get current authenticated user ID (backward compatibility).

    Args:
        user_context: User context from get_current_user dependency

    Returns:
        User ID from token or None if not authenticated
    """
    return user_context.user_id if user_context else None


async def require_auth_context(
    user_context: Optional[UserContext] = Depends(get_current_user),
) -> UserContext:
    """
    Dependency that requires authentication and returns UserContext.

    Args:
        user_context: User context from get_current_user dependency

    Returns:
        UserContext with user_id and role

    Raises:
        UnauthorizedException: If user is not authenticated
    """
    if not user_context:
        raise UnauthorizedException("Authentication required")
    return user_context


async def require_auth(
    user_context: Optional[UserContext] = Depends(get_current_user),
) -> str:
    """
    Dependency that requires authentication and returns user ID.
    For backward compatibility with existing endpoints.

    Args:
        user_context: User context from get_current_user dependency

    Returns:
        User ID string

    Raises:
        UnauthorizedException: If user is not authenticated
    """
    if not user_context:
        raise UnauthorizedException("Authentication required")
    return user_context.user_id


async def get_optional_user_id(
    user_id: Optional[str] = Depends(get_current_user_id),
) -> Optional[str]:
    """
    Get user ID if authenticated, otherwise None.
    Useful for endpoints that work with or without auth.

    Args:
        user_id: User ID from get_current_user_id dependency

    Returns:
        User ID or None
    """
    return user_id


async def get_optional_user(
    user_context: Optional[UserContext] = Depends(get_current_user),
) -> Optional[UserContext]:
    """
    Get user context if authenticated, otherwise None.

    Args:
        user_context: User context from get_current_user dependency

    Returns:
        UserContext or None
    """
    return user_context


async def require_admin(
    user_context: UserContext = Depends(require_auth_context),
) -> UserContext:
    """
    Dependency that requires admin role.

    Args:
        user_context: User context from require_auth dependency

    Returns:
        UserContext

    Raises:
        UnauthorizedException: If user is not admin
    """
    if user_context.role != "admin":
        raise UnauthorizedException("Admin access required")
    return user_context
