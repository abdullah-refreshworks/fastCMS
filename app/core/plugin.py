"""
Base plugin system for FastCMS.

Provides the foundation for creating plugins that extend FastCMS functionality.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession


class BasePlugin(ABC):
    """
    Base class for all FastCMS plugins.

    All plugins must inherit from this class and implement the required methods.
    """

    # Required metadata
    name: str = ""  # Unique identifier (e.g., "langflow")
    display_name: str = ""  # Human-readable name (e.g., "Langflow")
    description: str = ""  # Short description
    version: str = "0.1.0"  # Semantic version
    author: str = ""  # Plugin author

    # Optional metadata
    homepage: str = ""  # Plugin website
    repository: str = ""  # Source code URL
    license: str = "MIT"  # License type

    # Dependencies
    requires: List[str] = []  # Required plugins
    depends_on: List[str] = []  # Python packages

    def __init__(self):
        """Initialize the plugin."""
        if not self.name:
            raise ValueError(f"Plugin {self.__class__.__name__} must define 'name'")
        if not self.display_name:
            raise ValueError(f"Plugin {self.__class__.__name__} must define 'display_name'")

        self._logger = None
        self._config: Dict[str, Any] = {}
        self._enabled = True

    @property
    def logger(self) -> logging.Logger:
        """Get plugin logger."""
        if self._logger is None:
            self._logger = logging.getLogger(f"plugin.{self.name}")
        return self._logger

    @property
    def config(self) -> Dict[str, Any]:
        """Get plugin configuration."""
        return self._config

    def set_config(self, config: Dict[str, Any]) -> None:
        """Set plugin configuration."""
        self._config = config

    @property
    def enabled(self) -> bool:
        """Check if plugin is enabled."""
        return self._enabled

    def enable(self) -> None:
        """Enable the plugin."""
        self._enabled = True
        self.logger.info(f"Plugin {self.display_name} enabled")

    def disable(self) -> None:
        """Disable the plugin."""
        self._enabled = False
        self.logger.info(f"Plugin {self.display_name} disabled")

    # Lifecycle hooks

    def initialize(self) -> None:
        """
        Called when plugin is loaded.

        Use this to set up any initialization logic.
        """
        self.logger.info(f"{self.display_name} v{self.version} initialized")

    def shutdown(self) -> None:
        """
        Called when plugin is unloaded.

        Use this to clean up resources.
        """
        self.logger.info(f"{self.display_name} shutting down")

    # Feature registration

    def register_routes(self, app: FastAPI) -> None:
        """
        Register API routes with the FastAPI app.

        Args:
            app: FastAPI application instance

        Example:
            router = APIRouter()

            @router.get("/hello")
            async def hello():
                return {"message": "Hello from plugin!"}

            app.include_router(
                router,
                prefix=f"/api/v1/plugins/{self.name}",
                tags=[self.display_name]
            )
        """
        pass

    def register_admin_routes(self, app: FastAPI) -> None:
        """
        Register admin UI routes (Jinja2 templates).

        Args:
            app: FastAPI application instance

        Example:
            from fastapi import Request
            from fastapi.responses import HTMLResponse
            from fastapi.templating import Jinja2Templates

            templates = Jinja2Templates(directory="plugins/my_plugin/templates")
            router = APIRouter()

            @router.get("/", response_class=HTMLResponse)
            async def admin_page(request: Request):
                return templates.TemplateResponse("admin.html", {"request": request})

            app.include_router(
                router,
                prefix=f"/admin/plugins/{self.name}",
                tags=[f"{self.display_name} Admin"]
            )
        """
        pass

    def register_models(self) -> List[Any]:
        """
        Register database models.

        Returns:
            List of SQLAlchemy model classes

        Example:
            from plugins.my_plugin.models import MyModel
            return [MyModel]
        """
        return []

    def register_events(self) -> None:
        """
        Register event listeners.

        Example:
            from app.core.events import event_manager

            @event_manager.on("user.created")
            async def on_user_created(user):
                self.logger.info(f"User created: {user.email}")
        """
        pass

    def get_config_schema(self) -> Optional[Any]:
        """
        Return Pydantic model for plugin settings.

        Returns:
            Pydantic BaseModel class or None

        Example:
            from pydantic import BaseModel, Field

            class MyPluginConfig(BaseModel):
                api_key: str = Field(..., description="API key")
                timeout: int = Field(30, description="Request timeout")

            return MyPluginConfig
        """
        return None

    def get_info(self) -> Dict[str, Any]:
        """
        Get plugin information.

        Returns:
            Dictionary with plugin metadata
        """
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "homepage": self.homepage,
            "repository": self.repository,
            "license": self.license,
            "enabled": self.enabled,
            "requires": self.requires,
            "depends_on": self.depends_on,
        }
