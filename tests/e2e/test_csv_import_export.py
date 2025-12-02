"""
E2E tests for CSV Import/Export functionality.
Tests: CSV export, CSV import, validation, error handling

NOTE: These tests require dynamic table creation which doesn't work well with
the test database fixture. They are marked as integration tests and should be run
against a real database instance. The CSV functionality itself is tested separately
in unit tests.

To run these tests:
    pytest tests/e2e/test_csv_import_export.py -m integration --run-integration
"""

import pytest
from httpx import AsyncClient
import io

# Mark as integration test requiring real database
pytestmark = pytest.mark.integration


@pytest.mark.e2e
class TestCSVExport:
    """Test CSV export functionality."""

    async def test_export_empty_collection(self, client: AsyncClient):
        """Test exporting an empty collection returns CSV with headers only."""
        # Register and login
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "csv_export@test.com",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        # Create a collection
        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "empty_products",
                "type": "base",
                "schema": [
                    {"name": "name", "type": "text", "validation": {}},
                    {"name": "price", "type": "number", "validation": {}},
                ],
            },
        )

        # Export empty collection
        response = await client.get(
            "/api/v1/collections/empty_products/records/export/csv",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"

        # Check CSV has headers
        csv_content = response.text
        assert "id,created,updated,name,price" in csv_content

    async def test_export_collection_with_records(self, client: AsyncClient):
        """Test exporting a collection with records."""
        # Register and login
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "csv_export2@test.com",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        # Create a collection
        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "test_products",
                "type": "base",
                "schema": [
                    {"name": "name", "type": "text", "validation": {"required": True}},
                    {"name": "price", "type": "number", "validation": {"required": True}},
                    {"name": "active", "type": "bool", "validation": {}},
                ],
            },
        )

        # Create some records
        await client.post(
            "/api/v1/collections/test_products/records",
            headers={"Authorization": f"Bearer {token}"},
            json={"data": {"name": "Product 1", "price": 10.99, "active": True}},
        )
        await client.post(
            "/api/v1/collections/test_products/records",
            headers={"Authorization": f"Bearer {token}"},
            json={"data": {"name": "Product 2", "price": 20.50, "active": False}},
        )

        # Export collection
        response = await client.get(
            "/api/v1/collections/test_products/records/export/csv",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        # Check CSV content
        csv_content = response.text
        assert "Product 1" in csv_content
        assert "Product 2" in csv_content
        assert "10.99" in csv_content
        assert "20.50" in csv_content or "20.5" in csv_content  # Float formatting


@pytest.mark.e2e
class TestCSVImport:
    """Test CSV import functionality."""

    async def test_import_csv_basic(self, client: AsyncClient):
        """Test basic CSV import."""
        # Register and login
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "csv_import@test.com",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        # Create a collection
        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "import_test",
                "type": "base",
                "schema": [
                    {"name": "name", "type": "text", "validation": {}},
                    {"name": "quantity", "type": "number", "validation": {}},
                ],
            },
        )

        # Create CSV content
        csv_content = """name,quantity
Item 1,100
Item 2,200
Item 3,300"""

        # Import CSV
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = await client.post(
            "/api/v1/collections/import_test/records/import/csv",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["imported"] == 3
        assert data["total"] == 3
        assert data["errors"] is None

        # Verify records were created
        list_response = await client.get(
            "/api/v1/collections/import_test/records",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_response.status_code == 200
        records = list_response.json()
        assert records["total"] == 3

    async def test_import_csv_with_types(self, client: AsyncClient):
        """Test CSV import with different field types."""
        # Register and login
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "csv_types@test.com",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        # Create collection with various types
        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "typed_data",
                "type": "base",
                "schema": [
                    {"name": "name", "type": "text", "validation": {}},
                    {"name": "count", "type": "number", "validation": {}},
                    {"name": "enabled", "type": "bool", "validation": {}},
                ],
            },
        )

        # Create CSV with different types
        csv_content = """name,count,enabled
Test 1,42,true
Test 2,99,false
Test 3,0,yes"""

        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = await client.post(
            "/api/v1/collections/typed_data/records/import/csv",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["imported"] >= 2  # At least 2 should import successfully

    async def test_import_invalid_file_type(self, client: AsyncClient):
        """Test importing non-CSV file is rejected."""
        # Register and login
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "csv_invalid@test.com",
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
                "name": "invalid_import",
                "type": "base",
                "schema": [{"name": "data", "type": "text", "validation": {}}],
            },
        )

        # Try to import non-CSV file
        content = "Not a CSV"
        files = {"file": ("test.txt", io.BytesIO(content.encode()), "text/plain")}
        response = await client.post(
            "/api/v1/collections/invalid_import/records/import/csv",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
        )
        assert response.status_code == 422

    async def test_import_empty_csv(self, client: AsyncClient):
        """Test importing empty CSV file."""
        # Register and login
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "csv_empty@test.com",
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
                "name": "empty_import",
                "type": "base",
                "schema": [{"name": "data", "type": "text", "validation": {}}],
            },
        )

        # Import empty CSV
        csv_content = ""
        files = {"file": ("empty.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = await client.post(
            "/api/v1/collections/empty_import/records/import/csv",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
        )
        # Should fail with validation error
        assert response.status_code in [400, 422]


@pytest.mark.e2e
class TestCSVRoundTrip:
    """Test export then import (round trip)."""

    async def test_export_import_roundtrip(self, client: AsyncClient):
        """Test exporting data and reimporting it."""
        # Register and login
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "roundtrip@test.com",
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
                "name": "roundtrip_test",
                "type": "base",
                "schema": [
                    {"name": "title", "type": "text", "validation": {}},
                    {"name": "value", "type": "number", "validation": {}},
                ],
            },
        )

        # Create records
        original_records = [
            {"title": "First", "value": 100},
            {"title": "Second", "value": 200},
        ]
        for record in original_records:
            await client.post(
                "/api/v1/collections/roundtrip_test/records",
                headers={"Authorization": f"Bearer {token}"},
                json={"data": record},
            )

        # Export
        export_response = await client.get(
            "/api/v1/collections/roundtrip_test/records/export/csv",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert export_response.status_code == 200
        csv_data = export_response.text

        # Delete original records would require knowing their IDs
        # For now, import into a new collection
        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "roundtrip_test2",
                "type": "base",
                "schema": [
                    {"name": "title", "type": "text", "validation": {}},
                    {"name": "value", "type": "number", "validation": {}},
                ],
            },
        )

        # Import into new collection
        files = {"file": ("export.csv", io.BytesIO(csv_data.encode()), "text/csv")}
        import_response = await client.post(
            "/api/v1/collections/roundtrip_test2/records/import/csv",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
        )
        assert import_response.status_code == 201
        import_data = import_response.json()
        assert import_data["imported"] == 2
