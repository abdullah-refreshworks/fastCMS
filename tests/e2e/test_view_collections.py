"""
E2E tests for view collections.
Tests: Creating view collections with SQL queries
"""

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
class TestViewCollections:
    """Test view collection functionality."""

    async def test_create_view_collection(self, client: AsyncClient):
        """Test creating a view collection."""
        # Register and login
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "viewcol@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        # Create base collection first
        base_response = await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "orders",
                "type": "base",
                "schema": [
                    {"name": "amount", "type": "number", "validation": {}},
                ],
            },
        )
        collection_id = base_response.json()["id"]

        # Create view collection
        response = await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "order_stats",
                "type": "view",
                "schema": [],
                "options": {
                    "query": {
                        "source": collection_id,
                        "sql": "SELECT COUNT(*) as total, SUM(amount) as sum FROM orders",
                    }
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "order_stats"
        assert data["type"] == "view"
