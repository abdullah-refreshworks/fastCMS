"""
E2E tests for Full-Text Search functionality
"""
import pytest
import httpx
from tests.conftest import TestClient


@pytest.mark.asyncio
class TestFullTextSearch:
    """End-to-end tests for full-text search"""

    async def test_create_and_use_search_index(self, client: TestClient, admin_headers: dict):
        """Test complete search workflow"""
        # 1. Create a test collection
        collection_data = {
            "name": "articles",
            "schema": [
                {"name": "title", "type": "text", "required": True},
                {"name": "content", "type": "text", "required": True},
                {"name": "author", "type": "text", "required": False},
            ],
        }
        response = await client.post(
            "/api/v1/collections", json=collection_data, headers=admin_headers
        )
        assert response.status_code == 201

        # 2. Create search index on title and content fields
        search_index_data = {"collection_name": "articles", "fields": ["title", "content"]}
        response = await client.post(
            "/api/v1/search/indexes", json=search_index_data, headers=admin_headers
        )
        assert response.status_code == 200
        index_data = response.json()
        assert index_data["collection_name"] == "articles"
        assert "title" in index_data["indexed_fields"]
        assert "content" in index_data["indexed_fields"]

        # 3. Create test records
        articles = [
            {
                "title": "Introduction to Python",
                "content": "Python is a powerful programming language used for web development",
                "author": "John Doe",
            },
            {
                "title": "FastAPI Tutorial",
                "content": "FastAPI is a modern web framework for building APIs with Python",
                "author": "Jane Smith",
            },
            {
                "title": "JavaScript Basics",
                "content": "Learn the fundamentals of JavaScript programming",
                "author": "Bob Johnson",
            },
        ]

        for article in articles:
            response = await client.post(
                "/api/v1/articles/records", json=article, headers=admin_headers
            )
            assert response.status_code == 201

        # 4. Test search for "Python"
        response = await client.get("/api/v1/search/articles?q=Python", headers=admin_headers)
        assert response.status_code == 200
        results = response.json()
        assert results["count"] >= 2  # Should find "Introduction to Python" and "FastAPI Tutorial"
        assert "Python" in results["items"][0]["title"] or "Python" in results["items"][0]["content"]

        # 5. Test search for "FastAPI"
        response = await client.get("/api/v1/search/articles?q=FastAPI", headers=admin_headers)
        assert response.status_code == 200
        results = response.json()
        assert results["count"] >= 1
        assert "FastAPI" in results["items"][0]["title"]

        # 6. Test search for "JavaScript"
        response = await client.get("/api/v1/search/articles?q=JavaScript", headers=admin_headers)
        assert response.status_code == 200
        results = response.json()
        assert results["count"] >= 1

        # 7. Test search with limit
        response = await client.get(
            "/api/v1/search/articles?q=programming&limit=1", headers=admin_headers
        )
        assert response.status_code == 200
        results = response.json()
        assert len(results["items"]) <= 1

        # 8. Get search index info
        response = await client.get("/api/v1/search/indexes/articles", headers=admin_headers)
        assert response.status_code == 200
        index = response.json()
        assert index["collection_name"] == "articles"

        # 9. List all indexes
        response = await client.get("/api/v1/search/indexes", headers=admin_headers)
        assert response.status_code == 200
        indexes = response.json()
        assert any(idx["collection_name"] == "articles" for idx in indexes)

        # 10. Reindex collection
        response = await client.post(
            "/api/v1/search/indexes/articles/reindex", headers=admin_headers
        )
        assert response.status_code == 200
        reindex_result = response.json()
        assert reindex_result["records_indexed"] == 3

        # 11. Delete search index
        response = await client.delete("/api/v1/search/indexes/articles", headers=admin_headers)
        assert response.status_code == 200

        # 12. Verify index is deleted
        response = await client.get("/api/v1/search/articles?q=Python", headers=admin_headers)
        assert response.status_code == 400  # No search index

    async def test_search_without_index(self, client: TestClient, admin_headers: dict):
        """Test search on collection without index returns error"""
        # Create collection without search index
        collection_data = {
            "name": "no_index_collection",
            "schema": [{"name": "title", "type": "text", "required": True}],
        }
        response = await client.post(
            "/api/v1/collections", json=collection_data, headers=admin_headers
        )
        assert response.status_code == 201

        # Try to search without index
        response = await client.get(
            "/api/v1/search/no_index_collection?q=test", headers=admin_headers
        )
        assert response.status_code == 400
        assert "No search index found" in response.json()["detail"]

    async def test_search_permissions(self, client: TestClient, user_headers: dict, admin_headers: dict):
        """Test that only admins can create/delete indexes but anyone can search"""
        # Create collection as admin
        collection_data = {
            "name": "public_articles",
            "schema": [{"name": "title", "type": "text", "required": True}],
        }
        response = await client.post(
            "/api/v1/collections", json=collection_data, headers=admin_headers
        )
        assert response.status_code == 201

        # Try to create index as regular user (should fail)
        search_index_data = {"collection_name": "public_articles", "fields": ["title"]}
        response = await client.post(
            "/api/v1/search/indexes", json=search_index_data, headers=user_headers
        )
        assert response.status_code == 403

        # Create index as admin
        response = await client.post(
            "/api/v1/search/indexes", json=search_index_data, headers=admin_headers
        )
        assert response.status_code == 200

        # Create a record
        response = await client.post(
            "/api/v1/public_articles/records",
            json={"title": "Public article"},
            headers=admin_headers,
        )
        assert response.status_code == 201

        # Regular user should be able to search
        response = await client.get("/api/v1/search/public_articles?q=Public", headers=user_headers)
        assert response.status_code == 200

        # Try to delete index as regular user (should fail)
        response = await client.delete("/api/v1/search/indexes/public_articles", headers=user_headers)
        assert response.status_code == 403

        # Delete as admin should work
        response = await client.delete("/api/v1/search/indexes/public_articles", headers=admin_headers)
        assert response.status_code == 200

    async def test_search_with_special_characters(self, client: TestClient, admin_headers: dict):
        """Test search with special characters and phrases"""
        # Create collection
        collection_data = {
            "name": "special_search",
            "schema": [{"name": "content", "type": "text", "required": True}],
        }
        response = await client.post(
            "/api/v1/collections", json=collection_data, headers=admin_headers
        )
        assert response.status_code == 201

        # Create search index
        search_index_data = {"collection_name": "special_search", "fields": ["content"]}
        response = await client.post(
            "/api/v1/search/indexes", json=search_index_data, headers=admin_headers
        )
        assert response.status_code == 200

        # Create records with special content
        records = [
            {"content": "Hello world! This is a test."},
            {"content": "Python 3.11+ is amazing"},
            {"content": "FastAPI: Modern web framework"},
        ]

        for record in records:
            response = await client.post(
                "/api/v1/special_search/records", json=record, headers=admin_headers
            )
            assert response.status_code == 201

        # Test search with various queries
        response = await client.get("/api/v1/search/special_search?q=test", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["count"] >= 1

        response = await client.get("/api/v1/search/special_search?q=Python", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["count"] >= 1
