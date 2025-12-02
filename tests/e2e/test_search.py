"""
E2E tests for full-text search functionality.
Tests: Search across text fields, combined with filters, and edge cases

NOTE: These tests require dynamic table creation which doesn't work well with
the test database fixture. They are marked as integration tests and should be run
against a real database instance.

To run these tests:
    pytest tests/e2e/test_search.py -m integration --run-integration
"""

import pytest
from httpx import AsyncClient


# Mark as integration test requiring real database
pytestmark = pytest.mark.integration


@pytest.mark.e2e
class TestFullTextSearch:
    """Test full-text search functionality across collections."""

    async def test_basic_search(self, client: AsyncClient):
        """Test basic search across text fields."""
        # Setup: Create user and collection
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "search@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "search_posts",
                "type": "base",
                "schema": [
                    {"name": "title", "type": "text", "validation": {}},
                    {"name": "content", "type": "editor", "validation": {}},
                ],
            },
        )

        # Create test records
        await client.post(
            "/api/v1/collections/search_posts/records",
            headers={"Authorization": f"Bearer {token}"},
            json={"data": {"title": "FastCMS Introduction", "content": "Learn about FastCMS"}},
        )
        await client.post(
            "/api/v1/collections/search_posts/records",
            headers={"Authorization": f"Bearer {token}"},
            json={"data": {"title": "Getting Started", "content": "Install FastCMS quickly"}},
        )
        await client.post(
            "/api/v1/collections/search_posts/records",
            headers={"Authorization": f"Bearer {token}"},
            json={"data": {"title": "Advanced Topics", "content": "Deep dive into features"}},
        )

        # Search for "FastCMS"
        response = await client.get(
            "/api/v1/collections/search_posts/records?search=FastCMS",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2  # Should find 2 records containing "FastCMS"
        assert len(data["items"]) == 2

    async def test_search_across_multiple_fields(self, client: AsyncClient):
        """Test that search works across title and content fields."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "multifield@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "multi_search",
                "type": "base",
                "schema": [
                    {"name": "title", "type": "text", "validation": {}},
                    {"name": "description", "type": "text", "validation": {}},
                    {"name": "price", "type": "number", "validation": {}},
                ],
            },
        )

        # Create records with search term in different fields
        await client.post(
            "/api/v1/collections/multi_search/records",
            headers={"Authorization": f"Bearer {token}"},
            json={"data": {"title": "Python tutorial", "description": "Learn basics", "price": 10}},
        )
        await client.post(
            "/api/v1/collections/multi_search/records",
            headers={"Authorization": f"Bearer {token}"},
            json={"data": {"title": "Advanced course", "description": "Python mastery", "price": 50}},
        )
        await client.post(
            "/api/v1/collections/multi_search/records",
            headers={"Authorization": f"Bearer {token}"},
            json={"data": {"title": "JavaScript guide", "description": "Web development", "price": 30}},
        )

        # Search for "Python" - should find it in both title and description
        response = await client.get(
            "/api/v1/collections/multi_search/records?search=Python",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    async def test_search_with_filter(self, client: AsyncClient):
        """Test combining search with filters."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "searchfilter@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "filtered_search",
                "type": "base",
                "schema": [
                    {"name": "title", "type": "text", "validation": {}},
                    {"name": "status", "type": "text", "validation": {}},
                ],
            },
        )

        # Create records
        await client.post(
            "/api/v1/collections/filtered_search/records",
            headers={"Authorization": f"Bearer {token}"},
            json={"data": {"title": "Tutorial draft", "status": "draft"}},
        )
        await client.post(
            "/api/v1/collections/filtered_search/records",
            headers={"Authorization": f"Bearer {token}"},
            json={"data": {"title": "Tutorial published", "status": "published"}},
        )
        await client.post(
            "/api/v1/collections/filtered_search/records",
            headers={"Authorization": f"Bearer {token}"},
            json={"data": {"title": "Guide published", "status": "published"}},
        )

        # Search for "Tutorial" AND status=published
        response = await client.get(
            "/api/v1/collections/filtered_search/records?search=Tutorial&filter=status=published",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1  # Only one published tutorial
        assert data["items"][0]["data"]["title"] == "Tutorial published"

    async def test_search_case_insensitive(self, client: AsyncClient):
        """Test that search is case-insensitive."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "casetest@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "case_search",
                "type": "base",
                "schema": [{"name": "title", "type": "text", "validation": {}}],
            },
        )

        await client.post(
            "/api/v1/collections/case_search/records",
            headers={"Authorization": f"Bearer {token}"},
            json={"data": {"title": "FASTCMS Tutorial"}},
        )

        # Search with lowercase should still find it
        response = await client.get(
            "/api/v1/collections/case_search/records?search=fastcms",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    async def test_search_no_results(self, client: AsyncClient):
        """Test search with no matching results."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "noresults@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "empty_search",
                "type": "base",
                "schema": [{"name": "title", "type": "text", "validation": {}}],
            },
        )

        await client.post(
            "/api/v1/collections/empty_search/records",
            headers={"Authorization": f"Bearer {token}"},
            json={"data": {"title": "Test Record"}},
        )

        # Search for non-existent term
        response = await client.get(
            "/api/v1/collections/empty_search/records?search=nonexistent",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    async def test_search_partial_match(self, client: AsyncClient):
        """Test that search matches partial strings."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "partial@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "partial_search",
                "type": "base",
                "schema": [{"name": "title", "type": "text", "validation": {}}],
            },
        )

        await client.post(
            "/api/v1/collections/partial_search/records",
            headers={"Authorization": f"Bearer {token}"},
            json={"data": {"title": "Understanding FastCMS"}},
        )

        # Search for partial match "Fast" should find "FastCMS"
        response = await client.get(
            "/api/v1/collections/partial_search/records?search=Fast",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    async def test_search_with_pagination(self, client: AsyncClient):
        """Test search with pagination."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "paginated@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "paginated_search",
                "type": "base",
                "schema": [{"name": "title", "type": "text", "validation": {}}],
            },
        )

        # Create 5 records
        for i in range(5):
            await client.post(
                "/api/v1/collections/paginated_search/records",
                headers={"Authorization": f"Bearer {token}"},
                json={"data": {"title": f"Tutorial {i}"}},
            )

        # Search with per_page=2
        response = await client.get(
            "/api/v1/collections/paginated_search/records?search=Tutorial&per_page=2&page=1",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["total_pages"] == 3

    async def test_search_requires_auth(self, client: AsyncClient):
        """Test that search requires authentication."""
        response = await client.get(
            "/api/v1/collections/any_collection/records?search=test"
        )

        assert response.status_code == 401

    async def test_search_empty_query(self, client: AsyncClient):
        """Test search with empty query returns all records."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "emptyquery@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "empty_query",
                "type": "base",
                "schema": [{"name": "title", "type": "text", "validation": {}}],
            },
        )

        await client.post(
            "/api/v1/collections/empty_query/records",
            headers={"Authorization": f"Bearer {token}"},
            json={"data": {"title": "Record 1"}},
        )
        await client.post(
            "/api/v1/collections/empty_query/records",
            headers={"Authorization": f"Bearer {token}"},
            json={"data": {"title": "Record 2"}},
        )

        # Empty search should return all records
        response = await client.get(
            "/api/v1/collections/empty_query/records?search=",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
