"""
LangGraph Plugin for FastCMS.

Visual workflow builder for AI agent workflows using LangGraph.
"""

from pathlib import Path
from typing import Any, List

from fastapi import FastAPI

from app.core.plugin import BasePlugin


class LangGraphPlugin(BasePlugin):
    """LangGraph visual workflow builder plugin."""

    name = "langgraph"
    display_name = "LangGraph"
    description = "Visual workflow builder for AI agents using LangGraph"
    version = "0.1.0"
    author = "FastCMS Team"
    homepage = "https://fastcms.dev/plugins/langgraph"
    repository = "https://github.com/fastcms/plugin-langgraph"
    license = "MIT"

    # Dependencies
    requires = []
    depends_on = ["langgraph>=0.0.20", "langchain>=0.1.0"]

    def initialize(self) -> None:
        """Initialize the LangGraph plugin."""
        super().initialize()
        self.logger.info("🚀 LangGraph plugin initialized - Visual AI workflow builder ready!")

    def register_routes(self, app: FastAPI) -> None:
        """Register API routes."""
        from plugins.langgraph.routes import router

        app.include_router(
            router,
            prefix="/api/v1/plugins/langgraph",
            tags=["LangGraph Plugin"],
        )

        self.logger.info("API routes registered at /api/v1/plugins/langgraph")

    def register_admin_routes(self, app: FastAPI) -> None:
        """Register admin UI routes."""
        from plugins.langgraph.admin_routes import router

        app.include_router(
            router,
            prefix="/admin/langgraph",
            tags=["LangGraph Admin"],
        )

        self.logger.info("Admin routes registered at /admin/langgraph")

    def register_models(self) -> List[Any]:
        """Register database models."""
        from plugins.langgraph.models import Workflow, WorkflowNode, WorkflowEdge, WorkflowExecution

        self.logger.info("Registered 4 database models")
        return [Workflow, WorkflowNode, WorkflowEdge, WorkflowExecution]

    def shutdown(self) -> None:
        """Shutdown the plugin."""
        self.logger.info("LangGraph plugin shutting down")
        super().shutdown()
