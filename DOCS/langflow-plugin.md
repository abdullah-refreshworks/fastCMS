# Langflow Plugin - Visual AI Workflow Builder

The Langflow plugin integrates [Langflow](https://www.langflow.org/) with FastCMS, providing a powerful visual interface for building AI workflows without writing code.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Configuration](#configuration)
- [Admin Interface](#admin-interface)
- [API Reference](#api-reference)
- [Usage Examples](#usage-examples)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

---

## Overview

### What is Langflow?

Langflow is an open-source visual platform for building AI-powered workflows with 138K+ GitHub stars. It provides:

- **Visual Drag-and-Drop Builder** - Create AI workflows without coding
- **50+ Integrations** - OpenAI, Anthropic, Google, vector databases, tools
- **Real-time Streaming** - Token-by-token LLM output
- **Production Ready** - Battle-tested by thousands of users

### Why Langflow Integration?

Instead of building a custom workflow engine, FastCMS integrates with Langflow to provide:

| Benefit | Description |
|---------|-------------|
| **Better UI** | Professional visual editor maintained by dedicated team |
| **More Features** | 50+ integrations vs custom implementation |
| **Less Code** | ~350 lines vs 1,655 lines for custom solution |
| **Zero Dependencies** | No additional Python packages required |
| **Community Updates** | New features added constantly by Langflow team |

---

## Installation

### Prerequisites

1. FastCMS installed and running
2. Langflow instance (Docker, pip, or cloud)

### Step 1: Run Langflow

**Option A: Docker (Recommended)**

```bash
docker run -d -p 7860:7860 langflowai/langflow:latest
```

**Option B: pip**

```bash
pip install langflow
langflow run --port 7860
```

**Option C: Docker Compose with FastCMS**

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
    depends_on:
      - langflow

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

### Step 2: Configure FastCMS

Add to your `.env` file:

```bash
# Required: Langflow server URL
LANGFLOW_URL=http://localhost:7860

# Optional: API key for Langflow 1.5+
LANGFLOW_API_KEY=your-api-key

# Optional: Embed Langflow UI in admin (default: true)
LANGFLOW_EMBED_UI=true
```

### Step 3: Verify Connection

1. Start FastCMS
2. Navigate to `/admin/langflow`
3. Check the connection status indicator

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LANGFLOW_URL` | Langflow server URL | `http://localhost:7860` |
| `LANGFLOW_API_KEY` | API key for authentication | (empty) |
| `LANGFLOW_EMBED_UI` | Embed Langflow UI in admin | `true` |
| `LANGFLOW_PROXY_API` | Enable API proxy | `true` |
| `LANGFLOW_REQUEST_TIMEOUT` | Request timeout in seconds | `300` |

### Plugin Settings

The plugin configuration schema:

```python
class LangflowConfig:
    langflow_url: str       # Server URL
    api_key: str           # Authentication key
    embed_ui: bool         # Embed or link mode
    proxy_api: bool        # Enable API proxy
    request_timeout: int   # Timeout in seconds
```

---

## Admin Interface

Access the Langflow admin page at:

```
http://localhost:8000/admin/langflow
```

### Features

1. **Connection Status** - Real-time indicator showing Langflow connection health
2. **Embedded Editor** - Langflow UI embedded via iframe (if enabled)
3. **External Link** - Quick link to open Langflow in new tab
4. **Help Information** - API usage examples

### UI Modes

**Embedded Mode** (`LANGFLOW_EMBED_UI=true`)
- Langflow editor embedded directly in FastCMS admin
- Seamless user experience
- May require CORS configuration on Langflow

**Link Mode** (`LANGFLOW_EMBED_UI=false`)
- Shows link to external Langflow instance
- Feature cards explaining capabilities
- Works with any Langflow configuration

---

## API Reference

All endpoints require FastCMS authentication.

### Health Check

Check Langflow connection status.

```http
GET /api/v1/plugins/langflow/health
```

**Response:**
```json
{
  "status": "connected",
  "langflow_url": "http://localhost:7860"
}
```

### List Flows

Get all available Langflow flows.

```http
GET /api/v1/plugins/langflow/flows
Authorization: Bearer <token>
```

**Response:**
```json
{
  "flows": [
    {
      "id": "flow-uuid",
      "name": "My Chat Bot",
      "description": "Customer support chatbot"
    }
  ],
  "total": 1
}
```

### Get Flow

Get details of a specific flow.

```http
GET /api/v1/plugins/langflow/flows/{flow_id}
Authorization: Bearer <token>
```

### Execute Flow

Run a flow with input data.

```http
POST /api/v1/plugins/langflow/flows/{flow_id}/run
Authorization: Bearer <token>
Content-Type: application/json

{
  "input_value": "Hello, how can you help me?",
  "tweaks": {}
}
```

**Response:**
```json
{
  "outputs": [
    {
      "inputs": {...},
      "outputs": [
        {
          "results": {...},
          "messages": [...]
        }
      ]
    }
  ],
  "session_id": "session-uuid"
}
```

### Execute Flow with Streaming

Run a flow with Server-Sent Events streaming.

```http
POST /api/v1/plugins/langflow/flows/{flow_id}/run/stream
Authorization: Bearer <token>
Content-Type: application/json

{
  "input_value": "Explain quantum computing"
}
```

**Response (SSE):**
```
data: {"type": "token", "content": "Quantum"}
data: {"type": "token", "content": " computing"}
data: {"type": "token", "content": " is"}
...
data: {"type": "end"}
```

### List Projects

Get all Langflow projects.

```http
GET /api/v1/plugins/langflow/projects
Authorization: Bearer <token>
```

---

## Usage Examples

### JavaScript/Browser

```javascript
// Execute a flow
async function runFlow(flowId, input) {
  const response = await fetch(`/api/v1/plugins/langflow/flows/${flowId}/run`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ input_value: input })
  });
  return response.json();
}

// Execute with streaming
async function runFlowStream(flowId, input, onToken) {
  const response = await fetch(`/api/v1/plugins/langflow/flows/${flowId}/run/stream`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ input_value: input })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        onToken(data);
      }
    }
  }
}

// Usage
runFlowStream('flow-id', 'Hello!', (data) => {
  if (data.type === 'token') {
    console.log(data.content);
  }
});
```

### Python

```python
import httpx
import json

class FastCMSLangflowClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}

    async def run_flow(self, flow_id: str, input_value: str):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/plugins/langflow/flows/{flow_id}/run",
                headers=self.headers,
                json={"input_value": input_value},
                timeout=300
            )
            return response.json()

    async def run_flow_stream(self, flow_id: str, input_value: str):
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/v1/plugins/langflow/flows/{flow_id}/run/stream",
                headers=self.headers,
                json={"input_value": input_value},
                timeout=300
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        yield json.loads(line[6:])

# Usage
client = FastCMSLangflowClient("http://localhost:8000", "your-token")

# Blocking execution
result = await client.run_flow("flow-id", "Hello!")
print(result)

# Streaming execution
async for chunk in client.run_flow_stream("flow-id", "Hello!"):
    if chunk.get("type") == "token":
        print(chunk["content"], end="", flush=True)
```

### cURL

```bash
# Check health
curl http://localhost:8000/api/v1/plugins/langflow/health

# List flows
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/plugins/langflow/flows

# Run flow
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input_value": "Hello!"}' \
  http://localhost:8000/api/v1/plugins/langflow/flows/FLOW_ID/run
```

---

## Deployment

### Production Setup

1. **Use Docker Compose** for orchestrating both services
2. **Set API Keys** for production Langflow authentication
3. **Configure CORS** if embedding Langflow UI
4. **Use Reverse Proxy** (nginx) for SSL termination

### Example nginx Configuration

```nginx
server {
    listen 443 ssl;
    server_name cms.example.com;

    # FastCMS
    location / {
        proxy_pass http://fastcms:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Langflow (for embedded iframe)
    location /langflow/ {
        proxy_pass http://langflow:7860/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        # WebSocket support for Langflow
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Troubleshooting

### Connection Failed

**Symptoms:** "Disconnected" status in admin UI

**Solutions:**
1. Verify Langflow is running: `curl http://localhost:7860/health`
2. Check `LANGFLOW_URL` environment variable
3. Ensure network connectivity between services (if Docker)
4. Check Langflow logs for errors

### Iframe Not Loading

**Symptoms:** Empty iframe in admin UI

**Solutions:**
1. Langflow may block iframe embedding - use link mode instead
2. Set `LANGFLOW_EMBED_UI=false` in environment
3. Configure Langflow CORS settings if you control the instance

### Authentication Errors

**Symptoms:** 401/403 errors from Langflow

**Solutions:**
1. Generate API key in Langflow settings (1.5+)
2. Set `LANGFLOW_API_KEY` environment variable
3. Restart FastCMS to apply changes

### Timeout Errors

**Symptoms:** Requests timing out for long-running flows

**Solutions:**
1. Increase `LANGFLOW_REQUEST_TIMEOUT` (default: 300 seconds)
2. Use streaming endpoint for long-running flows
3. Optimize flow complexity in Langflow

---

## Security

### Authentication Flow

```
User → FastCMS Auth → Plugin Routes → Langflow API
         ↓                ↓
    JWT Token        API Key (x-api-key)
```

1. User authenticates with FastCMS
2. Plugin routes require FastCMS authentication
3. Plugin uses configured API key for Langflow

### Best Practices

1. **Never expose Langflow directly** - Always proxy through FastCMS
2. **Use API keys** - Enable authentication in Langflow 1.5+
3. **Limit network access** - Langflow should only be accessible from FastCMS
4. **Audit flow access** - FastCMS logs all API requests

---

## Resources

- [Langflow Documentation](https://docs.langflow.org/)
- [Langflow GitHub](https://github.com/langflow-ai/langflow)
- [FastCMS Plugin Development](plugin-development.md)
- [FastCMS Plugin System](plugins.md)
