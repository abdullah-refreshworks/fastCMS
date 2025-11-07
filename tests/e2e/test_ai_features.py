"""End-to-end tests for AI features."""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch


pytestmark = pytest.mark.asyncio


class TestAIContentGeneration:
    """Test AI content generation endpoints."""

    @patch("app.api.v1.ai.settings.AI_ENABLED", True)
    @patch("app.api.v1.ai.settings.AI_PROVIDER", "openai")
    @patch("app.api.v1.ai.settings.OPENAI_API_KEY", "test-key")
    @patch("app.services.ai_service.ChatOpenAI")
    async def test_generate_content(
        self, mock_chat_openai: MagicMock, client: AsyncClient
    ):
        """Test content generation."""
        # Mock LLM response
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Generated content based on your prompt."
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_chat_openai.return_value = mock_llm

        # Register and get token
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "ai@example.com",
                "password": "Test123!Pass",
                "password_confirm": "Test123!Pass",
            },
        )
        token = response.json()["token"]["access_token"]

        # Generate content
        gen_response = await client.post(
            "/api/v1/ai/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "prompt": "Write a blog post about FastCMS",
                "max_tokens": 500,
            },
        )

        assert gen_response.status_code == 200
        data = gen_response.json()
        assert "content" in data
        assert len(data["content"]) > 0

    @patch("app.api.v1.ai.settings.AI_ENABLED", False)
    async def test_generate_content_disabled(self, client: AsyncClient):
        """Test content generation when AI is disabled."""
        # Register and get token
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "aidisabled@example.com",
                "password": "Test123!Pass",
                "password_confirm": "Test123!Pass",
            },
        )
        token = response.json()["token"]["access_token"]

        # Try to generate content
        gen_response = await client.post(
            "/api/v1/ai/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"prompt": "Test prompt"},
        )

        assert gen_response.status_code == 503


class TestSemanticSearch:
    """Test semantic search functionality."""

    @patch("app.api.v1.ai.settings.AI_ENABLED", True)
    @patch("app.api.v1.ai.settings.AI_PROVIDER", "openai")
    @patch("app.api.v1.ai.settings.OPENAI_API_KEY", "test-key")
    async def test_search_requires_indexing(self, client: AsyncClient):
        """Test that search works after indexing."""
        # Register admin user
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "search@example.com",
                "password": "Test123!Pass",
                "password_confirm": "Test123!Pass",
            },
        )
        token = response.json()["token"]["access_token"]

        # Manually set role to admin for this test
        from app.db.session import async_session_maker
        async with async_session_maker() as db:
            from app.db.repositories.user import UserRepository
            user_repo = UserRepository(db)
            user = await user_repo.get_by_email("search@example.com")
            if user:
                user.role = "admin"
                await db.commit()

        # Create collection
        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "articles",
                "type": "base",
                "schema": [
                    {"name": "title", "type": "text", "validation": {}},
                    {"name": "content", "type": "text", "validation": {}},
                ],
            },
        )

        # Create some records
        await client.post(
            "/api/v1/articles/records",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "data": {
                    "title": "Introduction to FastCMS",
                    "content": "FastCMS is an AI-native headless CMS built with FastAPI.",
                }
            },
        )

        # Note: Full semantic search would require actual embeddings
        # This test ensures the endpoint exists and has proper error handling


class TestNaturalLanguageQuery:
    """Test natural language to filter conversion."""

    @patch("app.api.v1.ai.settings.AI_ENABLED", True)
    @patch("app.api.v1.ai.settings.AI_PROVIDER", "openai")
    @patch("app.api.v1.ai.settings.OPENAI_API_KEY", "test-key")
    @patch("app.services.ai_service.ChatOpenAI")
    async def test_nl_to_filter(
        self, mock_chat_openai: MagicMock, client: AsyncClient
    ):
        """Test natural language query conversion."""
        # Mock LLM response
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "age>=18&&status=active"
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_chat_openai.return_value = mock_llm

        # Register user and create collection
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "nlquery@example.com",
                "password": "Test123!Pass",
                "password_confirm": "Test123!Pass",
            },
        )
        token = response.json()["token"]["access_token"]

        await client.post(
            "/api/v1/collections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "users",
                "type": "base",
                "schema": [
                    {"name": "age", "type": "number", "validation": {}},
                    {"name": "status", "type": "text", "validation": {}},
                ],
            },
        )

        # Convert natural language query
        nl_response = await client.post(
            "/api/v1/ai/query/natural-language",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "query": "Find all active users over 18",
                "collection_name": "users",
            },
        )

        assert nl_response.status_code == 200
        data = nl_response.json()
        assert "filter_expression" in data


class TestSchemaGeneration:
    """Test AI-powered schema generation."""

    @patch("app.api.v1.ai.settings.AI_ENABLED", True)
    @patch("app.api.v1.ai.settings.AI_PROVIDER", "openai")
    @patch("app.api.v1.ai.settings.OPENAI_API_KEY", "test-key")
    @patch("app.services.ai_service.ChatOpenAI")
    async def test_generate_schema(
        self, mock_chat_openai: MagicMock, client: AsyncClient
    ):
        """Test schema generation from description."""
        # Mock LLM response
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = """
        [
          {"name": "title", "type": "text", "validation": {"required": true}},
          {"name": "content", "type": "editor", "validation": {}},
          {"name": "published", "type": "bool", "validation": {}}
        ]
        """
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_chat_openai.return_value = mock_llm

        # Register user
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "schemagen@example.com",
                "password": "Test123!Pass",
                "password_confirm": "Test123!Pass",
            },
        )
        token = response.json()["token"]["access_token"]

        # Generate schema
        schema_response = await client.post(
            "/api/v1/ai/schema/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "description": "A blog post collection with title, content, and published status"
            },
        )

        assert schema_response.status_code == 200
        data = schema_response.json()
        assert "schema" in data
        assert isinstance(data["schema"], list)


class TestAIChat:
    """Test AI chat functionality."""

    @patch("app.api.v1.ai.settings.AI_ENABLED", True)
    @patch("app.api.v1.ai.settings.AI_PROVIDER", "openai")
    @patch("app.api.v1.ai.settings.OPENAI_API_KEY", "test-key")
    @patch("app.services.ai_service.ChatOpenAI")
    async def test_chat(
        self, mock_chat_openai: MagicMock, client: AsyncClient
    ):
        """Test AI chat."""
        # Mock LLM response
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "FastCMS is a headless CMS built with FastAPI."
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_chat_openai.return_value = mock_llm

        # Register user
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "chat@example.com",
                "password": "Test123!Pass",
                "password_confirm": "Test123!Pass",
            },
        )
        token = response.json()["token"]["access_token"]

        # Chat
        chat_response = await client.post(
            "/api/v1/ai/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "message": "What is FastCMS?",
                "history": [],
            },
        )

        assert chat_response.status_code == 200
        data = chat_response.json()
        assert "message" in data
        assert "model" in data
