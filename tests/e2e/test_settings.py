"""
E2E tests for system settings functionality.
Tests: Settings CRUD operations, categories, and access control.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
class TestSettings:
    """Test system settings management."""

    async def test_create_setting(self, client: AsyncClient):
        """Test creating a new setting."""
        # Setup: Create admin user
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "settings_admin@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        # Create setting
        response = await client.post(
            "/api/v1/settings",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "key": "app_name",
                "value": "My FastCMS",
                "category": "app",
                "description": "Application name",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "app_name"
        assert data["value"] == "My FastCMS"
        assert data["category"] == "app"
        assert "id" in data

    async def test_update_setting(self, client: AsyncClient):
        """Test updating an existing setting."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "settings_update@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        # Create setting
        await client.post(
            "/api/v1/settings",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "key": "maintenance_mode",
                "value": False,
                "category": "app",
                "description": "Maintenance mode enabled",
            },
        )

        # Update setting
        response = await client.post(
            "/api/v1/settings",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "key": "maintenance_mode",
                "value": True,
                "category": "app",
                "description": "Maintenance mode enabled",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["value"] is True

    async def test_get_all_settings(self, client: AsyncClient):
        """Test getting all settings."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "settings_getall@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        # Create multiple settings
        settings = [
            {"key": "app_name", "value": "FastCMS", "category": "app"},
            {"key": "smtp_host", "value": "smtp.gmail.com", "category": "email"},
            {"key": "max_file_size", "value": 10485760, "category": "storage"},
        ]

        for setting in settings:
            await client.post(
                "/api/v1/settings",
                headers={"Authorization": f"Bearer {token}"},
                json=setting,
            )

        # Get all settings
        response = await client.get(
            "/api/v1/settings",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    async def test_get_settings_by_category(self, client: AsyncClient):
        """Test getting settings filtered by category."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "settings_category@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        # Create settings in different categories
        settings = [
            {"key": "app_name", "value": "FastCMS", "category": "app"},
            {"key": "app_version", "value": "1.0.0", "category": "app"},
            {"key": "smtp_host", "value": "smtp.gmail.com", "category": "email"},
            {"key": "smtp_port", "value": 587, "category": "email"},
        ]

        for setting in settings:
            await client.post(
                "/api/v1/settings",
                headers={"Authorization": f"Bearer {token}"},
                json=setting,
            )

        # Get settings by category
        response = await client.get(
            "/api/v1/settings/app",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert all(s["category"] == "app" for s in data)
        assert len(data) >= 2

    async def test_delete_setting(self, client: AsyncClient):
        """Test deleting a setting."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "settings_delete@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        # Create setting
        await client.post(
            "/api/v1/settings",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "key": "temp_setting",
                "value": "temporary",
                "category": "custom",
            },
        )

        # Delete setting
        response = await client.delete(
            "/api/v1/settings/temp_setting",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] is True

        # Verify deletion
        response = await client.get(
            "/api/v1/settings/custom",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert not any(s["key"] == "temp_setting" for s in data)

    async def test_settings_support_different_types(self, client: AsyncClient):
        """Test that settings support different value types."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "settings_types@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        # Create settings with different types
        settings = [
            {"key": "string_value", "value": "test", "category": "custom"},
            {"key": "number_value", "value": 42, "category": "custom"},
            {"key": "boolean_value", "value": True, "category": "custom"},
            {"key": "float_value", "value": 3.14, "category": "custom"},
        ]

        for setting in settings:
            response = await client.post(
                "/api/v1/settings",
                headers={"Authorization": f"Bearer {token}"},
                json=setting,
            )
            assert response.status_code == 200

        # Verify all were created
        response = await client.get(
            "/api/v1/settings/custom",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert len(data) >= 4

    async def test_settings_feature_flags(self, client: AsyncClient):
        """Test using settings as feature flags."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "settings_flags@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        # Create feature flags
        feature_flags = [
            {"key": "enable_ai_features", "value": True, "category": "app"},
            {"key": "enable_webhooks", "value": True, "category": "app"},
            {"key": "enable_realtime", "value": False, "category": "app"},
        ]

        for flag in feature_flags:
            await client.post(
                "/api/v1/settings",
                headers={"Authorization": f"Bearer {token}"},
                json={**flag, "description": f"Feature flag: {flag['key']}"},
            )

        # Get app settings
        response = await client.get(
            "/api/v1/settings/app",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify feature flags exist
        feature_keys = {s["key"] for s in data}
        assert "enable_ai_features" in feature_keys
        assert "enable_webhooks" in feature_keys
        assert "enable_realtime" in feature_keys

    async def test_settings_rate_limits(self, client: AsyncClient):
        """Test using settings for rate limits."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "settings_limits@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        # Create rate limit settings
        await client.post(
            "/api/v1/settings",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "key": "api_rate_limit",
                "value": 100,
                "category": "security",
                "description": "Max API requests per minute",
            },
        )

        await client.post(
            "/api/v1/settings",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "key": "file_upload_limit",
                "value": 10485760,
                "category": "storage",
                "description": "Max file size in bytes (10MB)",
            },
        )

        # Get security settings
        response = await client.get(
            "/api/v1/settings/security",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        rate_limit = next((s for s in data if s["key"] == "api_rate_limit"), None)
        assert rate_limit is not None
        assert rate_limit["value"] == 100

    async def test_settings_requires_authentication(self, client: AsyncClient):
        """Test that settings endpoints require authentication."""
        # Try to create setting without token
        response = await client.post(
            "/api/v1/settings",
            json={
                "key": "test",
                "value": "value",
                "category": "custom",
            },
        )
        assert response.status_code == 401

        # Try to get settings without token
        response = await client.get("/api/v1/settings")
        assert response.status_code == 401

        # Try to delete setting without token
        response = await client.delete("/api/v1/settings/test")
        assert response.status_code == 401

    async def test_setting_categories(self, client: AsyncClient):
        """Test all standard setting categories."""
        # Setup
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "settings_categories@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
        )
        token = response.json()["token"]["access_token"]

        # Create settings in all categories
        categories = ["app", "email", "security", "storage", "custom"]

        for category in categories:
            await client.post(
                "/api/v1/settings",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "key": f"{category}_setting",
                    "value": f"value_{category}",
                    "category": category,
                    "description": f"Test {category} setting",
                },
            )

        # Verify each category
        for category in categories:
            response = await client.get(
                f"/api/v1/settings/{category}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data) >= 1
            assert all(s["category"] == category for s in data)
