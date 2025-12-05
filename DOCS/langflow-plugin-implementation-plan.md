# Langflow Plugin Implementation Plan

## Overview

This document outlines the complete implementation plan for replacing the custom LangGraph visual workflow builder plugin with a lightweight **Langflow integration plugin**. This follows the Unix philosophy: **do one thing well** - FastCMS handles backend/data, Langflow handles AI workflows.

---

## Why Replace LangGraph with Langflow?

### Current LangGraph Plugin (To Be Removed)

| Aspect | Current State |
|--------|--------------|
| **Lines of Code** | ~1,655 lines of Python |
| **Database Tables** | 5 tables (workflows, nodes, edges, executions, checkpoints) |
| **API Endpoints** | 14+ endpoints |
| **Node Types** | 8 custom node types |
| **Dependencies** | Heavy (langgraph, langchain, torch, transformers, faiss-cpu) |
| **Maintenance** | High - custom visual editor, execution engine |

### Langflow Alternative

| Aspect | Langflow |
|--------|----------|
| **Community** | 138K+ GitHub stars, production-ready |
| **Features** | 50+ integrations, polished UI, better UX |
| **API** | Full REST API at `/api/v1/run/{flow_id}` with streaming |
| **Deployment** | Self-hosted (Docker, pip) or cloud |
| **Maintenance** | Zero - just API wrapper (~200 lines) |

### Benefits

1. **90% less code to maintain** - Just API proxy instead of full workflow engine
2. **Better UI/UX** - Dedicated team focused on visual builder
3. **More integrations** - 50+ vs custom implementation
4. **Smaller footprint** - Remove heavy AI dependencies from FastCMS core
5. **Faster updates** - Langflow community adds features constantly
6. **Battle-tested** - Used by thousands in production

---

## Files to Remove

### LangGraph Plugin Directory
```
plugins/langgraph/                        # DELETE ENTIRE DIRECTORY
├── __init__.py
├── plugin.py                             # ~70 lines
├── config.py                             # ~35 lines
├── models.py                             # ~156 lines (5 database models)
├── schemas.py                            # ~218 lines
├── routes.py                             # ~760 lines (14+ endpoints)
├── admin_routes.py                       # ~101 lines
├── executor.py                           # ~305 lines
├── langgraph_integration/
│   ├── __init__.py
│   └── code_generator.py                 # ~385 lines
├── templates/
│   ├── workflows.html
│   └── visual_editor.html
├── README.md
└── __pycache__/                          # DELETE
```

### Migrations to Remove
```
migrations/versions/
├── 20251202_1059_57ded8edb60e_add_langgraph_plugin_tables.py    # DELETE
└── 20251203_1055_57348398da9a_add_langgraph_integration_support.py  # DELETE
```

### Tests to Remove/Update
```
tests/integration/
└── test_langgraph_e2e.py                 # DELETE (replace with Langflow tests)
```

### Documentation to Remove
```
DOCS/
├── langgraph-plugin.md                   # DELETE
├── langgraph-api-reference.md            # DELETE
└── langgraph-plugin-plan.md              # DELETE
```

---

## Database Migration Strategy

### Option A: Create Downgrade Migration (Recommended for Development)
Since this is development and the LangGraph tables have minimal data, create a migration that drops all LangGraph tables.

### Option B: Manual Table Cleanup
For existing installations, provide SQL to drop tables:
```sql
DROP TABLE IF EXISTS langgraph_checkpoints;
DROP TABLE IF EXISTS langgraph_executions;
DROP TABLE IF EXISTS langgraph_edges;
DROP TABLE IF EXISTS langgraph_nodes;
DROP TABLE IF EXISTS langgraph_workflows;
```

### Migration Chain Fix
After removing LangGraph migrations:
1. The latest migration will be `20251123_2048_fb06c7171ada_add_collection_to_oauth.py`
2. New Langflow migration (if needed) will reference this

---

## New Langflow Plugin Architecture

### Design Principles

1. **Minimal footprint** - Only API proxy, no custom logic
2. **No database tables** - Just configuration in settings
3. **Stateless** - All state lives in Langflow
4. **Secure** - API key stored in environment/settings
5. **Extensible** - Easy to add FastCMS collection bridges later

### Directory Structure

```
plugins/langflow/
├── __init__.py                           # Package init
├── plugin.py                             # LangflowPlugin class (~50 lines)
├── config.py                             # Configuration schema (~30 lines)
├── routes.py                             # API proxy routes (~100 lines)
├── admin_routes.py                       # Admin UI routes (~50 lines)
├── schemas.py                            # Request/response schemas (~40 lines)
├── client.py                             # Langflow HTTP client (~80 lines)
├── templates/
│   └── langflow.html                     # Admin page with iframe/links
└── README.md                             # Plugin documentation
```

**Total: ~350 lines** (vs 1,655 for LangGraph)

### Plugin Configuration

```python
# config.py
from pydantic import BaseModel, Field

class LangflowConfig(BaseModel):
    """Langflow plugin configuration."""

    # Connection settings
    langflow_url: str = Field(
        default="http://localhost:7860",
        description="Langflow server URL"
    )
    api_key: str = Field(
        default="",
        description="Langflow API key (x-api-key header)"
    )

    # Feature flags
    embed_ui: bool = Field(
        default=True,
        description="Embed Langflow UI in admin (iframe)"
    )
    proxy_api: bool = Field(
        default=True,
        description="Proxy Langflow API through FastCMS"
    )

    # Timeouts
    request_timeout: int = Field(
        default=300,
        description="Request timeout in seconds"
    )
```

### Plugin Class

```python
# plugin.py
from app.core.plugin import BasePlugin
from fastapi import FastAPI

class LangflowPlugin(BasePlugin):
    """Langflow integration plugin for FastCMS."""

    name = "langflow"
    display_name = "Langflow"
    description = "Visual AI workflow builder powered by Langflow"
    version = "1.0.0"
    author = "FastCMS Team"

    # No Python dependencies - just HTTP client (httpx already in FastCMS)
    depends_on = []

    def initialize(self) -> None:
        """Initialize plugin."""
        super().initialize()
        self.logger.info("Langflow plugin initialized")

    def register_routes(self, app: FastAPI) -> None:
        """Register API routes."""
        from plugins.langflow.routes import router
        app.include_router(
            router,
            prefix="/api/v1/plugins/langflow",
            tags=["Langflow"]
        )

    def register_admin_routes(self, app: FastAPI) -> None:
        """Register admin UI routes."""
        from plugins.langflow.admin_routes import router
        app.include_router(
            router,
            prefix="/admin/langflow",
            tags=["Langflow Admin"]
        )

    def register_models(self):
        """No database models needed."""
        return []

    def get_config_schema(self):
        """Return configuration schema."""
        from plugins.langflow.config import LangflowConfig
        return LangflowConfig
```

### API Routes (Proxy)

```python
# routes.py
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from app.core.dependencies import get_current_user
from plugins.langflow.client import LangflowClient
from plugins.langflow.schemas import FlowExecuteRequest, FlowExecuteResponse

router = APIRouter()

def get_langflow_client() -> LangflowClient:
    """Get configured Langflow client."""
    from app.services.settings_service import SettingsService
    settings = SettingsService.get_plugin_settings("langflow")
    return LangflowClient(
        base_url=settings.get("langflow_url", "http://localhost:7860"),
        api_key=settings.get("api_key", "")
    )

@router.get("/health")
async def health_check(
    client: LangflowClient = Depends(get_langflow_client)
):
    """Check Langflow connection."""
    return await client.health_check()

@router.get("/flows")
async def list_flows(
    user = Depends(get_current_user),
    client: LangflowClient = Depends(get_langflow_client)
):
    """List all Langflow flows."""
    return await client.list_flows()

@router.get("/flows/{flow_id}")
async def get_flow(
    flow_id: str,
    user = Depends(get_current_user),
    client: LangflowClient = Depends(get_langflow_client)
):
    """Get flow details."""
    return await client.get_flow(flow_id)

@router.post("/flows/{flow_id}/run")
async def run_flow(
    flow_id: str,
    request: FlowExecuteRequest,
    user = Depends(get_current_user),
    client: LangflowClient = Depends(get_langflow_client)
):
    """Execute a Langflow flow."""
    return await client.run_flow(flow_id, request.input_value, request.tweaks)

@router.post("/flows/{flow_id}/run/stream")
async def run_flow_stream(
    flow_id: str,
    request: FlowExecuteRequest,
    user = Depends(get_current_user),
    client: LangflowClient = Depends(get_langflow_client)
):
    """Execute flow with streaming response."""
    async def generate():
        async for chunk in client.run_flow_stream(flow_id, request.input_value):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

### HTTP Client

```python
# client.py
import httpx
from typing import Any, AsyncIterator, Dict, Optional

class LangflowClient:
    """HTTP client for Langflow API."""

    def __init__(self, base_url: str, api_key: str = "", timeout: int = 300):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    async def health_check(self) -> Dict[str, Any]:
        """Check Langflow health."""
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/health",
                    headers=self._get_headers()
                )
                return {"status": "connected", "langflow_url": self.base_url}
            except Exception as e:
                return {"status": "disconnected", "error": str(e)}

    async def list_flows(self) -> Dict[str, Any]:
        """List all flows."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/flows",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def get_flow(self, flow_id: str) -> Dict[str, Any]:
        """Get flow by ID."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/flows/{flow_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def run_flow(
        self,
        flow_id: str,
        input_value: str,
        tweaks: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute a flow."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {"input_value": input_value}
            if tweaks:
                payload["tweaks"] = tweaks

            response = await client.post(
                f"{self.base_url}/api/v1/run/{flow_id}",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def run_flow_stream(
        self,
        flow_id: str,
        input_value: str
    ) -> AsyncIterator[str]:
        """Execute flow with streaming."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/v1/run/{flow_id}?stream=true",
                headers=self._get_headers(),
                json={"input_value": input_value}
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        yield line
```

### Admin Routes

```python
# admin_routes.py
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.dependencies import get_current_admin_user

router = APIRouter()
templates = Jinja2Templates(directory="plugins/langflow/templates")

@router.get("/", response_class=HTMLResponse)
async def langflow_admin(
    request: Request,
    user = Depends(get_current_admin_user)
):
    """Langflow admin page."""
    from app.services.settings_service import SettingsService
    settings = SettingsService.get_plugin_settings("langflow")

    return templates.TemplateResponse(
        "langflow.html",
        {
            "request": request,
            "user": user,
            "langflow_url": settings.get("langflow_url", "http://localhost:7860"),
            "embed_ui": settings.get("embed_ui", True)
        }
    )
```

### Admin Template

```html
<!-- templates/langflow.html -->
{% extends "admin/base.html" %}

{% block title %}Langflow - AI Workflows{% endblock %}

{% block content %}
<div class="p-6">
    <div class="mb-6">
        <h1 class="text-2xl font-bold text-gray-900">Langflow - AI Workflows</h1>
        <p class="text-gray-600 mt-1">
            Build and manage AI workflows using Langflow's visual editor.
        </p>
    </div>

    <!-- Connection Status -->
    <div id="connection-status" class="mb-6 p-4 rounded-lg bg-gray-50">
        <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
                <div id="status-indicator" class="w-3 h-3 rounded-full bg-gray-400"></div>
                <span id="status-text" class="text-sm text-gray-600">Checking connection...</span>
            </div>
            <a href="{{ langflow_url }}" target="_blank"
               class="text-sm text-blue-600 hover:text-blue-800">
                Open Langflow <i class="fas fa-external-link-alt ml-1"></i>
            </a>
        </div>
    </div>

    {% if embed_ui %}
    <!-- Embedded Langflow UI -->
    <div class="bg-white rounded-lg shadow-sm border overflow-hidden" style="height: calc(100vh - 250px);">
        <iframe
            src="{{ langflow_url }}"
            class="w-full h-full border-0"
            title="Langflow Editor"
            allow="clipboard-read; clipboard-write"
        ></iframe>
    </div>
    {% else %}
    <!-- Link to Langflow -->
    <div class="bg-white rounded-lg shadow-sm border p-8 text-center">
        <div class="max-w-md mx-auto">
            <div class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <i class="fas fa-project-diagram text-2xl text-blue-600"></i>
            </div>
            <h2 class="text-xl font-semibold mb-2">Langflow Visual Editor</h2>
            <p class="text-gray-600 mb-6">
                Create powerful AI workflows with drag-and-drop simplicity.
            </p>
            <a href="{{ langflow_url }}" target="_blank"
               class="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                <i class="fas fa-external-link-alt mr-2"></i>
                Open Langflow Editor
            </a>
        </div>
    </div>
    {% endif %}
</div>

<script>
// Check connection status
async function checkConnection() {
    try {
        const response = await fetch('/api/v1/plugins/langflow/health', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        const data = await response.json();

        const indicator = document.getElementById('status-indicator');
        const text = document.getElementById('status-text');

        if (data.status === 'connected') {
            indicator.classList.remove('bg-gray-400', 'bg-red-500');
            indicator.classList.add('bg-green-500');
            text.textContent = 'Connected to Langflow';
            text.classList.remove('text-gray-600', 'text-red-600');
            text.classList.add('text-green-600');
        } else {
            indicator.classList.remove('bg-gray-400', 'bg-green-500');
            indicator.classList.add('bg-red-500');
            text.textContent = 'Disconnected - ' + (data.error || 'Check Langflow server');
            text.classList.remove('text-gray-600', 'text-green-600');
            text.classList.add('text-red-600');
        }
    } catch (error) {
        console.error('Connection check failed:', error);
    }
}

// Check on load and every 30 seconds
checkConnection();
setInterval(checkConnection, 30000);
</script>
{% endblock %}
```

---

## Deployment Architecture

### Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  fastcms:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LANGFLOW_URL=http://langflow:7860
      - LANGFLOW_API_KEY=${LANGFLOW_API_KEY:-}
    depends_on:
      - langflow
    volumes:
      - ./data:/app/data

  langflow:
    image: langflowai/langflow:latest
    ports:
      - "7860:7860"
    environment:
      - LANGFLOW_AUTO_LOGIN=true
    volumes:
      - langflow_data:/app/langflow

volumes:
  langflow_data:
```

### Environment Variables

```bash
# .env

# Langflow connection
LANGFLOW_URL=http://localhost:7860
LANGFLOW_API_KEY=your-api-key-here

# Optional settings
LANGFLOW_EMBED_UI=true
LANGFLOW_PROXY_API=true
LANGFLOW_REQUEST_TIMEOUT=300
```

---

## Implementation Steps

### Phase 1: Cleanup (Remove LangGraph)

1. **Delete LangGraph plugin directory**
   ```bash
   rm -rf plugins/langgraph/
   ```

2. **Delete LangGraph migrations**
   ```bash
   rm migrations/versions/20251202_1059_57ded8edb60e_add_langgraph_plugin_tables.py
   rm migrations/versions/20251203_1055_57348398da9a_add_langgraph_integration_support.py
   ```

3. **Delete LangGraph e2e test**
   ```bash
   rm tests/integration/test_langgraph_e2e.py
   ```

4. **Delete LangGraph documentation**
   ```bash
   rm DOCS/langgraph-plugin.md
   rm DOCS/langgraph-api-reference.md
   rm DOCS/langgraph-plugin-plan.md
   ```

5. **Create migration to drop tables** (for existing installations)
   ```python
   # migrations/versions/YYYYMMDD_HHMM_drop_langgraph_tables.py
   def upgrade():
       op.drop_table("langgraph_checkpoints")
       op.drop_table("langgraph_executions")
       op.drop_table("langgraph_edges")
       op.drop_table("langgraph_nodes")
       op.drop_table("langgraph_workflows")
   ```

### Phase 2: Create Langflow Plugin

1. **Create plugin directory structure**
   ```bash
   mkdir -p plugins/langflow/templates
   ```

2. **Create plugin files**
   - `__init__.py`
   - `plugin.py`
   - `config.py`
   - `client.py`
   - `routes.py`
   - `admin_routes.py`
   - `schemas.py`
   - `templates/langflow.html`
   - `README.md`

3. **Test plugin loading**
   ```bash
   python -c "from plugins.langflow.plugin import LangflowPlugin; print(LangflowPlugin().get_info())"
   ```

### Phase 3: Update Documentation

1. **Create new documentation**
   - `DOCS/langflow-plugin.md` - User guide
   - Update `DOCS/plugins.md` - Plugin list

2. **Update README.md**
   - Update plugin section
   - Add Langflow deployment instructions

### Phase 4: Create Tests

1. **Create Langflow e2e test**
   - `tests/integration/test_langflow_e2e.py`
   - Test health check
   - Test flow listing (mocked)
   - Test flow execution (mocked)

### Phase 5: Final Cleanup

1. **Run tests**
   ```bash
   pytest tests/ -v
   ```

2. **Verify no LangGraph references remain**
   ```bash
   grep -r "langgraph" . --include="*.py" --exclude-dir=".venv"
   ```

3. **Clean up any orphaned imports**

---

## API Comparison

### LangGraph Plugin (Removed)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/workflows` | POST | Create workflow |
| `/workflows` | GET | List workflows |
| `/workflows/{id}` | GET | Get workflow |
| `/workflows/{id}` | PUT | Update workflow |
| `/workflows/{id}` | DELETE | Delete workflow |
| `/workflows/{id}/nodes` | POST | Create node |
| `/workflows/{id}/nodes` | GET | List nodes |
| `/workflows/{id}/edges` | POST | Create edge |
| `/workflows/{id}/edges` | GET | List edges |
| `/workflows/{id}/execute` | POST | Execute workflow |
| `/workflows/{id}/execute/stream` | POST | Execute with streaming |
| `/workflows/{id}/executions` | GET | List executions |
| `/templates` | GET | List templates |

### Langflow Plugin (New)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Check Langflow connection |
| `/flows` | GET | List flows (proxy) |
| `/flows/{id}` | GET | Get flow details (proxy) |
| `/flows/{id}/run` | POST | Execute flow (proxy) |
| `/flows/{id}/run/stream` | POST | Execute with streaming (proxy) |

**Key difference**: 5 endpoints vs 14+ endpoints. All workflow management happens in Langflow.

---

## Security Considerations

1. **API Key Storage**
   - Store in environment variables or settings
   - Never expose in logs or responses

2. **Request Validation**
   - Validate all proxy requests
   - Sanitize input before forwarding

3. **Rate Limiting**
   - Apply FastCMS rate limits to Langflow proxy
   - Respect Langflow's own rate limits

4. **Authentication**
   - All endpoints require FastCMS authentication
   - API key for Langflow stored server-side

5. **CORS**
   - Configure Langflow CORS for iframe embedding
   - Or use proxy mode only

---

## Future Enhancements

1. **FastCMS Collection Bridge**
   - Allow Langflow flows to read/write FastCMS collections
   - Custom Langflow component for FastCMS data

2. **Flow Registry**
   - Store flow references in FastCMS settings
   - Map flows to FastCMS features (webhooks, automation)

3. **Embedded Execution Results**
   - Show flow execution history in FastCMS
   - Link results to FastCMS records

4. **Multi-tenant Support**
   - Per-user Langflow projects
   - Access control for flows

---

## Testing Strategy

### Unit Tests

```python
# tests/unit/test_langflow_client.py
import pytest
from unittest.mock import AsyncMock, patch
from plugins.langflow.client import LangflowClient

@pytest.mark.asyncio
async def test_health_check_connected():
    client = LangflowClient("http://localhost:7860")
    with patch("httpx.AsyncClient") as mock:
        mock.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=AsyncMock(status_code=200)
        )
        result = await client.health_check()
        assert result["status"] == "connected"

@pytest.mark.asyncio
async def test_health_check_disconnected():
    client = LangflowClient("http://localhost:7860")
    with patch("httpx.AsyncClient") as mock:
        mock.return_value.__aenter__.return_value.get = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        result = await client.health_check()
        assert result["status"] == "disconnected"
```

### Integration Tests

```python
# tests/integration/test_langflow_e2e.py
import pytest
import httpx

BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_langflow_health_endpoint():
    async with httpx.AsyncClient() as client:
        # Login first
        login_response = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": "admin@fastcms.dev", "password": "admin"}
        )
        token = login_response.json()["access_token"]

        # Check health
        response = await client.get(
            f"{BASE_URL}/api/v1/plugins/langflow/health",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
```

---

## Summary

| Aspect | Before (LangGraph) | After (Langflow) |
|--------|-------------------|------------------|
| **Lines of Code** | ~1,655 | ~350 |
| **Database Tables** | 5 | 0 |
| **API Endpoints** | 14+ | 5 |
| **Dependencies** | Heavy | None (uses httpx) |
| **Maintenance** | High | Minimal |
| **UI Quality** | Custom Rete.js | Polished Langflow |
| **Features** | Limited | 50+ integrations |

This implementation plan provides a complete roadmap for replacing the custom LangGraph plugin with a lightweight Langflow integration, significantly reducing complexity while improving capabilities.
