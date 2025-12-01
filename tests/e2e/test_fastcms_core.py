"""
Comprehensive E2E tests for FastCMS core functionality.
Tests: Auth, Base Collections, Auth Collections, View Collections, Records CRUD, Access Control
"""

import pytest
from httpx import AsyncClient


class TestAdminAuthentication:
    """Test admin user authentication."""

    async def test_admin_registration_and_login(self, client: AsyncClient):
        """Test admin user registration and login flow."""
        # Register admin user
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "admin@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
                "name": "Test Admin",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == "admin@testcms.dev"
        assert data["user"]["role"] == "user"  # Default role

        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@testcms.dev",
                "password": "SecurePass123!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data["token"]
        assert "refresh_token" in data["token"]

    async def test_admin_token_refresh(self, client: AsyncClient):
        """Test token refresh functionality."""
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "refresh@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )

        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "refresh@testcms.dev",
                "password": "SecurePass123!",
            },
        )
        refresh_token = login_response.json()["token"]["refresh_token"]

        # Refresh token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()["token"]


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
        collections = response.json()
        assert isinstance(collections, list)
        assert len(collections) >= 1


class TestAuthCollections:
    """Test auth collection functionality."""

    async def test_create_auth_collection(self, client: AsyncClient):
        """Test creating an auth collection."""
        # Register and login as admin
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "authcol@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        # Create auth collection
        response = await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "customers",
                "type": "auth",
                "schema": [
                    {"name": "phone", "type": "text", "validation": {}},
                ],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "customers"
        assert data["type"] == "auth"

    async def test_auth_collection_registration(self, client: AsyncClient):
        """Test user registration in auth collection."""
        # Create admin and auth collection first
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "admin2@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        admin_token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "vendors",
                "type": "auth",
                "schema": [],
            },
        )

        # Register as vendor
        response = await client.post(
            "/api/v1/collections/vendors/auth/register",
            json={
                "email": "vendor@example.com",
                "password": "VendorPass123!",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "vendor@example.com"

    async def test_auth_collection_login(self, client: AsyncClient):
        """Test user login in auth collection."""
        # Setup: Create admin, collection, and register user
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "admin3@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        admin_token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "members", "type": "auth", "schema": []},
        )

        await client.post(
            "/api/v1/collections/members/auth/register",
            json={
                "email": "member@example.com",
                "password": "MemberPass123!",
            },
        )

        # Login as member
        response = await client.post(
            "/api/v1/collections/members/auth/login",
            json={
                "email": "member@example.com",
                "password": "MemberPass123!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "member@example.com"


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
