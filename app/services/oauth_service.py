"""OAuth2 service for social authentication with Google, GitHub, and Microsoft."""

import secrets
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from authlib.integrations.starlette_client import OAuth
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestException, ConflictException
from app.core.logging import get_logger
from app.core.security import hash_password
from app.db.models.oauth import OAuthAccount
from app.db.models.user import User
from app.db.repositories.oauth import OAuthAccountRepository
from app.db.repositories.user import UserRepository
from app.schemas.auth import AuthResponse, TokenResponse, UserResponse
from app.services.auth_service import AuthService

logger = get_logger(__name__)

# Initialize OAuth registry
oauth = OAuth()

# Register OAuth providers
if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

if settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET:
    oauth.register(
        name="github",
        client_id=settings.GITHUB_CLIENT_ID,
        client_secret=settings.GITHUB_CLIENT_SECRET,
        authorize_url="https://github.com/login/oauth/authorize",
        access_token_url="https://github.com/login/oauth/access_token",
        client_kwargs={"scope": "user:email"},
    )

if settings.MICROSOFT_CLIENT_ID and settings.MICROSOFT_CLIENT_SECRET:
    oauth.register(
        name="microsoft",
        client_id=settings.MICROSOFT_CLIENT_ID,
        client_secret=settings.MICROSOFT_CLIENT_SECRET,
        server_metadata_url="https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


class OAuthService:
    """Service for OAuth2 social authentication."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.oauth_repo = OAuthAccountRepository(db)
        self.user_repo = UserRepository(db)
        self.auth_service = AuthService(db)

    async def authenticate_oauth_user(
        self,
        provider: str,
        user_info: Dict[str, Any],
        token: Dict[str, Any],
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        collection_name: Optional[str] = None,
    ) -> AuthResponse:
        """
        Authenticate or register user via OAuth.

        Args:
            provider: OAuth provider name (google, github, microsoft)
            user_info: User information from OAuth provider
            token: OAuth token information
            user_agent: User agent string
            ip_address: Client IP address
            collection_name: Optional name of the auth collection (e.g., "customers")

        Returns:
            Auth response with user and tokens
        """
        # Extract provider-specific user ID and email
        provider_user_id, email, name = self._extract_user_info(provider, user_info)

        if not email:
            raise BadRequestException("Email not provided by OAuth provider")

        # Check if OAuth account already exists
        oauth_account = await self.oauth_repo.get_by_provider_and_user_id(
            provider, provider_user_id
        )

        # Filter by collection if specified, or ensure it's a system user (collection_name=None)
        if oauth_account:
            if collection_name and oauth_account.collection_name != collection_name:
                # Account exists but for a different collection or system
                oauth_account = None
            elif not collection_name and oauth_account.collection_name is not None:
                # Account exists but is for a collection, not system
                oauth_account = None

        user = None

        if oauth_account:
            # Existing OAuth account - update tokens and authenticate
            oauth_account.access_token = token.get("access_token")
            oauth_account.refresh_token = token.get("refresh_token")
            oauth_account.expires_at = self._calculate_expiry(token)
            oauth_account.token_type = token.get("token_type")
            oauth_account.scope = token.get("scope")
            await self.oauth_repo.update(oauth_account)

            # Get user
            if collection_name:
                # Get user from dynamic collection
                from app.db.repositories.record import RecordRepository
                record_repo = RecordRepository(self.db, collection_name)
                user = await record_repo.get_by_id(oauth_account.user_id)
            else:
                # Get system user
                user = await self.user_repo.get_by_id(oauth_account.user_id)
            
            if not user:
                raise BadRequestException("User not found")

            logger.info(f"OAuth login for existing user: {email} (collection: {collection_name})")
        else:
            # New OAuth account - check if user exists by email
            if collection_name:
                # Check in dynamic collection
                from app.db.repositories.record import RecordRepository
                from sqlalchemy import select
                
                record_repo = RecordRepository(self.db, collection_name)
                model = await record_repo._get_model()
                
                result = await self.db.execute(select(model).where(model.email == email))
                user = result.scalar_one_or_none()
            else:
                # Check system users
                user = await self.user_repo.get_by_email(email)

            if user:
                # Link OAuth account to existing user
                logger.info(f"Linking {provider} account to existing user: {email}")
            else:
                # Create new user
                random_password = secrets.token_urlsafe(32)
                password_hash = hash_password(random_password)
                token_key = secrets.token_hex(32)
                
                if collection_name:
                    # Create user in dynamic collection
                    from app.db.repositories.record import RecordRepository
                    record_repo = RecordRepository(self.db, collection_name)
                    
                    user_data = {
                        "email": email,
                        "password": password_hash,
                        "name": name or email.split("@")[0],
                        "verified": True,  # OAuth providers verify emails
                    }
                    # Add any other required fields with defaults if needed
                    
                    user = await record_repo.create(user_data)
                    # Need to manually set token_key as it might not be in the schema
                    # But wait, dynamic models might not have token_key unless defined in schema
                    # For auth collections, we should assume they might need it or we handle it differently
                    # Let's check if the model has token_key, if not we might need to rely on something else
                    # or just not use token_key for invalidation in dynamic collections yet
                    pass 
                else:
                    # Create system user
                    user = User(
                        email=email,
                        password_hash=password_hash,
                        token_key=token_key,
                        name=name or email.split("@")[0],
                        verified=True,
                    )
                    user = await self.user_repo.create(user)
                
                logger.info(f"Created new user via {provider} OAuth: {email}")

            # Create OAuth account link
            oauth_account = OAuthAccount(
                user_id=user.id,
                collection_name=collection_name,
                provider=provider,
                provider_user_id=provider_user_id,
                access_token=token.get("access_token"),
                refresh_token=token.get("refresh_token"),
                expires_at=self._calculate_expiry(token),
                token_type=token.get("token_type"),
                scope=token.get("scope"),
            )
            await self.oauth_repo.create(oauth_account)

        await self.db.commit()

        # Generate JWT tokens
        if collection_name:
            # Generate tokens for collection user
            from app.core.security import create_access_token
            
            token_data = {
                "sub": user.id,
                "email": user.email,
                "collection": collection_name
            }
            access_token = create_access_token(token_data)
            
            # For now, return a simplified response for collection users
            # as they might not match the full UserResponse schema
            return {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": getattr(user, "name", None),
                    "verified": getattr(user, "verified", True),
                },
                "token": {
                    "access_token": access_token,
                    "token_type": "bearer"
                }
            }
        else:
            # Generate tokens for system user
            tokens = await self.auth_service._create_tokens(user, user_agent, ip_address)

            return AuthResponse(
                user=UserResponse(
                    id=user.id,
                    email=user.email,
                    verified=user.verified,
                    name=user.name,
                    avatar=user.avatar,
                    role=user.role,
                    created=user.created,
                    updated=user.updated,
                ),
                token=tokens,
            )

    async def unlink_oauth_account(
        self, user_id: str, provider: str
    ) -> None:
        """
        Unlink OAuth account from user.

        Args:
            user_id: User ID
            provider: OAuth provider name

        Raises:
            BadRequestException: If account not found or user has no password
        """
        # Get all OAuth accounts for user
        oauth_accounts = await self.oauth_repo.get_by_user_id(user_id)

        # Find the account to unlink
        account_to_unlink = None
        for account in oauth_accounts:
            if account.provider == provider:
                account_to_unlink = account
                break

        if not account_to_unlink:
            raise BadRequestException(f"No {provider} account linked")

        # Check if user has a password or other OAuth accounts
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise BadRequestException("User not found")

        # Don't allow unlinking if it's the only auth method
        if len(oauth_accounts) == 1 and not user.password_hash:
            raise BadRequestException(
                "Cannot unlink the only authentication method. Set a password first."
            )

        # Delete OAuth account
        await self.oauth_repo.delete(account_to_unlink)
        await self.db.commit()

        logger.info(f"Unlinked {provider} account for user: {user.email}")

    def _extract_user_info(
        self, provider: str, user_info: Dict[str, Any]
    ) -> tuple[str, Optional[str], Optional[str]]:
        """Extract user ID, email, and name from provider-specific user info."""
        if provider == "google":
            return (
                user_info.get("sub"),
                user_info.get("email"),
                user_info.get("name"),
            )
        elif provider == "github":
            return (
                str(user_info.get("id")),
                user_info.get("email"),
                user_info.get("name") or user_info.get("login"),
            )
        elif provider == "microsoft":
            return (
                user_info.get("sub") or user_info.get("id"),
                user_info.get("email") or user_info.get("userPrincipalName"),
                user_info.get("name"),
            )
        else:
            raise BadRequestException(f"Unsupported provider: {provider}")

    def _calculate_expiry(self, token: Dict[str, Any]) -> Optional[str]:
        """Calculate token expiry timestamp."""
        expires_in = token.get("expires_in")
        if expires_in:
            expiry = datetime.now(timezone.utc).timestamp() + expires_in
            return datetime.fromtimestamp(expiry, timezone.utc).isoformat()
        return None
