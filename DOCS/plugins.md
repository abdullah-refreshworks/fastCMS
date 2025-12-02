# FastCMS Plugin System

FastCMS features a powerful plugin system that allows you to extend functionality without modifying the core codebase. Plugins can add new features, integrate external services, provide custom UI components, and much more.

## Table of Contents

- [Overview](#overview)
- [Plugin Architecture](#plugin-architecture)
- [Plugin Structure](#plugin-structure)
- [Plugin Lifecycle](#plugin-lifecycle)
- [Core Plugin APIs](#core-plugin-apis)
- [Plugin Installation](#plugin-installation)
- [Creating Your First Plugin](#creating-your-first-plugin)
- [Official Plugins](#official-plugins)

---

## Overview

### What is a Plugin?

A plugin is a self-contained module that extends FastCMS functionality. Plugins can:

- **Add API Endpoints**: Create new REST API routes
- **Extend Admin UI**: Add new pages, components, and navigation items
- **Register Database Models**: Create custom tables and relationships
- **Provide Background Tasks**: Schedule jobs and process data
- **Integrate External Services**: Connect to third-party APIs
- **Add Custom Field Types**: Extend collection schemas
- **Hook into Events**: React to system events (record creation, user login, etc.)

### Why Plugins?

- **Modularity**: Keep core clean, add features as needed
- **Reusability**: Share plugins across projects
- **Maintainability**: Update plugins independently
- **Community**: Build and share with the FastCMS ecosystem

---

## Plugin Architecture

### Design Principles

1. **Zero Core Modification**: Plugins never modify core files
2. **Self-Contained**: All plugin code lives in plugin directory
3. **Discoverable**: Plugins register themselves automatically
4. **Configurable**: Each plugin has its own settings
5. **Hot-Pluggable**: Enable/disable without restart (where possible)

### Plugin System Components

```
┌──────────────────────────────────────┐
│         FastCMS Core                 │
│  ┌────────────────────────────────┐  │
│  │   Plugin Manager               │  │
│  │  - Discovery                   │  │
│  │  - Registration                │  │
│  │  - Lifecycle Management        │  │
│  └────────────────────────────────┘  │
│              ▲                        │
│              │                        │
│  ┌───────────┴──────────────┐        │
│  │   Plugin Registry         │        │
│  │  {                        │        │
│  │    "langgraph": Plugin1   │        │
│  │    "analytics": Plugin2   │        │
│  │  }                        │        │
│  └───────────────────────────┘        │
└──────────────────────────────────────┘
              │
              │ Loads
              ▼
┌──────────────────────────────────────┐
│          Plugins Directory            │
│                                      │
│  plugins/                            │
│  ├── langgraph/                      │
│  │   ├── __init__.py                │
│  │   ├── plugin.py                  │
│  │   ├── routes.py                  │
│  │   ├── models.py                  │
│  │   └── frontend/                  │
│  │                                  │
│  └── analytics/                      │
│      ├── __init__.py                │
│      └── plugin.py                  │
└──────────────────────────────────────┘
```

---

## Plugin Structure

### Directory Layout

Each plugin follows a standard structure:

```
plugins/
└── my_plugin/
    ├── __init__.py           # Plugin entry point
    ├── plugin.py             # Plugin class definition
    ├── config.py             # Plugin configuration
    ├── routes.py             # API endpoints (optional)
    ├── admin_routes.py       # Admin UI routes (optional)
    ├── models.py             # Database models (optional)
    ├── schemas.py            # Pydantic schemas (optional)
    ├── services.py           # Business logic (optional)
    ├── tasks.py              # Background tasks (optional)
    ├── frontend/             # Frontend assets (optional)
    │   ├── components/       # React/Vue components
    │   ├── pages/            # Full page views
    │   └── styles/           # CSS files
    ├── templates/            # Jinja2 templates (optional)
    ├── static/               # Static files (optional)
    ├── migrations/           # Database migrations (optional)
    ├── requirements.txt      # Plugin dependencies
    └── README.md             # Plugin documentation
```

### Minimal Plugin

The simplest plugin requires just two files:

**`plugins/my_plugin/__init__.py`:**
```python
from .plugin import MyPlugin

__version__ = "0.1.0"
__all__ = ["MyPlugin"]
```

**`plugins/my_plugin/plugin.py`:**
```python
from app.core.plugin import BasePlugin

class MyPlugin(BasePlugin):
    """My custom plugin."""

    name = "my_plugin"
    display_name = "My Plugin"
    description = "A simple example plugin"
    version = "0.1.0"
    author = "Your Name"

    def initialize(self):
        """Called when plugin is loaded."""
        self.logger.info(f"{self.display_name} initialized")
```

---

## Plugin Lifecycle

### 1. Discovery

On startup, FastCMS scans the `plugins/` directory:

```python
# Automatic discovery
plugins_dir = Path("plugins")
for plugin_dir in plugins_dir.iterdir():
    if plugin_dir.is_dir() and (plugin_dir / "plugin.py").exists():
        # Load plugin
        pass
```

### 2. Registration

Plugins register themselves with the Plugin Manager:

```python
class PluginManager:
    def register(self, plugin_class):
        """Register a plugin class."""
        plugin = plugin_class()
        self.plugins[plugin.name] = plugin
```

### 3. Initialization

After registration, plugins are initialized:

```python
# Plugin lifecycle
plugin.initialize()        # Setup
plugin.register_routes()   # Add API routes
plugin.register_models()   # Register DB models
plugin.register_admin()    # Add admin UI
```

### 4. Running

Plugin is active and handling requests.

### 5. Shutdown

Clean shutdown when app stops:

```python
plugin.shutdown()  # Cleanup resources
```

---

## Core Plugin APIs

### BasePlugin Class

All plugins inherit from `BasePlugin`:

```python
class BasePlugin:
    """Base class for all plugins."""

    # Metadata (required)
    name: str              # Unique identifier
    display_name: str      # Human-readable name
    description: str       # Short description
    version: str           # Semantic version
    author: str            # Plugin author

    # Optional metadata
    homepage: str = ""     # Plugin website
    repository: str = ""   # Source code URL
    license: str = "MIT"   # License type

    # Dependencies
    requires: List[str] = []  # Required plugins
    depends_on: List[str] = []  # Python packages

    # Lifecycle hooks
    def initialize(self): pass
    def shutdown(self): pass

    # Feature registration
    def register_routes(self, app): pass
    def register_models(self): pass
    def register_admin(self, router): pass
    def register_events(self): pass

    # Utilities
    @property
    def logger(self): ...
    @property
    def config(self): ...
    @property
    def db(self): ...
```

### Plugin Configuration

Plugins can define configuration settings:

```python
class MyPlugin(BasePlugin):
    name = "my_plugin"

    def get_config_schema(self):
        """Return Pydantic model for settings."""
        from pydantic import BaseModel, Field

        class MyPluginConfig(BaseModel):
            api_key: str = Field(..., description="API key")
            timeout: int = Field(30, description="Request timeout")
            enabled: bool = Field(True, description="Enable feature")

        return MyPluginConfig
```

Configuration is stored in database and accessible via:

```python
# In plugin code
api_key = self.config.get("api_key")
timeout = self.config.get("timeout", default=30)
```

---

## Plugin Installation

### From Package (Recommended)

Install plugins via pip:

```bash
# Install from PyPI
pip install fastcms-plugin-langgraph

# Install from Git
pip install git+https://github.com/user/fastcms-plugin-name.git

# Install locally for development
cd plugins/my_plugin
pip install -e .
```

Plugin is automatically discovered on next startup.

### Manual Installation

Copy plugin directory to `plugins/`:

```bash
cp -r my_plugin plugins/
cd plugins/my_plugin
pip install -r requirements.txt
```

### Enable/Disable

Plugins can be enabled/disabled via admin UI or CLI:

```bash
# Via CLI
fastcms plugin enable my_plugin
fastcms plugin disable my_plugin

# Via Admin UI
Admin > Settings > Plugins > [Enable/Disable]
```

---

## Creating Your First Plugin

### Step 1: Create Plugin Directory

```bash
mkdir -p plugins/hello_world
cd plugins/hello_world
touch __init__.py plugin.py
```

### Step 2: Define Plugin Class

**`plugin.py`:**
```python
from app.core.plugin import BasePlugin
from fastapi import APIRouter

class HelloWorldPlugin(BasePlugin):
    name = "hello_world"
    display_name = "Hello World"
    description = "A simple greeting plugin"
    version = "1.0.0"
    author = "FastCMS Team"

    def initialize(self):
        self.logger.info("Hello World plugin initialized!")

    def register_routes(self, app):
        """Add custom API endpoint."""
        router = APIRouter()

        @router.get("/hello")
        async def hello():
            return {"message": "Hello from plugin!"}

        app.include_router(
            router,
            prefix="/api/v1/plugins/hello_world",
            tags=["Hello World Plugin"]
        )
```

### Step 3: Register Plugin

**`__init__.py`:**
```python
from .plugin import HelloWorldPlugin

__all__ = ["HelloWorldPlugin"]
```

### Step 4: Test

Restart FastCMS and visit:
```
http://localhost:8000/api/v1/plugins/hello_world/hello
```

---

## Official Plugins

### LangGraph Plugin

Visual workflow builder for AI agents using LangGraph.

**Features:**
- Drag-and-drop node editor
- Visual edge connections
- Built-in LangGraph nodes
- Real-time execution
- Workflow templates

[Learn more →](langgraph-plugin.md)

### Analytics Plugin

Track and analyze usage metrics.

**Features:**
- Page views tracking
- User activity monitoring
- Custom event logging
- Dashboard visualizations

### Export Plugin

Export data in multiple formats.

**Features:**
- PDF generation
- Excel export
- JSON/XML export
- Scheduled exports

---

## Best Practices

### 1. Use Semantic Versioning

```python
version = "1.2.3"  # MAJOR.MINOR.PATCH
```

### 2. Declare Dependencies

```python
class MyPlugin(BasePlugin):
    requires = ["other_plugin>=1.0.0"]
    depends_on = ["requests>=2.28.0", "pandas>=2.0.0"]
```

### 3. Handle Errors Gracefully

```python
def initialize(self):
    try:
        self.setup_external_service()
    except Exception as e:
        self.logger.error(f"Failed to initialize: {e}")
        raise  # Or handle gracefully
```

### 4. Clean Up Resources

```python
def shutdown(self):
    """Release resources."""
    if hasattr(self, 'connection'):
        self.connection.close()
```

### 5. Document Your Plugin

Provide clear README with:
- What the plugin does
- How to configure it
- Example usage
- API reference

---

## Plugin API Reference

See [Plugin Development Guide](plugin-development.md) for complete API documentation.

---

## Security Considerations

### Plugin Sandbox

Plugins run in the same process as FastCMS. Always:

1. **Validate Inputs**: Never trust plugin data
2. **Use Permissions**: Check user permissions
3. **Sanitize SQL**: Use ORM, never raw queries
4. **Limit Resources**: Avoid infinite loops, excessive memory
5. **Review Code**: Audit third-party plugins

### Trusted Plugins Only

Only install plugins from trusted sources. Malicious plugins can:
- Access database
- Read/write files
- Make network requests
- Execute arbitrary code

---

## Troubleshooting

### Plugin Not Found

```bash
# Check plugins directory
ls plugins/

# Verify plugin.py exists
ls plugins/my_plugin/plugin.py
```

### Import Errors

```bash
# Install plugin dependencies
cd plugins/my_plugin
pip install -r requirements.txt
```

### Plugin Disabled

Check admin UI: `Admin > Settings > Plugins`

Or check database:
```sql
SELECT * FROM plugin_settings WHERE name = 'my_plugin';
```

---

## Next Steps

- [Plugin Development Guide](plugin-development.md) - Deep dive into plugin development
- [LangGraph Plugin Spec](langgraph-plugin.md) - Build the LangGraph visual editor
- [Plugin Examples](https://github.com/fastcms/plugin-examples) - Example plugins to learn from

---

## Community

- **GitHub**: https://github.com/fastcms/fastcms
- **Plugins Registry**: https://fastcms.dev/plugins
- **Discord**: https://discord.gg/fastcms
- **Forum**: https://forum.fastcms.dev

---

## License

Plugin system is part of FastCMS core (MIT License). Individual plugins may have different licenses.
