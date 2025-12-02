"""
E2E tests for access control.
Tests: Authentication requirements for protected endpoints
"""

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
class TestAccessControl:
    """Test access control rules."""

    async def test_unauthenticated_access_denied(self, client: AsyncClient):
        """Test that unauthenticated users cannot access protected endpoints."""
        response = await client.get("/api/v1/collections")
        assert response.status_code == 401

    async def test_authentication_required_for_collections(self, client: AsyncClient):
        """Test that authentication is required for collection operations."""
        response = await client.post(
            "/api/v1/collections",
            json={
                "name": "test",
                "type": "base",
                "schema": [],
            },
        )
        assert response.status_code == 401
