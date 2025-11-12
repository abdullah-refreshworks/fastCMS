"""
End-to-end tests for complete workflows.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestAccessControlWorkflow:
    """Test complete access control workflow."""

    async def test_public_collection_workflow(self, client: AsyncClient):
        """Test public collection workflow."""
        # 1. Register user
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "testuser@example.com",
                "password": "Test123!Pass",
                "password_confirm": "Test123!Pass",
                "name": "Test User",
            },
        )
        assert response.status_code == 201
        token = response.json()["token"]["access_token"]

        # 2. Create collection with public list/view, authenticated create
        response = await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "public_posts",
                "type": "base",
                "schema": [
                    {"name": "title", "type": "text", "validation": {"required": True}},
                    {"name": "content", "type": "editor", "validation": {}},
                ],
                "list_rule": "",  # Public
                "view_rule": "",  # Public
                "create_rule": "@request.auth.id != ''",  # Authenticated only
            },
        )
        assert response.status_code == 200

        # 3. Create a record (authenticated)
        response = await client.post(
            "/api/v1/public_posts/records",
            headers={"Authorization": f"Bearer {token}"},
            json={"data": {"title": "Hello World", "content": "This is a test"}},
        )
        assert response.status_code == 201
        record_id = response.json()["id"]

        # 4. List records without auth (public access)
        response = await client.get("/api/v1/public_posts/records")
        assert response.status_code == 200
        assert len(response.json()["items"]) >= 1

        # 5. View record without auth (public access)
        response = await client.get(f"/api/v1/public_posts/records/{record_id}")
        assert response.status_code == 200
        assert response.json()["data"]["title"] == "Hello World"

        # 6. Try to create without auth (should fail)
        response = await client.post(
            "/api/v1/public_posts/records",
            json={"data": {"title": "Unauthorized", "content": "Should fail"}},
        )
        assert response.status_code == 403

    async def test_owner_only_workflow(self, client: AsyncClient):
        """Test owner-only access control workflow."""
        # 1. Register first user
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "owner@example.com",
                "password": "Owner123!Pass",
                "password_confirm": "Owner123!Pass",
                "name": "Owner",
            },
        )
        assert response.status_code == 201
        owner_token = response.json()["token"]["access_token"]
        owner_id = response.json()["user"]["id"]

        # 2. Register second user
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "other@example.com",
                "password": "Other123!Pass",
                "password_confirm": "Other123!Pass",
                "name": "Other User",
            },
        )
        assert response.status_code == 201
        other_token = response.json()["token"]["access_token"]

        # 3. Create collection with owner-only rules
        response = await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "name": "private_notes",
                "type": "base",
                "schema": [
                    {"name": "title", "type": "text", "validation": {"required": True}},
                    {"name": "user_id", "type": "text", "validation": {"required": True}},
                ],
                "list_rule": "@request.auth.id != ''",
                "view_rule": "@request.auth.id = @record.user_id",
                "create_rule": "@request.auth.id != ''",
                "update_rule": "@request.auth.id = @record.user_id",
                "delete_rule": "@request.auth.id = @record.user_id",
            },
        )
        assert response.status_code == 200

        # 4. Owner creates a record
        response = await client.post(
            "/api/v1/private_notes/records",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"data": {"title": "My Private Note", "user_id": owner_id}},
        )
        assert response.status_code == 201
        record_id = response.json()["id"]

        # 5. Owner can view their record
        response = await client.get(
            f"/api/v1/private_notes/records/{record_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert response.status_code == 200

        # 6. Other user cannot view owner's record
        response = await client.get(
            f"/api/v1/private_notes/records/{record_id}",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert response.status_code == 403

        # 7. Owner can update their record
        response = await client.patch(
            f"/api/v1/private_notes/records/{record_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"data": {"title": "Updated Note"}},
        )
        assert response.status_code == 200

        # 8. Other user cannot update owner's record
        response = await client.patch(
            f"/api/v1/private_notes/records/{record_id}",
            headers={"Authorization": f"Bearer {other_token}"},
            json={"data": {"title": "Hacked"}},
        )
        assert response.status_code == 403

    async def test_admin_override_workflow(self, client: AsyncClient, db: AsyncSession):
        """Test admin can override access rules."""
        from app.core.security import hash_password
        from app.db.models.user import User
        from app.db.repositories.user import UserRepository

        # 1. Create admin user
        admin = User(
            email="admin@example.com",
            password_hash=hash_password("Admin123!Pass"),
            name="Admin",
            role="admin",
            verified=True,
            token_key="test_key",
        )
        user_repo = UserRepository(db)
        await user_repo.create(admin)
        await db.commit()

        # 2. Login as admin
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "Admin123!Pass"},
        )
        assert response.status_code == 200
        admin_token = response.json()["token"]["access_token"]

        # 3. Register regular user
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "regular@example.com",
                "password": "Regular123!Pass",
                "password_confirm": "Regular123!Pass",
                "name": "Regular User",
            },
        )
        assert response.status_code == 201
        user_token = response.json()["token"]["access_token"]
        user_id = response.json()["user"]["id"]

        # 4. Create collection with admin-or-owner rules
        response = await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "name": "managed_content",
                "type": "base",
                "schema": [
                    {"name": "title", "type": "text", "validation": {"required": True}},
                    {"name": "user_id", "type": "text", "validation": {"required": True}},
                ],
                "list_rule": "@request.auth.id != ''",
                "view_rule": "",
                "create_rule": "@request.auth.id != ''",
                "update_rule": "@request.auth.id = @record.user_id || @request.auth.role = 'admin'",
                "delete_rule": "@request.auth.id = @record.user_id || @request.auth.role = 'admin'",
            },
        )
        assert response.status_code == 200

        # 5. User creates record
        response = await client.post(
            "/api/v1/managed_content/records",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"data": {"title": "User Content", "user_id": user_id}},
        )
        assert response.status_code == 201
        record_id = response.json()["id"]

        # 6. Admin can update user's record (admin override)
        response = await client.patch(
            f"/api/v1/managed_content/records/{record_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"data": {"title": "Moderated by Admin"}},
        )
        assert response.status_code == 200

        # 7. Admin can delete user's record (admin override)
        response = await client.delete(
            f"/api/v1/managed_content/records/{record_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 204


class TestAdminDashboardWorkflow:
    """Test complete admin dashboard workflow."""

    async def test_complete_admin_workflow(self, client: AsyncClient, db: AsyncSession):
        """Test complete admin workflow from login to management."""
        from app.core.security import hash_password
        from app.db.models.user import User
        from app.db.repositories.user import UserRepository

        # 1. Create admin user
        admin = User(
            email="superadmin@example.com",
            password_hash=hash_password("SuperAdmin123!"),
            name="Super Admin",
            role="admin",
            verified=True,
            token_key="test_key",
        )
        user_repo = UserRepository(db)
        await user_repo.create(admin)
        await db.commit()

        # 2. Login as admin
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "superadmin@example.com", "password": "SuperAdmin123!"},
        )
        assert response.status_code == 200
        assert response.json()["user"]["role"] == "admin"
        admin_token = response.json()["token"]["access_token"]

        # 3. Get system stats
        response = await client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert "users" in response.json()
        assert "collections" in response.json()

        # 4. List all users
        response = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) >= 1

        # 5. Create regular user
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "NewUser123!",
                "password_confirm": "NewUser123!",
                "name": "New User",
            },
        )
        assert response.status_code == 201
        new_user_id = response.json()["user"]["id"]

        # 6. Promote user to admin
        response = await client.patch(
            f"/api/v1/admin/users/{new_user_id}/role?role=admin",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["role"] == "admin"

        # 7. Demote user back to regular
        response = await client.patch(
            f"/api/v1/admin/users/{new_user_id}/role?role=user",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["role"] == "user"

        # 8. Delete user
        response = await client.delete(
            f"/api/v1/admin/users/{new_user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 204

        # 9. Verify user is deleted
        response = await client.get(
            f"/api/v1/admin/users/{new_user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404
