"""
End-to-end tests for OAuth2 social authentication features.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


class TestOAuthAuthentication:
    """Test OAuth2 social authentication flows."""

    @pytest.mark.asyncio
    async def test_oauth_login_google_new_user(self, client: AsyncClient):
        """Test OAuth login with Google for a new user."""
        # Mock OAuth provider responses
        mock_token = {
            "access_token": "mock_access_token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "mock_refresh_token",
            "userinfo": {
                "sub": "google_user_123",
                "email": "test@example.com",
                "name": "Test User",
                "email_verified": True,
            },
        }

        # Mock Authlib client
        with patch("app.api.v1.oauth.oauth.create_client") as mock_oauth:
            mock_client = MagicMock()
            mock_client.authorize_redirect = AsyncMock(
                return_value=MagicMock(status_code=307)
            )
            mock_client.authorize_access_token = AsyncMock(return_value=mock_token)
            mock_oauth.return_value = mock_client

            # Test callback endpoint
            response = await client.get(
                "/api/v1/oauth/callback/google",
                follow_redirects=False,
            )

            assert response.status_code == 200
            data = response.json()

            # Verify user and tokens created
            assert "user" in data
            assert "token" in data
            assert data["user"]["email"] == "test@example.com"
            assert data["user"]["name"] == "Test User"
            assert data["user"]["verified"] is True
            assert "access_token" in data["token"]
            assert "refresh_token" in data["token"]

    @pytest.mark.asyncio
    async def test_oauth_login_github_new_user(self, client: AsyncClient):
        """Test OAuth login with GitHub for a new user."""
        mock_token = {
            "access_token": "mock_github_token",
            "token_type": "Bearer",
        }

        mock_user_info = {
            "id": 12345678,
            "login": "testuser",
            "name": "Test GitHub User",
            "email": None,  # GitHub doesn't always provide email in user endpoint
        }

        mock_emails = [
            {"email": "github@example.com", "primary": True, "verified": True}
        ]

        with patch("app.api.v1.oauth.oauth.create_client") as mock_oauth:
            mock_client = MagicMock()
            mock_client.authorize_access_token = AsyncMock(return_value=mock_token)

            # Mock GitHub user info endpoint
            mock_user_response = MagicMock()
            mock_user_response.json = MagicMock(return_value=mock_user_info)

            # Mock GitHub emails endpoint
            mock_emails_response = MagicMock()
            mock_emails_response.json = MagicMock(return_value=mock_emails)

            async def mock_get(url):
                if "user/emails" in url:
                    return mock_emails_response
                return mock_user_response

            mock_client.get = AsyncMock(side_effect=mock_get)
            mock_oauth.return_value = mock_client

            response = await client.get("/api/v1/oauth/callback/github")

            assert response.status_code == 200
            data = response.json()
            assert data["user"]["email"] == "github@example.com"
            assert data["user"]["verified"] is True

    @pytest.mark.asyncio
    async def test_oauth_login_microsoft_new_user(self, client: AsyncClient):
        """Test OAuth login with Microsoft for a new user."""
        mock_token = {
            "access_token": "mock_ms_token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        mock_user_info = {
            "id": "microsoft_user_456",
            "userPrincipalName": "msuser@example.com",
            "displayName": "MS Test User",
        }

        with patch("app.api.v1.oauth.oauth.create_client") as mock_oauth:
            mock_client = MagicMock()
            mock_client.authorize_access_token = AsyncMock(return_value=mock_token)

            mock_response = MagicMock()
            mock_response.json = MagicMock(return_value=mock_user_info)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_oauth.return_value = mock_client

            response = await client.get("/api/v1/oauth/callback/microsoft")

            assert response.status_code == 200
            data = response.json()
            assert data["user"]["email"] == "msuser@example.com"

    @pytest.mark.asyncio
    async def test_oauth_link_to_existing_user(self, client: AsyncClient):
        """Test OAuth linking to existing user with same email."""
        # First create a regular user
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "existing@example.com",
                "password": "Test123!Pass",
                "password_confirm": "Test123!Pass",
            },
        )
        assert register_response.status_code == 201

        # Now try OAuth login with same email
        mock_token = {
            "access_token": "mock_token",
            "userinfo": {
                "sub": "google_existing_123",
                "email": "existing@example.com",
                "name": "Existing User",
            },
        }

        with patch("app.api.v1.oauth.oauth.create_client") as mock_oauth:
            mock_client = MagicMock()
            mock_client.authorize_access_token = AsyncMock(return_value=mock_token)
            mock_oauth.return_value = mock_client

            response = await client.get("/api/v1/oauth/callback/google")

            assert response.status_code == 200
            data = response.json()
            # Should link to existing user
            assert data["user"]["email"] == "existing@example.com"

    @pytest.mark.asyncio
    async def test_oauth_login_existing_oauth_account(self, client: AsyncClient):
        """Test OAuth login for user who already logged in with OAuth before."""
        # First OAuth login
        mock_token = {
            "access_token": "first_token",
            "refresh_token": "first_refresh",
            "userinfo": {
                "sub": "google_repeat_123",
                "email": "repeat@example.com",
                "name": "Repeat User",
            },
        }

        with patch("app.api.v1.oauth.oauth.create_client") as mock_oauth:
            mock_client = MagicMock()
            mock_client.authorize_access_token = AsyncMock(return_value=mock_token)
            mock_oauth.return_value = mock_client

            first_response = await client.get("/api/v1/oauth/callback/google")
            assert first_response.status_code == 200
            first_data = first_response.json()
            user_id = first_data["user"]["id"]

            # Second OAuth login - should update tokens
            mock_token["access_token"] = "second_token"
            mock_token["refresh_token"] = "second_refresh"

            second_response = await client.get("/api/v1/oauth/callback/google")
            assert second_response.status_code == 200
            second_data = second_response.json()

            # Should be same user
            assert second_data["user"]["id"] == user_id
            assert second_data["user"]["email"] == "repeat@example.com"

    @pytest.mark.asyncio
    async def test_list_oauth_accounts(self, client: AsyncClient):
        """Test listing linked OAuth accounts."""
        # Register user
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "oauth_list@example.com",
                "password": "Test123!Pass",
                "password_confirm": "Test123!Pass",
            },
        )
        token = register_response.json()["token"]["access_token"]

        # Link Google account
        mock_token = {
            "access_token": "google_token",
            "userinfo": {
                "sub": "google_list_123",
                "email": "oauth_list@example.com",
                "name": "OAuth List User",
            },
        }

        with patch("app.api.v1.oauth.oauth.create_client") as mock_oauth:
            mock_client = MagicMock()
            mock_client.authorize_access_token = AsyncMock(return_value=mock_token)
            mock_oauth.return_value = mock_client

            await client.get("/api/v1/oauth/callback/google")

        # List OAuth accounts
        response = await client.get(
            "/api/v1/oauth/accounts",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "accounts" in data
        assert len(data["accounts"]) == 1
        assert data["accounts"][0]["provider"] == "google"
        assert data["accounts"][0]["provider_user_id"] == "google_list_123"

    @pytest.mark.asyncio
    async def test_unlink_oauth_account(self, client: AsyncClient):
        """Test unlinking an OAuth account."""
        # Register user with password
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "oauth_unlink@example.com",
                "password": "Test123!Pass",
                "password_confirm": "Test123!Pass",
            },
        )
        token = register_response.json()["token"]["access_token"]

        # Link Google account
        mock_token = {
            "access_token": "google_token",
            "userinfo": {
                "sub": "google_unlink_123",
                "email": "oauth_unlink@example.com",
                "name": "Unlink User",
            },
        }

        with patch("app.api.v1.oauth.oauth.create_client") as mock_oauth:
            mock_client = MagicMock()
            mock_client.authorize_access_token = AsyncMock(return_value=mock_token)
            mock_oauth.return_value = mock_client

            await client.get("/api/v1/oauth/callback/google")

        # Unlink OAuth account
        response = await client.delete(
            "/api/v1/oauth/accounts/google",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 204

        # Verify account is unlinked
        list_response = await client.get(
            "/api/v1/oauth/accounts",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert len(list_response.json()["accounts"]) == 0

    @pytest.mark.asyncio
    async def test_cannot_unlink_only_auth_method(self, client: AsyncClient):
        """Test that user cannot unlink OAuth if it's their only auth method."""
        # Create user via OAuth (no password)
        mock_token = {
            "access_token": "google_token",
            "userinfo": {
                "sub": "google_only_auth_123",
                "email": "only_oauth@example.com",
                "name": "Only OAuth User",
            },
        }

        with patch("app.api.v1.oauth.oauth.create_client") as mock_oauth:
            mock_client = MagicMock()
            mock_client.authorize_access_token = AsyncMock(return_value=mock_token)
            mock_oauth.return_value = mock_client

            oauth_response = await client.get("/api/v1/oauth/callback/google")

        token = oauth_response.json()["token"]["access_token"]

        # Try to unlink - should fail
        response = await client.delete(
            "/api/v1/oauth/accounts/google",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        assert "only authentication method" in response.json()["error"].lower()

    @pytest.mark.asyncio
    async def test_oauth_unsupported_provider(self, client: AsyncClient):
        """Test OAuth with unsupported provider."""
        response = await client.get("/api/v1/oauth/login/unsupported")

        assert response.status_code == 400
        assert "unsupported" in response.json()["error"].lower()

    @pytest.mark.asyncio
    async def test_oauth_provider_not_configured(self, client: AsyncClient):
        """Test OAuth when provider credentials not configured."""
        with patch("app.api.v1.oauth.oauth.create_client") as mock_oauth:
            mock_oauth.return_value = None

            response = await client.get("/api/v1/oauth/login/google")

            assert response.status_code == 500
            assert "not configured" in response.json()["error"].lower()

    @pytest.mark.asyncio
    async def test_oauth_missing_email(self, client: AsyncClient):
        """Test OAuth fails when provider doesn't provide email."""
        mock_token = {
            "access_token": "token",
            "userinfo": {
                "sub": "google_no_email",
                "name": "No Email User",
                # Missing email
            },
        }

        with patch("app.api.v1.oauth.oauth.create_client") as mock_oauth:
            mock_client = MagicMock()
            mock_client.authorize_access_token = AsyncMock(return_value=mock_token)
            mock_oauth.return_value = mock_client

            response = await client.get("/api/v1/oauth/callback/google")

            assert response.status_code == 400
            assert "email" in response.json()["error"].lower()

    @pytest.mark.asyncio
    async def test_multiple_oauth_providers_same_user(self, client: AsyncClient):
        """Test user can link multiple OAuth providers."""
        # Register user
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "multi_oauth@example.com",
                "password": "Test123!Pass",
                "password_confirm": "Test123!Pass",
            },
        )
        token = register_response.json()["token"]["access_token"]

        # Link Google
        with patch("app.api.v1.oauth.oauth.create_client") as mock_oauth:
            mock_client = MagicMock()
            mock_client.authorize_access_token = AsyncMock(
                return_value={
                    "access_token": "google_token",
                    "userinfo": {
                        "sub": "google_multi_123",
                        "email": "multi_oauth@example.com",
                        "name": "Multi OAuth",
                    },
                }
            )
            mock_oauth.return_value = mock_client
            await client.get("/api/v1/oauth/callback/google")

        # Link GitHub
        with patch("app.api.v1.oauth.oauth.create_client") as mock_oauth:
            mock_client = MagicMock()
            mock_client.authorize_access_token = AsyncMock(
                return_value={"access_token": "github_token"}
            )
            mock_user_response = MagicMock()
            mock_user_response.json = MagicMock(
                return_value={
                    "id": 87654321,
                    "login": "multiuser",
                    "email": "multi_oauth@example.com",
                }
            )
            mock_client.get = AsyncMock(return_value=mock_user_response)
            mock_oauth.return_value = mock_client
            await client.get("/api/v1/oauth/callback/github")

        # List accounts - should have both
        response = await client.get(
            "/api/v1/oauth/accounts",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        accounts = response.json()["accounts"]
        assert len(accounts) == 2
        providers = [acc["provider"] for acc in accounts]
        assert "google" in providers
        assert "github" in providers
