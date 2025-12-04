# Langflow Integration Plugin

Visual AI workflow builder for FastCMS powered by [Langflow](https://www.langflow.org/).

## Overview

This plugin provides seamless integration with Langflow, a visual platform for building AI-powered workflows. Instead of building a custom workflow engine, FastCMS leverages Langflow's mature, battle-tested platform (138K+ GitHub stars).

## Features

- **Visual Workflow Builder** - Drag-and-drop interface for creating AI workflows
- **50+ Integrations** - OpenAI, Anthropic, Google, vector databases, and more
- **Real-time Streaming** - Token-by-token LLM output via SSE
- **Minimal Footprint** - Just API proxy, no additional dependencies
- **Embedded UI** - Langflow UI embedded in FastCMS admin (optional)

## Installation

The plugin is included with FastCMS. You need to run a Langflow instance separately.

### Option 1: Docker (Recommended)

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

### Option 2: Auto-Start with FastCMS (Default)

FastCMS can automatically start Langflow when the server starts:

```bash
# .env file
LANGFLOW_AUTO_START=true      # Enable auto-start (default: true)
LANGFLOW_USE_DOCKER=true      # Use Docker (default: true, recommended)
LANGFLOW_DOCKER_IMAGE=langflowai/langflow:latest

# Just run FastCMS - Langflow starts automatically
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Option 3: Local Installation (pipx)

```bash
# Install Langflow via pipx (isolated, no dependency conflicts)
pipx install langflow

# Run Langflow manually
langflow run --port 7860
```

> **Note**: Direct `pip install langflow` in FastCMS's venv causes dependency conflicts. Use Docker or pipx instead.

## Configuration

Set these environment variables in your `.env` file:

```bash
# Required: Langflow server URL
LANGFLOW_URL=http://localhost:7860

# Optional: API key for authentication (Langflow 1.5+)
LANGFLOW_API_KEY=your-api-key

# Optional: Embed Langflow UI in FastCMS admin
LANGFLOW_EMBED_UI=true

# Optional: Request timeout in seconds
LANGFLOW_REQUEST_TIMEOUT=300
```

## Usage

### Admin Interface

Access the Langflow admin page at:
```
http://localhost:8000/admin/langflow
```

This provides:
- Connection status indicator
- Embedded Langflow UI (if enabled)
- Quick link to open Langflow in new tab

### API Endpoints

All endpoints require FastCMS authentication.

#### Check Connection
```bash
GET /api/v1/plugins/langflow/health
```

Response:
```json
{
  "status": "connected",
  "langflow_url": "http://localhost:7860"
}
```

#### List Flows
```bash
GET /api/v1/plugins/langflow/flows
```

#### Get Flow Details
```bash
GET /api/v1/plugins/langflow/flows/{flow_id}
```

#### Execute Flow
```bash
POST /api/v1/plugins/langflow/flows/{flow_id}/run
Content-Type: application/json

{
  "input_value": "Your input text here",
  "tweaks": {}
}
```

#### Execute Flow with Streaming
```bash
POST /api/v1/plugins/langflow/flows/{flow_id}/run/stream
Content-Type: application/json

{
  "input_value": "Your input text here"
}
```

Returns Server-Sent Events (SSE) stream.

### JavaScript Example

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
```

### Python Example

```python
import httpx

class LangflowClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}

    async def run_flow(self, flow_id: str, input_value: str):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/plugins/langflow/flows/{flow_id}/run",
                headers=self.headers,
                json={"input_value": input_value}
            )
            return response.json()

    async def run_flow_stream(self, flow_id: str, input_value: str):
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/v1/plugins/langflow/flows/{flow_id}/run/stream",
                headers=self.headers,
                json={"input_value": input_value}
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        yield json.loads(line[6:])
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│    FastCMS      │     │    Langflow     │
│                 │     │                 │
│  ┌───────────┐  │     │  ┌───────────┐  │
│  │  Plugin   │◄─┼─────┼─►│   API     │  │
│  │  Routes   │  │     │  │  Server   │  │
│  └───────────┘  │     │  └───────────┘  │
│                 │     │                 │
│  ┌───────────┐  │     │  ┌───────────┐  │
│  │  Admin    │  │     │  │  Visual   │  │
│  │  UI       │◄─┼─────┼─►│  Editor   │  │
│  └───────────┘  │     │  └───────────┘  │
└─────────────────┘     └─────────────────┘
```

- FastCMS handles authentication and authorization
- Plugin proxies API requests to Langflow
- Admin UI can embed Langflow or link to it
- All workflow data lives in Langflow

## Comparison with Previous LangGraph Plugin

| Aspect | LangGraph (Old) | Langflow (New) |
|--------|-----------------|----------------|
| Lines of Code | ~1,655 | ~350 |
| Database Tables | 5 | 0 |
| API Endpoints | 14+ | 5 |
| Dependencies | Heavy (torch, transformers) | None |
| Maintenance | High | Minimal |
| UI Quality | Custom Rete.js | Professional |
| Integrations | ~8 | 50+ |

## Troubleshooting

### Connection Issues

1. Verify Langflow is running:
   ```bash
   curl http://localhost:7860/health
   ```

2. Check environment variables:
   ```bash
   echo $LANGFLOW_URL
   ```

3. Check FastCMS logs for connection errors

### Iframe Embedding

If the embedded UI doesn't load:
- Langflow may block iframe embedding
- Set `LANGFLOW_EMBED_UI=false` to use link mode instead
- Or configure Langflow's CORS settings

### Authentication

For Langflow 1.5+:
- Generate an API key in Langflow settings
- Set `LANGFLOW_API_KEY` environment variable

## Resources

- [Langflow Documentation](https://docs.langflow.org/)
- [Langflow GitHub](https://github.com/langflow-ai/langflow)
- [FastCMS Plugin Development](../DOCS/plugin-development.md)

## Credits

This plugin integrates with [Langflow](https://github.com/langflow-ai/langflow), an open-source visual framework for building AI-powered applications.

Langflow is licensed under the [MIT License](https://github.com/langflow-ai/langflow/blob/main/LICENSE).

```
MIT License

Copyright (c) 2023 Langflow

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

We thank the Langflow team for creating and maintaining this excellent tool.
