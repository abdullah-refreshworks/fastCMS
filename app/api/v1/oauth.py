"""
API endpoints for OAuth2 social authentication.
"""

from typing import Optional

from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from app.core.dependencies import require_auth
from app.db.session import get_db
from app.schemas.oauth import OAuthAccountResponse, OAuthAccountsList, OAuthUnlinkRequest
from app.services.oauth_service import oauth, OAuthService

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


@router.get(
    "/login/{provider}",
    summary="Initiate OAuth2 login",
    description="Redirect to OAuth provider for authentication. Supported providers: google, github, microsoft.",
)
async def oauth_login(provider: str, request: Request) -> RedirectResponse:
    """
    Initiate OAuth login flow.

    Args:
        provider: OAuth provider name (google, github, microsoft)
        request: Request object

    Returns:
        Redirect to OAuth provider
    """
    if provider not in ["google", "github", "microsoft"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}",
        )

    # Get OAuth client
    client = oauth.create_client(provider)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth provider {provider} not configured",
        )

    # Build callback URL
    redirect_uri = request.url_for("oauth_callback", provider=provider)

    # Redirect to provider
    return await client.authorize_redirect(request, redirect_uri)


@router.get(
    "/callback/{provider}",
    summary="OAuth2 callback",
    description="Handle OAuth callback from provider. This endpoint receives the authorization code.",
)
async def oauth_callback(
    provider: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle OAuth callback and authenticate user.

    Args:
        provider: OAuth provider name
        request: Request object
        db: Database session

    Returns:
        Auth response with user and tokens
    """
    if provider not in ["google", "github", "microsoft"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}",
        )

    # Get OAuth client
    client = oauth.create_client(provider)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth provider {provider} not configured",
        )

    try:
        # Exchange authorization code for access token
        token = await client.authorize_access_token(request)

        # Get user info from provider
        if provider == "google":
            user_info = token.get("userinfo")
            if not user_info:
                resp = await client.get("https://www.googleapis.com/oauth2/v3/userinfo")
                user_info = resp.json()
        elif provider == "github":
            resp = await client.get("https://api.github.com/user")
            user_info = resp.json()
            # GitHub requires separate endpoint for email
            if not user_info.get("email"):
                email_resp = await client.get("https://api.github.com/user/emails")
                emails = email_resp.json()
                # Get primary verified email
                for email_data in emails:
                    if email_data.get("primary") and email_data.get("verified"):
                        user_info["email"] = email_data["email"]
                        break
        elif provider == "microsoft":
            resp = await client.get("https://graph.microsoft.com/v1.0/me")
            user_info = resp.json()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {provider}",
            )

        # Authenticate or register user
        service = OAuthService(db)
        user_agent, ip_address = get_client_info(request)
        auth_response = await service.authenticate_oauth_user(
            provider=provider,
            user_info=user_info,
            token=token,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        # Return auth response
        return auth_response

    except OAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth authentication failed: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}",
        )


@router.get(
    "/accounts",
    response_model=OAuthAccountsList,
    summary="List OAuth accounts",
    description="Get list of OAuth accounts linked to the authenticated user. Requires authentication.",
)
async def list_oauth_accounts(
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> OAuthAccountsList:
    """
    List OAuth accounts for authenticated user.

    Args:
        user_id: Authenticated user ID
        db: Database session

    Returns:
        List of OAuth accounts
    """
    service = OAuthService(db)
    accounts = await service.oauth_repo.get_by_user_id(user_id)

    return OAuthAccountsList(
        accounts=[
            OAuthAccountResponse(
                id=account.id,
                provider=account.provider,
                provider_user_id=account.provider_user_id,
                created=account.created.isoformat(),
            )
            for account in accounts
        ]
    )


@router.delete(
    "/accounts/{provider}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unlink OAuth account",
    description="Unlink an OAuth provider from the authenticated user. Requires authentication. "
    "Cannot unlink if it's the only authentication method.",
)
async def unlink_oauth_account(
    provider: str,
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Unlink OAuth account from user.

    Args:
        provider: OAuth provider to unlink
        user_id: Authenticated user ID
        db: Database session
    """
    if provider not in ["google", "github", "microsoft"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OAuth provider: {provider}",
        )

    service = OAuthService(db)
    await service.unlink_oauth_account(user_id, provider)
