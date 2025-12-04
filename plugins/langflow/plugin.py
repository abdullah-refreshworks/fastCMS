"""
Langflow integration plugin for FastCMS.

Provides visual AI workflow building through Langflow integration.
"""

import logging
import shutil
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI

from app.core.plugin import BasePlugin
from plugins.langflow.config import LangflowConfig

logger = logging.getLogger(__name__)


class LangflowPlugin(BasePlugin):
    """
    Langflow integration plugin.

    Provides a lightweight integration with Langflow for visual AI workflow building.
    Instead of building a custom workflow engine, this plugin proxies requests to
    a Langflow instance and optionally embeds the Langflow UI.
    """

    # Required metadata
    name = "langflow"
    display_name = "Langflow"
    description = "Visual AI workflow builder powered by Langflow"
    version = "1.0.0"
    author = "FastCMS Team"

    # Optional metadata
    homepage = "https://www.langflow.org/"
    repository = "https://github.com/langflow-ai/langflow"
    license = "MIT"

    # No additional Python dependencies - uses httpx already in FastCMS
    depends_on: List[str] = []
    requires: List[str] = []

    # Process handle for Langflow subprocess
    _langflow_process: Optional[subprocess.Popen] = None
    _docker_container: Optional[str] = None

    def initialize(self) -> None:
        """Initialize the plugin."""
        super().initialize()
        self._config = LangflowConfig()

        if self._config.auto_start:
            self._start_langflow()
        else:
            self.logger.info("Langflow auto-start disabled")
            self.logger.info(f"Configure LANGFLOW_URL to connect to external Langflow: {self._config.langflow_url}")

    def _start_langflow(self) -> None:
        """Start Langflow as a subprocess or Docker container."""
        # Check if Langflow is already running
        if self._is_langflow_running():
            self.logger.info(f"Langflow already running at {self._config.langflow_url}")
            return

        if self._config.use_docker:
            self._start_langflow_docker()
        else:
            self._start_langflow_native()

    def _start_langflow_docker(self) -> None:
        """Start Langflow using Docker."""
        # Check if Docker is available
        docker_path = shutil.which("docker")
        if not docker_path:
            self.logger.warning("Docker not found. Set LANGFLOW_USE_DOCKER=false to use native mode")
            return

        try:
            # Check if container already exists
            container_name = "fastcms-langflow"
            result = subprocess.run(
                ["docker", "ps", "-a", "-q", "-f", f"name={container_name}"],
                capture_output=True,
                text=True
            )

            if result.stdout.strip():
                # Container exists, remove it first
                self.logger.info(f"Removing existing Langflow container...")
                subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)

            # Start Langflow container
            cmd = [
                "docker", "run", "-d",
                "--name", container_name,
                "-p", f"{self._config.langflow_port}:7860",
                "-e", "LANGFLOW_AUTO_LOGIN=true",
                self._config.docker_image,
            ]

            self.logger.info(f"Starting Langflow Docker container: {self._config.docker_image}")
            self._langflow_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Wait for container to start
            self._langflow_process.wait()

            # Store container name for cleanup
            self._docker_container = container_name

            # Wait for Langflow to be ready
            self._wait_for_langflow()

        except Exception as e:
            self.logger.error(f"Failed to start Langflow Docker container: {e}")
            self.logger.info("You can start manually: docker run -p 7860:7860 langflowai/langflow:latest")

    def _start_langflow_native(self) -> None:
        """Start Langflow using native command."""
        langflow_cmd = self._config.langflow_command.split()[0]
        langflow_path = shutil.which(langflow_cmd)

        if not langflow_path and langflow_cmd == "langflow":
            # Try common locations
            for path in [
                sys.prefix + "/bin/langflow",
                "/usr/local/bin/langflow",
                "~/.local/bin/langflow",
            ]:
                expanded = shutil.which(path) or (path if shutil.which(path.replace("~", "")) else None)
                if expanded and shutil.which(expanded):
                    langflow_path = expanded
                    break

        if not langflow_path and langflow_cmd == "langflow":
            self.logger.warning(
                "Langflow command not found. Install it with: pipx install langflow"
            )
            self.logger.warning("Or set LANGFLOW_USE_DOCKER=true to use Docker")
            self.logger.info("Langflow auto-start skipped - will try to connect to existing instance")
            return

        try:
            # Build command
            cmd_parts = self._config.langflow_command.split()
            cmd = cmd_parts + [
                "run",
                "--host", self._config.langflow_host,
                "--port", str(self._config.langflow_port),
            ]

            self.logger.info(f"Starting Langflow: {' '.join(cmd)}")

            # Start Langflow as subprocess
            self._langflow_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )

            # Wait for Langflow to be ready
            self._wait_for_langflow()

        except Exception as e:
            self.logger.error(f"Failed to start Langflow: {e}")
            self.logger.info("You can start Langflow manually: langflow run")

    def _is_langflow_running(self) -> bool:
        """Check if Langflow is already running."""
        try:
            response = httpx.get(
                f"{self._config.langflow_url}/health",
                timeout=2.0
            )
            return response.status_code == 200
        except Exception:
            return False

    def _wait_for_langflow(self) -> None:
        """Wait for Langflow to be ready."""
        start_time = time.time()
        timeout = self._config.startup_timeout

        self.logger.info(f"Waiting for Langflow to start (timeout: {timeout}s)...")

        while time.time() - start_time < timeout:
            if self._langflow_process and self._langflow_process.poll() is not None:
                # Process exited
                stderr = self._langflow_process.stderr.read().decode() if self._langflow_process.stderr else ""
                self.logger.error(f"Langflow process exited unexpectedly: {stderr[:500]}")
                self._langflow_process = None
                return

            if self._is_langflow_running():
                self.logger.info(f"Langflow started successfully at {self._config.langflow_url}")
                return

            time.sleep(1)

        self.logger.warning(f"Langflow did not start within {timeout}s")
        self.logger.info("Langflow may still be starting in the background")

    def shutdown(self) -> None:
        """Shutdown the plugin."""
        super().shutdown()

        # Stop Docker container if we started one
        if self._docker_container:
            self.logger.info(f"Stopping Langflow Docker container: {self._docker_container}")
            try:
                subprocess.run(
                    ["docker", "stop", self._docker_container],
                    capture_output=True,
                    timeout=30
                )
                subprocess.run(
                    ["docker", "rm", self._docker_container],
                    capture_output=True,
                    timeout=10
                )
                self._docker_container = None
                self.logger.info("Langflow Docker container stopped")
            except Exception as e:
                self.logger.error(f"Error stopping Langflow Docker container: {e}")

        # Stop native subprocess if we started one
        if self._langflow_process:
            self.logger.info("Stopping Langflow subprocess...")
            try:
                self._langflow_process.terminate()
                try:
                    self._langflow_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.logger.warning("Langflow did not stop gracefully, killing...")
                    self._langflow_process.kill()
                self._langflow_process = None
                self.logger.info("Langflow stopped")
            except Exception as e:
                self.logger.error(f"Error stopping Langflow: {e}")

        self.logger.info("Langflow plugin shutdown complete")

    def register_routes(self, app: FastAPI) -> None:
        """Register API routes with FastAPI app."""
        from plugins.langflow.routes import router

        app.include_router(
            router,
            prefix="/api/v1/plugins/langflow",
            tags=["Langflow"],
        )
        self.logger.info("Langflow API routes registered")

    def register_admin_routes(self, app: FastAPI) -> None:
        """Register admin UI routes."""
        from plugins.langflow.admin_routes import router

        app.include_router(
            router,
            prefix="/admin/langflow",
            tags=["Langflow Admin"],
        )
        self.logger.info("Langflow admin routes registered")

    def register_models(self) -> List[Any]:
        """
        Register database models.

        Langflow plugin has no database models - all data lives in Langflow.
        """
        return []

    def register_events(self) -> None:
        """Register event listeners."""
        # No events needed for this plugin
        pass

    def get_config_schema(self) -> Optional[Any]:
        """Return configuration schema."""
        from plugins.langflow.config import LangflowConfig

        return LangflowConfig

    def get_info(self) -> Dict[str, Any]:
        """Get plugin information with additional details."""
        info = super().get_info()
        info["features"] = [
            "Visual workflow builder",
            "50+ AI integrations",
            "Real-time streaming",
            "No additional dependencies",
        ]
        return info
