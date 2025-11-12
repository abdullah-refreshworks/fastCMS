"""
End-to-end tests for core features.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch


class TestAdvancedFiltering:
    """Test advanced filtering and querying."""

    async def test_filter_with_comparison_operators(self, client: AsyncClient):
        """Test filtering with comparison operators."""
        # Register and login
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "filtertest@example.com",
                "password": "Test123!Pass",
                "password_confirm": "Test123!Pass",
            },
        )
        token = response.json()["token"]["access_token"]

        # Create collection
        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "users_test",
                "type": "base",
                "schema": [
                    {"name": "age", "type": "number", "validation": {}},
                    {"name": "status", "type": "text", "validation": {}},
                ],
            },
        )

        # Create test records
        for age, status in [(25, "active"), (30, "inactive"), (18, "active")]:
            await client.post(
                "/api/v1/users_test/records",
                headers={"Authorization": f"Bearer {token}"},
                json={"data": {"age": age, "status": status}},
            )

        # Test greater than filter
        response = await client.get(
            "/api/v1/users_test/records?filter=age>20",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) == 2

        # Test complex filter with AND
        response = await client.get(
            "/api/v1/users_test/records?filter=age>=18&&status=active",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) == 2

    async def test_sort_with_prefix(self, client: AsyncClient):
        """Test sorting with - prefix for descending."""
        # Register and login
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "sorttest@example.com",
                "password": "Test123!Pass",
                "password_confirm": "Test123!Pass",
            },
        )
        token = response.json()["token"]["access_token"]

        # Create collection
        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "products",
                "type": "base",
                "schema": [{"name": "price", "type": "number", "validation": {}}],
            },
        )

        # Create records
        for price in [10, 50, 25]:
            await client.post(
                "/api/v1/products/records",
                headers={"Authorization": f"Bearer {token}"},
                json={"data": {"price": price}},
            )

        # Test descending sort
        response = await client.get(
            "/api/v1/products/records?sort=-price",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        items = response.json()["items"]
        assert items[0]["data"]["price"] == 50
        assert items[1]["data"]["price"] == 25
        assert items[2]["data"]["price"] == 10


class TestRateLimiting:
    """Test rate limiting functionality."""

    async def test_rate_limit_enforcement(self, client: AsyncClient):
        """Test that rate limiting blocks excessive requests."""
        # Make rapid requests
        responses = []
        for _ in range(150):  # Exceed the per-minute limit
            response = await client.get("/health")
            responses.append(response.status_code)

        # Should get some 429 responses
        assert 429 in responses

    async def test_rate_limit_headers(self, client: AsyncClient):
        """Test that rate limit headers are present."""
        response = await client.get("/health")

        assert "X-RateLimit-Limit-Minute" in response.headers
        assert "X-RateLimit-Limit-Hour" in response.headers


class TestQueryParsing:
    """Test query parser functionality."""

    def test_parse_filter_single_condition(self):
        """Test parsing single filter condition."""
        from app.utils.query_parser import QueryParser

        filters = QueryParser.parse_filter("age>=18")
        assert len(filters) == 1
        assert filters[0].field == "age"
        assert filters[0].operator == "gte"
        assert filters[0].value == 18

    def test_parse_filter_multiple_conditions(self):
        """Test parsing multiple filter conditions."""
        from app.utils.query_parser import QueryParser

        filters = QueryParser.parse_filter("age>=18&&status=active")
        assert len(filters) == 2
        assert filters[0].field == "age"
        assert filters[1].field == "status"
        assert filters[1].value == "active"

    def test_parse_sort_ascending(self):
        """Test parsing ascending sort."""
        from app.utils.query_parser import QueryParser

        field, order = QueryParser.parse_sort("created")
        assert field == "created"
        assert order == "asc"

    def test_parse_sort_descending(self):
        """Test parsing descending sort."""
        from app.utils.query_parser import QueryParser

        field, order = QueryParser.parse_sort("-created")
        assert field == "created"
        assert order == "desc"


class TestEmailVerification:
    """Test email verification and password reset."""

    @patch("app.services.email_service.EmailService.send_verification_email")
    async def test_email_verification_flow(
        self, mock_send_email: AsyncMock, client: AsyncClient
    ):
        """Test complete email verification flow."""
        # Mock email sending
        mock_send_email.return_value = None

        # Register user
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "verify@example.com",
                "password": "Test123!Pass",
                "password_confirm": "Test123!Pass",
            },
        )
        assert response.status_code == 201
        user_data = response.json()
        assert user_data["user"]["verified"] is False

        # In real scenario, extract token from email
        # For test, we'll create a verification token directly
        from app.db.session import async_session_maker
        from app.db.models.verification import VerificationToken
        from datetime import datetime, timedelta, timezone

        token_value = "test_verification_token"
        async with async_session_maker() as db:
            from app.db.repositories.verification import VerificationTokenRepository

            repo = VerificationTokenRepository(db)
            token = VerificationToken(
                user_id=user_data["user"]["id"],
                token=token_value,
                expires_at=(datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                used=False,
            )
            await repo.create(token)
            await db.commit()

        # Verify email with token
        verify_response = await client.post(
            "/api/v1/auth/verify-email", json={"token": token_value}
        )
        assert verify_response.status_code == 204

    @patch("app.services.email_service.EmailService.send_password_reset_email")
    async def test_password_reset_flow(
        self, mock_send_email: AsyncMock, client: AsyncClient
    ):
        """Test complete password reset flow."""
        mock_send_email.return_value = None

        # Register user
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "reset@example.com",
                "password": "OldPass123!",
                "password_confirm": "OldPass123!",
            },
        )
        assert response.status_code == 201

        # Request password reset
        reset_request = await client.post(
            "/api/v1/auth/request-password-reset", json={"email": "reset@example.com"}
        )
        assert reset_request.status_code == 204

        # Get reset token from database
        from app.db.session import async_session_maker

        async with async_session_maker() as db:
            from app.db.repositories.verification import PasswordResetTokenRepository

            repo = PasswordResetTokenRepository(db)
            user_id = response.json()["user"]["id"]
            reset_token = await repo.get_by_user_id(user_id)
            assert reset_token is not None

            # Reset password
            reset_response = await client.post(
                "/api/v1/auth/reset-password",
                json={
                    "token": reset_token.token,
                    "password": "NewPass123!",
                    "password_confirm": "NewPass123!",
                },
            )
            assert reset_response.status_code == 204

        # Login with new password
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "reset@example.com", "password": "NewPass123!"},
        )
        assert login_response.status_code == 200


class TestRelationExpansion:
    """Test relation expansion functionality."""

    async def test_expand_single_relation(self, client: AsyncClient):
        """Test expanding a single relation field."""
        # Register and login
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "expand@example.com",
                "password": "Test123!Pass",
                "password_confirm": "Test123!Pass",
            },
        )
        token = response.json()["token"]["access_token"]

        # Create author collection
        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "authors",
                "type": "base",
                "schema": [{"name": "name", "type": "text", "validation": {}}],
            },
        )

        # Create author record
        author_response = await client.post(
            "/api/v1/authors/records",
            headers={"Authorization": f"Bearer {token}"},
            json={"data": {"name": "John Doe"}},
        )
        author_id = author_response.json()["id"]

        # Create posts collection with relation
        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "posts",
                "type": "base",
                "schema": [
                    {"name": "title", "type": "text", "validation": {}},
                    {
                        "name": "author",
                        "type": "relation",
                        "validation": {"collection_name": "authors"},
                    },
                ],
            },
        )

        # Create post with author relation
        post_response = await client.post(
            "/api/v1/posts/records",
            headers={"Authorization": f"Bearer {token}"},
            json={"data": {"title": "Test Post", "author": author_id}},
        )
        post_id = post_response.json()["id"]

        # Get post with expanded author
        expanded_response = await client.get(
            f"/api/v1/posts/records/{post_id}?expand=author",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert expanded_response.status_code == 200
        post_data = expanded_response.json()
        assert isinstance(post_data["data"]["author"], dict)
        assert post_data["data"]["author"]["data"]["name"] == "John Doe"


class TestWebhooks:
    """Test webhook functionality."""

    @patch("app.services.webhook_service.httpx.AsyncClient")
    async def test_webhook_delivery(
        self, mock_client_class: AsyncMock, client: AsyncClient
    ):
        """Test webhook is triggered on record creation."""
        # Mock HTTP POST for webhook delivery
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_post = AsyncMock(return_value=mock_response)
        mock_client_instance = AsyncMock()
        mock_client_instance.post = mock_post
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client_instance

        # Register and login
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "webhook@example.com",
                "password": "Test123!Pass",
                "password_confirm": "Test123!Pass",
            },
        )
        token = response.json()["token"]["access_token"]

        # Create collection
        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "items",
                "type": "base",
                "schema": [{"name": "name", "type": "text", "validation": {}}],
            },
        )

        # Create webhook
        webhook_response = await client.post(
            "/api/v1/webhooks",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "url": "https://example.com/webhook",
                "collection_name": "items",
                "events": ["record.created"],
                "secret": "test_secret",
            },
        )
        assert webhook_response.status_code == 201

        # Create record (should trigger webhook)
        await client.post(
            "/api/v1/items/records",
            headers={"Authorization": f"Bearer {token}"},
            json={"data": {"name": "Test Item"}},
        )

        # Give webhook time to fire (it's async)
        import asyncio
        await asyncio.sleep(0.5)

        # Verify webhook was called
        assert mock_post.called

    async def test_webhook_crud(self, client: AsyncClient):
        """Test webhook CRUD operations."""
        # Register and login
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "webhookcrud@example.com",
                "password": "Test123!Pass",
                "password_confirm": "Test123!Pass",
            },
        )
        token = response.json()["token"]["access_token"]

        # Create webhook
        create_response = await client.post(
            "/api/v1/webhooks",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "url": "https://example.com/hook",
                "collection_name": "test_collection",
                "events": ["record.created", "record.updated"],
            },
        )
        assert create_response.status_code == 201
        webhook_id = create_response.json()["id"]

        # Get webhook
        get_response = await client.get(
            f"/api/v1/webhooks/{webhook_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 200

        # Update webhook
        update_response = await client.patch(
            f"/api/v1/webhooks/{webhook_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"active": False},
        )
        assert update_response.status_code == 200
        assert update_response.json()["active"] is False

        # Delete webhook
        delete_response = await client.delete(
            f"/api/v1/webhooks/{webhook_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert delete_response.status_code == 204
