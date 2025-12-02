"""
Plugin manager for FastCMS.

Handles plugin discovery, registration, and lifecycle management.
"""

import importlib
import logging
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI

from app.core.plugin import BasePlugin

logger = logging.getLogger(__name__)


class PluginManager:
    """Manages all plugins in the system."""

    def __init__(self):
        """Initialize the plugin manager."""
        self.plugins: Dict[str, BasePlugin] = {}
        self._initialized = False

    def discover_plugins(self, plugins_dir: str = "plugins") -> List[str]:
        """
        Discover plugins in the plugins directory.

        Args:
            plugins_dir: Path to plugins directory

        Returns:
            List of discovered plugin names
        """
        plugins_path = Path(plugins_dir)

        if not plugins_path.exists():
            logger.warning(f"Plugins directory not found: {plugins_path}")
            plugins_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created plugins directory: {plugins_path}")
            return []

        discovered = []

        for plugin_dir in plugins_path.iterdir():
            if not plugin_dir.is_dir():
                continue

            if plugin_dir.name.startswith("_") or plugin_dir.name.startswith("."):
                continue

            # Check if plugin.py exists
            plugin_file = plugin_dir / "plugin.py"
            if not plugin_file.exists():
                logger.debug(f"Skipping {plugin_dir.name}: no plugin.py found")
                continue

            discovered.append(plugin_dir.name)

        logger.info(f"Discovered {len(discovered)} plugins: {discovered}")
        return discovered

    def load_plugin(self, plugin_name: str, plugins_dir: str = "plugins") -> Optional[BasePlugin]:
        """
        Load a single plugin.

        Args:
            plugin_name: Name of the plugin directory
            plugins_dir: Path to plugins directory

        Returns:
            Plugin instance or None if loading failed
        """
        try:
            # Import plugin module
            module_path = f"{plugins_dir}.{plugin_name}.plugin"
            module = importlib.import_module(module_path)

            # Find plugin class (should inherit from BasePlugin)
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BasePlugin)
                    and attr is not BasePlugin
                ):
                    plugin_class = attr
                    break

            if not plugin_class:
                logger.error(f"No plugin class found in {module_path}")
                return None

            # Instantiate plugin
            plugin = plugin_class()
            logger.info(f"Loaded plugin: {plugin.display_name} v{plugin.version}")
            return plugin

        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}", exc_info=True)
            return None

    def register_plugin(self, plugin: BasePlugin) -> bool:
        """
        Register a plugin.

        Args:
            plugin: Plugin instance

        Returns:
            True if registered successfully
        """
        if plugin.name in self.plugins:
            logger.warning(f"Plugin {plugin.name} already registered")
            return False

        self.plugins[plugin.name] = plugin
        logger.info(f"Registered plugin: {plugin.display_name}")
        return True

    def initialize_plugins(self, app: FastAPI) -> None:
        """
        Initialize all registered plugins.

        Args:
            app: FastAPI application instance
        """
        if self._initialized:
            logger.warning("Plugins already initialized")
            return

        logger.info(f"Initializing {len(self.plugins)} plugins...")

        for plugin_name, plugin in self.plugins.items():
            try:
                if not plugin.enabled:
                    logger.info(f"Skipping disabled plugin: {plugin.display_name}")
                    continue

                # Initialize plugin
                plugin.initialize()

                # Register routes
                plugin.register_routes(app)

                # Register admin routes
                plugin.register_admin_routes(app)

                # Register models
                models = plugin.register_models()
                if models:
                    logger.info(f"Plugin {plugin.display_name} registered {len(models)} models")

                # Register events
                plugin.register_events()

                logger.info(f"✅ Plugin {plugin.display_name} initialized successfully")

            except Exception as e:
                logger.error(f"Failed to initialize plugin {plugin_name}: {e}", exc_info=True)
                plugin.disable()

        self._initialized = True
        logger.info("All plugins initialized")

    def shutdown_plugins(self) -> None:
        """Shutdown all plugins."""
        logger.info("Shutting down plugins...")

        for plugin_name, plugin in self.plugins.items():
            try:
                plugin.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down plugin {plugin_name}: {e}", exc_info=True)

        logger.info("All plugins shut down")

    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """
        Get a plugin by name.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Plugin instance or None
        """
        return self.plugins.get(plugin_name)

    def list_plugins(self) -> List[Dict]:
        """
        List all registered plugins.

        Returns:
            List of plugin information dictionaries
        """
        return [plugin.get_info() for plugin in self.plugins.values()]

    def enable_plugin(self, plugin_name: str) -> bool:
        """
        Enable a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            True if enabled successfully
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            logger.error(f"Plugin {plugin_name} not found")
            return False

        plugin.enable()
        return True

    def disable_plugin(self, plugin_name: str) -> bool:
        """
        Disable a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            True if disabled successfully
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            logger.error(f"Plugin {plugin_name} not found")
            return False

        plugin.disable()
        return True


# Global plugin manager instance
plugin_manager = PluginManager()
