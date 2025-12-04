"""
Langflow plugin configuration.
"""

import os
from pydantic import BaseModel, Field


class LangflowConfig(BaseModel):
    """Langflow plugin configuration schema."""

    # Connection settings
    langflow_url: str = Field(
        default=os.getenv("LANGFLOW_URL", "http://localhost:7860"),
        description="Langflow server URL",
    )
    langflow_host: str = Field(
        default=os.getenv("LANGFLOW_HOST", "127.0.0.1"),
        description="Host to bind Langflow to when auto-starting",
    )
    langflow_port: int = Field(
        default=int(os.getenv("LANGFLOW_PORT", "7860")),
        description="Port for Langflow when auto-starting",
    )
    api_key: str = Field(
        default=os.getenv("LANGFLOW_API_KEY", ""),
        description="Langflow API key (x-api-key header)",
    )

    # Auto-start settings
    auto_start: bool = Field(
        default=os.getenv("LANGFLOW_AUTO_START", "true").lower() == "true",
        description="Automatically start Langflow when FastCMS starts",
    )
    use_docker: bool = Field(
        default=os.getenv("LANGFLOW_USE_DOCKER", "true").lower() == "true",
        description="Use Docker to run Langflow (recommended)",
    )
    docker_image: str = Field(
        default=os.getenv("LANGFLOW_DOCKER_IMAGE", "langflowai/langflow:latest"),
        description="Docker image for Langflow",
    )
    langflow_command: str = Field(
        default=os.getenv("LANGFLOW_COMMAND", "langflow"),
        description="Command to run Langflow (e.g., 'langflow', 'pipx run langflow', or full path)",
    )

    # Feature flags
    embed_ui: bool = Field(
        default=os.getenv("LANGFLOW_EMBED_UI", "true").lower() == "true",
        description="Embed Langflow UI in admin (iframe)",
    )
    proxy_api: bool = Field(
        default=os.getenv("LANGFLOW_PROXY_API", "true").lower() == "true",
        description="Proxy Langflow API through FastCMS",
    )

    # Timeouts
    request_timeout: int = Field(
        default=int(os.getenv("LANGFLOW_REQUEST_TIMEOUT", "300")),
        description="Request timeout in seconds",
    )
    startup_timeout: int = Field(
        default=int(os.getenv("LANGFLOW_STARTUP_TIMEOUT", "60")),
        description="Timeout in seconds to wait for Langflow to start",
    )

    model_config = {"extra": "ignore"}
