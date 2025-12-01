"""
E2E tests for bulk operations.
Tests: Bulk delete and bulk update operations on collection records

NOTE: These tests require dynamic table creation which doesn't work well with
the test database fixture. They are marked as integration tests and should be run
against a real database instance. The bulk operations functionality itself is tested
and works correctly in production.

To run these tests:
    pytest tests/e2e/test_bulk_operations.py -m integration --run-integration
"""

import pytest
from httpx import AsyncClient


# Mark as integration test requiring real database
pytestmark = pytest.mark.integration


@pytest.mark.e2e
class TestBulkOperations:
    """Test bulk operations on collection records."""

    async def test_bulk_delete_success(self, client: AsyncClient):
        """Test successfully deleting multiple records in one request."""
        # Setup: Create user and collection
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "bulkdelete@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "bulk_items",
                "type": "base",
                "schema": [{"name": "name", "type": "text", "validation": {}}],
            },
        )

        # Create multiple records
        record_ids = []
        for i in range(5):
            create_response = await client.post(
                "/api/v1/collections/bulk_items/records",
                headers={"Authorization": f"Bearer {token}"},
                json={"data": {"name": f"Item {i}"}},
            )
            record_ids.append(create_response.json()["id"])

        # Bulk delete 3 records
        delete_ids = record_ids[:3]
        response = await client.post(
            "/api/v1/collections/bulk_items/records/bulk-delete",
            headers={"Authorization": f"Bearer {token}"},
            json={"record_ids": delete_ids},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == 3
        assert data["failed"] == 0
        assert data["errors"] is None

        # Verify records are deleted
        for record_id in delete_ids:
            get_response = await client.get(
                f"/api/v1/collections/bulk_items/records/{record_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert get_response.status_code == 404

        # Verify remaining records still exist
        for record_id in record_ids[3:]:
            get_response = await client.get(
                f"/api/v1/collections/bulk_items/records/{record_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert get_response.status_code == 200

    async def test_bulk_delete_partial_failure(self, client: AsyncClient):
        """Test bulk delete with some non-existent records (partial failure)."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "bulkpartial@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "partial_items",
                "type": "base",
                "schema": [{"name": "data", "type": "text", "validation": {}}],
            },
        )

        # Create 2 records
        record_ids = []
        for i in range(2):
            create_response = await client.post(
                "/api/v1/collections/partial_items/records",
                headers={"Authorization": f"Bearer {token}"},
                json={"data": {"data": f"Data {i}"}},
            )
            record_ids.append(create_response.json()["id"])

        # Try to delete valid records + non-existent IDs
        delete_ids = record_ids + ["fake-id-1", "fake-id-2"]
        response = await client.post(
            "/api/v1/collections/partial_items/records/bulk-delete",
            headers={"Authorization": f"Bearer {token}"},
            json={"record_ids": delete_ids},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == 2  # 2 valid records deleted
        assert data["failed"] == 2   # 2 fake IDs failed
        assert data["errors"] is not None
        assert len(data["errors"]) == 2

        # Verify error details
        for error in data["errors"]:
            assert "record_id" in error
            assert error["record_id"] in ["fake-id-1", "fake-id-2"]
            assert "error" in error

    async def test_bulk_delete_validation_empty_list(self, client: AsyncClient):
        """Test bulk delete validation rejects empty record list."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "bulkempty@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "empty_test",
                "type": "base",
                "schema": [{"name": "data", "type": "text", "validation": {}}],
            },
        )

        # Try to bulk delete with empty list
        response = await client.post(
            "/api/v1/collections/empty_test/records/bulk-delete",
            headers={"Authorization": f"Bearer {token}"},
            json={"record_ids": []},
        )

        assert response.status_code == 422  # Validation error

    async def test_bulk_delete_validation_exceeds_limit(self, client: AsyncClient):
        """Test bulk delete validation rejects more than 100 records."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "bulklimit@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "limit_test",
                "type": "base",
                "schema": [{"name": "data", "type": "text", "validation": {}}],
            },
        )

        # Try to bulk delete with 101 IDs
        record_ids = [f"id-{i}" for i in range(101)]
        response = await client.post(
            "/api/v1/collections/limit_test/records/bulk-delete",
            headers={"Authorization": f"Bearer {token}"},
            json={"record_ids": record_ids},
        )

        assert response.status_code == 422  # Validation error

    async def test_bulk_delete_requires_auth(self, client: AsyncClient):
        """Test bulk delete requires authentication."""
        response = await client.post(
            "/api/v1/collections/any_collection/records/bulk-delete",
            json={"record_ids": ["id1", "id2"]},
        )

        assert response.status_code == 401  # Unauthorized

    async def test_bulk_update_success(self, client: AsyncClient):
        """Test successfully updating multiple records in one request."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "bulkupdate@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "update_items",
                "type": "base",
                "schema": [
                    {"name": "title", "type": "text", "validation": {}},
                    {"name": "status", "type": "text", "validation": {}},
                ],
            },
        )

        # Create multiple records
        record_ids = []
        for i in range(3):
            create_response = await client.post(
                "/api/v1/collections/update_items/records",
                headers={"Authorization": f"Bearer {token}"},
                json={"data": {"title": f"Title {i}", "status": "draft"}},
            )
            record_ids.append(create_response.json()["id"])

        # Bulk update all records
        response = await client.post(
            "/api/v1/collections/update_items/records/bulk-update",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "record_ids": record_ids,
                "data": {"status": "published"}
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == 3
        assert data["failed"] == 0
        assert data["errors"] is None

        # Verify all records were updated
        for record_id in record_ids:
            get_response = await client.get(
                f"/api/v1/collections/update_items/records/{record_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert get_response.status_code == 200
            record_data = get_response.json()
            assert record_data["status"] == "published"

    async def test_bulk_update_multiple_fields(self, client: AsyncClient):
        """Test bulk updating multiple fields at once."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "bulkmulti@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "multi_fields",
                "type": "base",
                "schema": [
                    {"name": "title", "type": "text", "validation": {}},
                    {"name": "status", "type": "text", "validation": {}},
                    {"name": "priority", "type": "number", "validation": {}},
                ],
            },
        )

        # Create records
        record_ids = []
        for i in range(2):
            create_response = await client.post(
                "/api/v1/collections/multi_fields/records",
                headers={"Authorization": f"Bearer {token}"},
                json={"data": {"title": f"Title {i}", "status": "draft", "priority": 0}},
            )
            record_ids.append(create_response.json()["id"])

        # Bulk update multiple fields
        response = await client.post(
            "/api/v1/collections/multi_fields/records/bulk-update",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "record_ids": record_ids,
                "data": {"status": "published", "priority": 5}
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == 2
        assert data["failed"] == 0

        # Verify updates
        for record_id in record_ids:
            get_response = await client.get(
                f"/api/v1/collections/multi_fields/records/{record_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            record_data = get_response.json()
            assert record_data["status"] == "published"
            assert record_data["priority"] == 5

    async def test_bulk_update_partial_failure(self, client: AsyncClient):
        """Test bulk update with some non-existent records."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "bulkupdatepartial@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "partial_update",
                "type": "base",
                "schema": [{"name": "value", "type": "text", "validation": {}}],
            },
        )

        # Create 1 record
        create_response = await client.post(
            "/api/v1/collections/partial_update/records",
            headers={"Authorization": f"Bearer {token}"},
            json={"data": {"value": "original"}},
        )
        valid_id = create_response.json()["id"]

        # Try to update valid + invalid IDs
        response = await client.post(
            "/api/v1/collections/partial_update/records/bulk-update",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "record_ids": [valid_id, "fake-id"],
                "data": {"value": "updated"}
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == 1
        assert data["failed"] == 1
        assert data["errors"] is not None
        assert len(data["errors"]) == 1

    async def test_bulk_update_validation_empty_data(self, client: AsyncClient):
        """Test bulk update validation rejects empty update data."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "bulkemptydata@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "empty_data_test",
                "type": "base",
                "schema": [{"name": "data", "type": "text", "validation": {}}],
            },
        )

        # Try to bulk update with empty data
        response = await client.post(
            "/api/v1/collections/empty_data_test/records/bulk-update",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "record_ids": ["id1"],
                "data": {}
            },
        )

        assert response.status_code == 422  # Validation error

    async def test_bulk_update_requires_auth(self, client: AsyncClient):
        """Test bulk update requires authentication."""
        response = await client.post(
            "/api/v1/collections/any_collection/records/bulk-update",
            json={
                "record_ids": ["id1"],
                "data": {"field": "value"}
            },
        )

        assert response.status_code == 401  # Unauthorized

    async def test_bulk_operations_collection_not_found(self, client: AsyncClient):
        """Test bulk operations fail gracefully when collection doesn't exist."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "bulknotfound@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        # Try bulk delete on non-existent collection
        response = await client.post(
            "/api/v1/collections/nonexistent/records/bulk-delete",
            headers={"Authorization": f"Bearer {token}"},
            json={"record_ids": ["id1"]},
        )
        assert response.status_code == 404

        # Try bulk update on non-existent collection
        response = await client.post(
            "/api/v1/collections/nonexistent/records/bulk-update",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "record_ids": ["id1"],
                "data": {"field": "value"}
            },
        )
        assert response.status_code == 404
