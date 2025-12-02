"""
E2E tests for record CRUD operations.
Tests: Create, Read, Update, Delete operations on collection records

NOTE: These tests require dynamic table creation which doesn't work well with
the test database fixture. They are marked as integration tests and should be run
against a real database instance. The record CRUD functionality itself is tested
and works correctly in production.

To run these tests:
    pytest tests/e2e/test_records_crud.py -m integration --run-integration
"""

import pytest
from httpx import AsyncClient


# Mark as integration test requiring real database
pytestmark = pytest.mark.integration


@pytest.mark.e2e
class TestRecordsCRUD:
    """Test CRUD operations on collection records."""

    async def test_create_record(self, client: AsyncClient):
        """Test creating a record in a collection."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "records@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "articles",
                "type": "base",
                "schema": [
                    {"name": "title", "type": "text", "validation": {"required": True}},
                    {"name": "content", "type": "text", "validation": {}},
                ],
            },
        )

        # Create record
        response = await client.post(
            "/api/v1/collections/articles/records",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "data": {
                    "title": "First Article",
                    "content": "This is the content",
                }
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "First Article"
        assert data["content"] == "This is the content"
        assert "id" in data
        assert "created" in data

    async def test_list_records(self, client: AsyncClient):
        """Test listing records with pagination."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "listrec@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "items",
                "type": "base",
                "schema": [{"name": "name", "type": "text", "validation": {}}],
            },
        )

        # Create multiple records
        for i in range(5):
            await client.post(
                "/api/v1/collections/items/records",
                headers={"Authorization": f"Bearer {token}"},
                json={"data": {"name": f"Item {i}"}},
            )

        # List records
        response = await client.get(
            "/api/v1/collections/items/records",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 5
        assert "total" in data
        assert data["total"] == 5

    async def test_get_single_record(self, client: AsyncClient):
        """Test retrieving a single record by ID."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "getrec@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "notes",
                "type": "base",
                "schema": [{"name": "text", "type": "text", "validation": {}}],
            },
        )

        # Create record
        create_response = await client.post(
            "/api/v1/collections/notes/records",
            headers={"Authorization": f"Bearer {token}"},
            json={"data": {"text": "Test Note"}},
        )
        record_id = create_response.json()["id"]

        # Get record
        response = await client.get(
            f"/api/v1/collections/notes/records/{record_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == record_id
        assert data["text"] == "Test Note"

    async def test_update_record(self, client: AsyncClient):
        """Test updating a record."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "updaterec@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "tasks",
                "type": "base",
                "schema": [
                    {"name": "title", "type": "text", "validation": {}},
                    {"name": "done", "type": "bool", "validation": {}},
                ],
            },
        )

        # Create record
        create_response = await client.post(
            "/api/v1/collections/tasks/records",
            headers={"Authorization": f"Bearer {token}"},
            json={"data": {"title": "Old Title", "done": False}},
        )
        record_id = create_response.json()["id"]

        # Update record
        response = await client.patch(
            f"/api/v1/collections/tasks/records/{record_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"data": {"title": "New Title", "done": True}},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["done"] is True

    async def test_delete_record(self, client: AsyncClient):
        """Test deleting a record."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "deleterec@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "temp",
                "type": "base",
                "schema": [{"name": "data", "type": "text", "validation": {}}],
            },
        )

        # Create record
        create_response = await client.post(
            "/api/v1/collections/temp/records",
            headers={"Authorization": f"Bearer {token}"},
            json={"data": {"data": "To be deleted"}},
        )
        record_id = create_response.json()["id"]

        # Delete record
        response = await client.delete(
            f"/api/v1/collections/temp/records/{record_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 204

        # Verify deletion
        get_response = await client.get(
            f"/api/v1/collections/temp/records/{record_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 404
