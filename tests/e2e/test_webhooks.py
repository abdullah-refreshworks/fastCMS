"""
E2E tests for webhooks functionality.
Tests: Webhook CRUD operations, event triggers, and security features.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
class TestWebhooks:
    """Test webhook management and event delivery."""

    async def test_create_webhook(self, client: AsyncClient):
        """Test creating a new webhook."""
        # Setup: Create admin user
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "webhook_admin@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        # Create a collection to use for webhooks
        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "webhook_posts",
                "type": "base",
                "schema": [{"name": "title", "type": "text", "validation": {"required": True}}],
            },
        )

        # Create webhook
        response = await client.post(
            "/api/v1/webhooks",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "url": "https://example.com/webhook",
                "collection_name": "webhook_posts",
                "events": ["create", "update", "delete"],
                "secret": "test_secret_123",
                "retry_count": 3,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["url"] == "https://example.com/webhook"
        assert data["collection_name"] == "webhook_posts"
        assert set(data["events"]) == {"create", "update", "delete"}
        assert data["active"] is True
        assert data["retry_count"] == 3
        assert "id" in data
        assert "created" in data

    async def test_list_webhooks(self, client: AsyncClient):
        """Test listing all webhooks."""
        # Setup: Create admin user
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "webhook_list@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        # Create collection
        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "list_posts",
                "type": "base",
                "schema": [{"name": "title", "type": "text", "validation": {}}],
            },
        )

        # Create multiple webhooks
        webhook_ids = []
        for i in range(3):
            response = await client.post(
                "/api/v1/webhooks",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "url": f"https://example.com/webhook{i}",
                    "collection_name": "list_posts",
                    "events": ["create"],
                    "retry_count": 3,
                },
            )
            webhook_ids.append(response.json()["id"])

        # List webhooks
        response = await client.get(
            "/api/v1/webhooks",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 3

    async def test_list_webhooks_by_collection(self, client: AsyncClient):
        """Test listing webhooks filtered by collection."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "webhook_filter@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        # Create two collections
        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "filter_posts",
                "type": "base",
                "schema": [{"name": "title", "type": "text", "validation": {}}],
            },
        )
        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "filter_pages",
                "type": "base",
                "schema": [{"name": "title", "type": "text", "validation": {}}],
            },
        )

        # Create webhooks for different collections
        await client.post(
            "/api/v1/webhooks",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "url": "https://example.com/posts",
                "collection_name": "filter_posts",
                "events": ["create"],
                "retry_count": 3,
            },
        )
        await client.post(
            "/api/v1/webhooks",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "url": "https://example.com/pages",
                "collection_name": "filter_pages",
                "events": ["create"],
                "retry_count": 3,
            },
        )

        # Filter by collection
        response = await client.get(
            "/api/v1/webhooks?collection_name=filter_posts",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert all(w["collection_name"] == "filter_posts" for w in data["items"])

    async def test_get_webhook(self, client: AsyncClient):
        """Test getting a specific webhook by ID."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "webhook_get@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "get_posts",
                "type": "base",
                "schema": [{"name": "title", "type": "text", "validation": {}}],
            },
        )

        # Create webhook
        create_response = await client.post(
            "/api/v1/webhooks",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "url": "https://example.com/webhook",
                "collection_name": "get_posts",
                "events": ["create"],
                "retry_count": 3,
            },
        )
        webhook_id = create_response.json()["id"]

        # Get webhook
        response = await client.get(
            f"/api/v1/webhooks/{webhook_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == webhook_id
        assert data["url"] == "https://example.com/webhook"

    async def test_update_webhook(self, client: AsyncClient):
        """Test updating a webhook."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "webhook_update@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "update_posts",
                "type": "base",
                "schema": [{"name": "title", "type": "text", "validation": {}}],
            },
        )

        # Create webhook
        create_response = await client.post(
            "/api/v1/webhooks",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "url": "https://example.com/webhook",
                "collection_name": "update_posts",
                "events": ["create"],
                "retry_count": 3,
            },
        )
        webhook_id = create_response.json()["id"]

        # Update webhook
        response = await client.patch(
            f"/api/v1/webhooks/{webhook_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "url": "https://example.com/new-webhook",
                "events": ["create", "update"],
                "active": False,
                "retry_count": 5,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["url"] == "https://example.com/new-webhook"
        assert set(data["events"]) == {"create", "update"}
        assert data["active"] is False
        assert data["retry_count"] == 5

    async def test_delete_webhook(self, client: AsyncClient):
        """Test deleting a webhook."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "webhook_delete@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "delete_posts",
                "type": "base",
                "schema": [{"name": "title", "type": "text", "validation": {}}],
            },
        )

        # Create webhook
        create_response = await client.post(
            "/api/v1/webhooks",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "url": "https://example.com/webhook",
                "collection_name": "delete_posts",
                "events": ["create"],
                "retry_count": 3,
            },
        )
        webhook_id = create_response.json()["id"]

        # Delete webhook
        response = await client.delete(
            f"/api/v1/webhooks/{webhook_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

        # Verify deletion
        response = await client.get(
            f"/api/v1/webhooks/{webhook_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def test_webhook_validation(self, client: AsyncClient):
        """Test webhook validation rules."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "webhook_validation@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "validation_posts",
                "type": "base",
                "schema": [{"name": "title", "type": "text", "validation": {}}],
            },
        )

        # Test invalid URL
        response = await client.post(
            "/api/v1/webhooks",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "url": "not-a-valid-url",
                "collection_name": "validation_posts",
                "events": ["create"],
                "retry_count": 3,
            },
        )
        assert response.status_code == 422

        # Test invalid events
        response = await client.post(
            "/api/v1/webhooks",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "url": "https://example.com/webhook",
                "collection_name": "validation_posts",
                "events": ["invalid_event"],
                "retry_count": 3,
            },
        )
        assert response.status_code == 422

        # Test invalid retry count (too high)
        response = await client.post(
            "/api/v1/webhooks",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "url": "https://example.com/webhook",
                "collection_name": "validation_posts",
                "events": ["create"],
                "retry_count": 10,
            },
        )
        assert response.status_code == 422

    async def test_webhook_requires_authentication(self, client: AsyncClient):
        """Test that webhook endpoints require authentication."""
        # Try to create webhook without token
        response = await client.post(
            "/api/v1/webhooks",
            json={
                "url": "https://example.com/webhook",
                "collection_name": "posts",
                "events": ["create"],
                "retry_count": 3,
            },
        )
        assert response.status_code == 401

        # Try to list webhooks without token
        response = await client.get("/api/v1/webhooks")
        assert response.status_code == 401
