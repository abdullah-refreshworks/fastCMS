"""
End-to-end tests for Langflow plugin.

These tests verify the Langflow plugin integration with FastCMS.
Note: Most tests mock the Langflow server to avoid external dependencies.
"""

import asyncio
import os
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
LANGFLOW_URL = os.getenv("LANGFLOW_URL", "http://localhost:7860")


class TestLangflowPlugin:
    """Test suite for Langflow plugin."""

    @pytest.fixture
    async def auth_headers(self):
        """Get authentication headers."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            # Try to login with test credentials
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "admin@fastcms.dev", "password": "admin"},
            )
            if response.status_code == 200:
                token = response.json()["access_token"]
                return {"Authorization": f"Bearer {token}"}
            # Return empty headers if login fails
            return {}

    @pytest.mark.asyncio
    async def test_health_endpoint_exists(self, auth_headers):
        """Test that health endpoint exists and returns valid response."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            response = await client.get(
                "/api/v1/plugins/langflow/health",
                headers=auth_headers,
            )

            # Should return 200 OK regardless of Langflow connection
            assert response.status_code == 200

            data = response.json()
            assert "status" in data
            assert data["status"] in ["connected", "disconnected"]

    @pytest.mark.asyncio
    async def test_flows_endpoint_requires_auth(self):
        """Test that flows endpoint requires authentication."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            response = await client.get("/api/v1/plugins/langflow/flows")

            # Should return 401 Unauthorized without token
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_flows_endpoint_with_auth(self, auth_headers):
        """Test flows endpoint with valid authentication."""
        if not auth_headers:
            pytest.skip("Authentication not available")

        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            response = await client.get(
                "/api/v1/plugins/langflow/flows",
                headers=auth_headers,
            )

            # Should return 200 or 502 (if Langflow not available)
            assert response.status_code in [200, 502]

    @pytest.mark.asyncio
    async def test_run_flow_endpoint_requires_auth(self):
        """Test that run endpoint requires authentication."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            response = await client.post(
                "/api/v1/plugins/langflow/flows/test-id/run",
                json={"input_value": "test"},
            )

            # Should return 401 Unauthorized without token
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_admin_page_requires_admin(self):
        """Test that admin page requires admin user."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            response = await client.get("/admin/langflow/")

            # Should redirect to login or return 401/403
            assert response.status_code in [302, 401, 403]


class TestLangflowClient:
    """Test Langflow client functionality."""

    @pytest.mark.asyncio
    async def test_client_health_check_connected(self):
        """Test client health check when connected."""
        from plugins.langflow.client import LangflowClient

        client = LangflowClient("http://localhost:7860")

        # Mock successful response
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await client.health_check()

            assert result["status"] == "connected"
            assert result["langflow_url"] == "http://localhost:7860"

    @pytest.mark.asyncio
    async def test_client_health_check_disconnected(self):
        """Test client health check when disconnected."""
        from plugins.langflow.client import LangflowClient

        client = LangflowClient("http://localhost:7860")

        # Mock connection error
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("Connection refused")
            )

            result = await client.health_check()

            assert result["status"] == "disconnected"
            assert "error" in result

    @pytest.mark.asyncio
    async def test_client_list_flows(self):
        """Test client list flows."""
        from plugins.langflow.client import LangflowClient

        client = LangflowClient("http://localhost:7860")

        mock_flows = [
            {"id": "flow-1", "name": "Test Flow 1"},
            {"id": "flow-2", "name": "Test Flow 2"},
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_flows
            mock_response.raise_for_status = AsyncMock()
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await client.list_flows()

            assert "flows" in result
            assert len(result["flows"]) == 2

    @pytest.mark.asyncio
    async def test_client_run_flow(self):
        """Test client run flow."""
        from plugins.langflow.client import LangflowClient

        client = LangflowClient("http://localhost:7860")

        mock_result = {
            "outputs": [{"result": "Hello!"}],
            "session_id": "test-session",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_result
            mock_response.raise_for_status = AsyncMock()
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await client.run_flow("flow-1", "Hello!")

            assert "outputs" in result
            assert result["session_id"] == "test-session"


class TestLangflowConfig:
    """Test Langflow configuration."""

    def test_config_defaults(self):
        """Test configuration default values."""
        from plugins.langflow.config import LangflowConfig

        # Clear env vars for test
        original_url = os.environ.pop("LANGFLOW_URL", None)
        original_key = os.environ.pop("LANGFLOW_API_KEY", None)

        try:
            config = LangflowConfig()
            assert config.langflow_url == "http://localhost:7860"
            assert config.api_key == ""
            assert config.embed_ui is True
            assert config.request_timeout == 300
        finally:
            # Restore env vars
            if original_url:
                os.environ["LANGFLOW_URL"] = original_url
            if original_key:
                os.environ["LANGFLOW_API_KEY"] = original_key

    def test_config_from_env(self):
        """Test configuration from environment variables."""
        from plugins.langflow.config import LangflowConfig

        # Set test env vars
        os.environ["LANGFLOW_URL"] = "http://test:9999"
        os.environ["LANGFLOW_API_KEY"] = "test-key"
        os.environ["LANGFLOW_EMBED_UI"] = "false"

        try:
            config = LangflowConfig()
            assert config.langflow_url == "http://test:9999"
            assert config.api_key == "test-key"
            assert config.embed_ui is False
        finally:
            # Clean up
            del os.environ["LANGFLOW_URL"]
            del os.environ["LANGFLOW_API_KEY"]
            del os.environ["LANGFLOW_EMBED_UI"]


class TestLangflowSchemas:
    """Test Langflow request/response schemas."""

    def test_flow_execute_request(self):
        """Test FlowExecuteRequest schema."""
        from plugins.langflow.schemas import FlowExecuteRequest

        request = FlowExecuteRequest(input_value="Hello!")
        assert request.input_value == "Hello!"
        assert request.tweaks is None

        request_with_tweaks = FlowExecuteRequest(
            input_value="Hello!", tweaks={"param": "value"}
        )
        assert request_with_tweaks.tweaks == {"param": "value"}

    def test_health_response(self):
        """Test HealthResponse schema."""
        from plugins.langflow.schemas import HealthResponse

        response = HealthResponse(
            status="connected", langflow_url="http://localhost:7860"
        )
        assert response.status == "connected"
        assert response.error is None


def run_tests():
    """Run all tests manually."""
    print("=" * 60)
    print("Langflow Plugin E2E Tests")
    print("=" * 60)

    # Run pytest programmatically
    import sys

    sys.exit(pytest.main([__file__, "-v"]))


if __name__ == "__main__":
    run_tests()
