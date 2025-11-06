"""
Integration tests for admin API endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.collection import Collection
from app.db.models.user import User
from app.db.repositories.collection import CollectionRepository
from app.db.repositories.user import UserRepository


@pytest.fixture
async def admin_user(db: AsyncSession) -> User:
    """Create admin user for testing."""
    from app.core.security import hash_password

    user = User(
        email="admin@test.com",
        password_hash=hash_password("AdminPass123!"),
        name="Admin User",
        role="admin",
        verified=True,
        token_key="test_key",
    )

    user_repo = UserRepository(db)
    created_user = await user_repo.create(user)
    await db.commit()
    return created_user


@pytest.fixture
async def regular_user(db: AsyncSession) -> User:
    """Create regular user for testing."""
    from app.core.security import hash_password

    user = User(
        email="user@test.com",
        password_hash=hash_password("UserPass123!"),
        name="Regular User",
        role="user",
        verified=True,
        token_key="test_key",
    )

    user_repo = UserRepository(db)
    created_user = await user_repo.create(user)
    await db.commit()
    return created_user


@pytest.fixture
async def admin_token(client: AsyncClient, admin_user: User) -> str:
    """Get admin access token."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "AdminPass123!"},
    )
    assert response.status_code == 200
    data = response.json()
    return data["token"]["access_token"]


@pytest.fixture
async def user_token(client: AsyncClient, regular_user: User) -> str:
    """Get regular user access token."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "user@test.com", "password": "UserPass123!"},
    )
    assert response.status_code == 200
    data = response.json()
    return data["token"]["access_token"]


class TestAdminStats:
    """Test admin stats endpoint."""

    async def test_get_stats_as_admin(
        self, client: AsyncClient, admin_token: str, db: AsyncSession
    ):
        """Admin can get system stats."""
        response = await client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "users" in data
        assert "collections" in data
        assert "total" in data["users"]
        assert "admins" in data["users"]
        assert "recent" in data["users"]

    async def test_get_stats_as_user_denied(
        self, client: AsyncClient, user_token: str
    ):
        """Regular user cannot get system stats."""
        response = await client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 401

    async def test_get_stats_without_auth_denied(self, client: AsyncClient):
        """Unauthenticated access denied."""
        response = await client.get("/api/v1/admin/stats")
        assert response.status_code == 401


class TestAdminUsers:
    """Test admin user management endpoints."""

    async def test_list_users_as_admin(
        self, client: AsyncClient, admin_token: str, db: AsyncSession
    ):
        """Admin can list all users."""
        response = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert len(data["items"]) >= 2  # At least admin and regular user

    async def test_get_user_as_admin(
        self, client: AsyncClient, admin_token: str, regular_user: User
    ):
        """Admin can get user details."""
        response = await client.get(
            f"/api/v1/admin/users/{regular_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == regular_user.id
        assert data["email"] == regular_user.email
        assert data["role"] == "user"

    async def test_update_user_role_as_admin(
        self, client: AsyncClient, admin_token: str, regular_user: User
    ):
        """Admin can update user role."""
        response = await client.patch(
            f"/api/v1/admin/users/{regular_user.id}/role?role=admin",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["role"] == "admin"

    async def test_cannot_change_own_role(
        self, client: AsyncClient, admin_token: str, admin_user: User
    ):
        """Admin cannot change their own role."""
        response = await client.patch(
            f"/api/v1/admin/users/{admin_user.id}/role?role=user",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400

    async def test_delete_user_as_admin(
        self, client: AsyncClient, admin_token: str, db: AsyncSession
    ):
        """Admin can delete users."""
        from app.core.security import hash_password

        # Create temp user
        user = User(
            email="temp@test.com",
            password_hash=hash_password("TempPass123!"),
            name="Temp User",
            role="user",
            verified=True,
            token_key="test_key",
        )
        user_repo = UserRepository(db)
        temp_user = await user_repo.create(user)
        await db.commit()

        response = await client.delete(
            f"/api/v1/admin/users/{temp_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 204

    async def test_cannot_delete_self(
        self, client: AsyncClient, admin_token: str, admin_user: User
    ):
        """Admin cannot delete their own account."""
        response = await client.delete(
            f"/api/v1/admin/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400

    async def test_user_management_denied_for_regular_user(
        self, client: AsyncClient, user_token: str, regular_user: User
    ):
        """Regular users cannot access admin endpoints."""
        # List users
        response = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 401

        # Get user
        response = await client.get(
            f"/api/v1/admin/users/{regular_user.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 401

        # Update role
        response = await client.patch(
            f"/api/v1/admin/users/{regular_user.id}/role?role=admin",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 401


class TestAdminCollections:
    """Test admin collection management endpoints."""

    async def test_list_collections_as_admin(
        self, client: AsyncClient, admin_token: str, db: AsyncSession
    ):
        """Admin can list all collections."""
        # Create test collection
        collection = Collection(
            name="test_collection",
            type="base",
            schema={"fields": []},
            options={},
        )
        collection_repo = CollectionRepository(db)
        await collection_repo.create(collection)
        await db.commit()

        response = await client.get(
            "/api/v1/admin/collections",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1

    async def test_delete_collection_as_admin(
        self, client: AsyncClient, admin_token: str, db: AsyncSession
    ):
        """Admin can delete collections."""
        # Create test collection
        collection = Collection(
            name="deletable_collection",
            type="base",
            schema={"fields": []},
            options={},
            system=False,
        )
        collection_repo = CollectionRepository(db)
        created = await collection_repo.create(collection)
        await db.commit()

        response = await client.delete(
            f"/api/v1/admin/collections/{created.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 204

    async def test_cannot_delete_system_collection(
        self, client: AsyncClient, admin_token: str, db: AsyncSession
    ):
        """Cannot delete system collections."""
        # Create system collection
        collection = Collection(
            name="system_collection",
            type="base",
            schema={"fields": []},
            options={},
            system=True,
        )
        collection_repo = CollectionRepository(db)
        created = await collection_repo.create(collection)
        await db.commit()

        response = await client.delete(
            f"/api/v1/admin/collections/{created.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400
