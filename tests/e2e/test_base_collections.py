"""
E2E tests for base collections.
Tests: Creating and listing base collections
"""

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
class TestBaseCollections:
    """Test base collection CRUD operations."""

    async def test_create_base_collection(self, client: AsyncClient):
        """Test creating a base collection."""
        # Register and login
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "collections@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        # Create collection
        response = await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "products",
                "type": "base",
                "schema": [
                    {
                        "name": "title",
                        "type": "text",
                        "validation": {"required": True, "max_length": 200},
                    },
                    {
                        "name": "price",
                        "type": "number",
                        "validation": {"required": True, "min": 0},
                    },
                    {
                        "name": "published",
                        "type": "bool",
                        "validation": {},
                    },
                ],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "products"
        assert data["type"] == "base"
        assert len(data["schema"]) == 3

    async def test_list_collections(self, client: AsyncClient):
        """Test listing all collections."""
        # Register and login
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "listcol@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        # Create a collection first
        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "posts",
                "type": "base",
                "schema": [
                    {"name": "title", "type": "text", "validation": {}},
                ],
            },
        )

        # List collections
        response = await client.get(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        # API returns paginated response
        if isinstance(data, dict) and "items" in data:
            collections = data["items"]
        else:
            collections = data
        assert isinstance(collections, list)
        assert len(collections) >= 1
