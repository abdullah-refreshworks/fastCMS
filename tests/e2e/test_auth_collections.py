"""
E2E tests for auth collections.
Tests: Creating auth collections, user registration and login in auth collections
"""

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
class TestAuthCollections:
    """Test auth collection functionality."""

    async def test_create_auth_collection(self, client: AsyncClient):
        """Test creating an auth collection."""
        # Register and login as admin
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "authcol@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        # Create auth collection
        response = await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "customers",
                "type": "auth",
                "schema": [
                    {"name": "phone", "type": "text", "validation": {}},
                ],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "customers"
        assert data["type"] == "auth"

    @pytest.mark.integration
    async def test_auth_collection_registration(self, client: AsyncClient):
        """Test user registration in auth collection."""
        # Create admin and auth collection first
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "admin2@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        admin_token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "vendors",
                "type": "auth",
                "schema": [],
            },
        )

        # Register as vendor
        response = await client.post(
            "/api/v1/collections/vendors/auth/register",
            json={
                "email": "vendor@example.com",
                "password": "VendorPass123!",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "vendor@example.com"

    @pytest.mark.integration
    async def test_auth_collection_login(self, client: AsyncClient):
        """Test user login in auth collection."""
        # Setup: Create admin, collection, and register user
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "admin3@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        admin_token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "members", "type": "auth", "schema": []},
        )

        await client.post(
            "/api/v1/collections/members/auth/register",
            json={
                "email": "member@example.com",
                "password": "MemberPass123!",
            },
        )

        # Login as member
        response = await client.post(
            "/api/v1/collections/members/auth/login",
            json={
                "email": "member@example.com",
                "password": "MemberPass123!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "member@example.com"
