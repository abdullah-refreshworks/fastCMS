"""
API endpoints for authentication.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_auth
from app.db.session import get_db
from app.schemas.auth import (
    AuthResponse,
    EmailVerification,
    PasswordChange,
    PasswordReset,
    PasswordResetRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    UserUpdate,
)
from app.services.auth_service import AuthService

router = APIRouter()


def get_client_info(request: Request) -> tuple[Optional[str], Optional[str]]:
    """
    Extract client information from request.

    Args:
        request: FastAPI request

    Returns:
        Tuple of (user_agent, ip_address)
    """
    user_agent = request.headers.get("user-agent")
    # Get real IP from proxy headers if behind reverse proxy
    ip_address = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or request.headers.get("x-real-ip")
        or request.client.host if request.client else None
    )
    return user_agent, ip_address


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password.",
)
async def register(
    data: UserRegister,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """
    Register a new user.

    Args:
        data: Registration data
        request: Request object
        db: Database session

    Returns:
        Auth response with user and tokens
    """
    service = AuthService(db)
    user_agent, ip_address = get_client_info(request)
    return await service.register(data, user_agent, ip_address)


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login with email and password",
    description="Authenticate user and receive access and refresh tokens.",
)
async def login(
    data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """
    Login user.

    Args:
        data: Login credentials
        request: Request object
        db: Database session

    Returns:
        Auth response with user and tokens
    """
    service = AuthService(db)
    user_agent, ip_address = get_client_info(request)
    return await service.login(data, user_agent, ip_address)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Get a new access token using a refresh token.",
)
async def refresh_tokens(
    data: RefreshTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Refresh access token.

    Args:
        data: Refresh token
        request: Request object
        db: Database session

    Returns:
        New token response
    """
    service = AuthService(db)
    user_agent, ip_address = get_client_info(request)
    return await service.refresh_tokens(data.refresh_token, user_agent, ip_address)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout user",
    description="Revoke the current refresh token.",
)
async def logout(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Logout user.

    Args:
        data: Refresh token to revoke
        db: Database session
    """
    service = AuthService(db)
    await service.logout(data.refresh_token)


@router.post(
    "/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout from all devices",
    description="Revoke all refresh tokens for the authenticated user. Requires authentication.",
)
async def logout_all(
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Logout user from all devices.

    Args:
        user_id: Authenticated user ID
        db: Database session
    """
    service = AuthService(db)
    await service.logout_all(user_id)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the authenticated user's profile. Requires authentication.",
)
async def get_current_user(
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Get current user profile.

    Args:
        user_id: Authenticated user ID
        db: Database session

    Returns:
        User response
    """
    service = AuthService(db)
    return await service.get_user(user_id)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user",
    description="Update the authenticated user's profile. Requires authentication.",
)
async def update_current_user(
    data: UserUpdate,
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Update current user profile.

    Args:
        data: Update data
        user_id: Authenticated user ID
        db: Database session

    Returns:
        Updated user response
    """
    service = AuthService(db)
    return await service.update_user(user_id, data)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete current user account",
    description="Permanently delete the authenticated user's account and all associated data. Requires authentication.",
)
async def delete_current_user(
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete current user account.

    Args:
        user_id: Authenticated user ID
        db: Database session
    """
    service = AuthService(db)
    await service.delete_user(user_id)


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change password",
    description="Change the authenticated user's password. Requires authentication.",
)
async def change_password(
    data: PasswordChange,
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Change user password.

    Args:
        data: Password change data
        user_id: Authenticated user ID
        db: Database session
    """
    service = AuthService(db)
    await service.change_password(user_id, data)


@router.post(
    "/verify-email",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Verify email",
    description="Verify user email with token received via email.",
)
async def verify_email(
    data: EmailVerification,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Verify user email.

    Args:
        data: Email verification data with token
        db: Database session
    """
    service = AuthService(db)
    await service.verify_email(data.token)


@router.post(
    "/resend-verification",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Resend verification email",
    description="Resend verification email to authenticated user. Requires authentication.",
)
async def resend_verification(
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Resend verification email.

    Args:
        user_id: Authenticated user ID
        db: Database session
    """
    service = AuthService(db)
    await service.resend_verification(user_id)


@router.post(
    "/request-password-reset",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Request password reset",
    description="Request a password reset email. Always returns success to prevent email enumeration.",
)
async def request_password_reset(
    data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Request password reset.

    Args:
        data: Password reset request with email
        db: Database session
    """
    service = AuthService(db)
    await service.request_password_reset(data.email)


@router.post(
    "/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reset password",
    description="Reset password using token received via email.",
)
async def reset_password(
    data: PasswordReset,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Reset password with token.

    Args:
        data: Password reset data with token and new password
        db: Database session
    """
    service = AuthService(db)
    await service.reset_password(data.token, data.password)


@router.get(
    "/sessions",
    summary="Get active sessions",
    description="Get all active sessions for the authenticated user. Requires authentication.",
)
async def get_sessions(
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get active sessions.

    Args:
        user_id: Authenticated user ID
        db: Database session

    Returns:
        Dict with sessions list
    """
    service = AuthService(db)
    sessions = await service.get_sessions(user_id)
    return {"sessions": sessions}


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke session",
    description="Revoke a specific session (refresh token). Requires authentication.",
)
async def revoke_session(
    session_id: str,
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Revoke a session.

    Args:
        session_id: Session ID to revoke
        user_id: Authenticated user ID
        db: Database session
    """
    service = AuthService(db)
    await service.revoke_session(user_id, session_id)
