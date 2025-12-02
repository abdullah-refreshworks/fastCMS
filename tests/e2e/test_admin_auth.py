"""
E2E tests for admin authentication.
Tests: Admin user registration, login, and token refresh
"""

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
class TestAdminAuthentication:
    """Test admin user authentication."""

    async def test_admin_registration_and_login(self, client: AsyncClient):
        """Test admin user registration and login flow."""
        # Register admin user
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "admin@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
                "name": "Test Admin",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == "admin@testcms.dev"
        assert data["user"]["role"] == "user"  # Default role

        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@testcms.dev",
                "password": "SecurePass123!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data["token"]
        assert "refresh_token" in data["token"]

    async def test_admin_token_refresh(self, client: AsyncClient):
        """Test token refresh functionality."""
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "refresh@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )

        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "refresh@testcms.dev",
                "password": "SecurePass123!",
            },
        )
        refresh_token = login_response.json()["token"]["refresh_token"]

        # Refresh token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
