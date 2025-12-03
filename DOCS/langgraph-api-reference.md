# LangGraph Plugin - Complete API Reference

FastCMS is a **Backend as a Service (BaaS)**, and the LangGraph plugin provides a complete REST API for building AI-powered workflows programmatically.

## 🌐 Base URL

```
http://localhost:8000/api/v1/plugins/langgraph
```

## 📚 Interactive API Documentation

FastCMS automatically generates interactive API documentation:

### Swagger UI (Try it out in browser)
```
http://localhost:8000/docs
```
- **Interactive**: Test APIs directly in browser
- **Authentication**: Built-in token authentication
- **Request/Response**: See all schemas

### ReDoc (Clean documentation)
```
http://localhost:8000/redoc
```
- **Clean layout**: Better for reading
- **Search**: Find endpoints quickly
- **Examples**: View request/response examples

---

## 🔐 Authentication

All API requests require authentication using Bearer tokens.

### Step 1: Login to Get Access Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@fastcms.dev",
    "password": "your-password"
  }'
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "user-uuid",
    "email": "admin@fastcms.dev"
  }
}
```

### Step 2: Use Token in Requests

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  http://localhost:8000/api/v1/plugins/langgraph/workflows
```

---

## 📋 Complete API Endpoints

### Workflows

#### 1. Create Workflow
`POST /api/v1/plugins/langgraph/workflows`

Create a new AI workflow.

**Request Body**:
```json
{
  "name": "My AI Workflow",
  "description": "Description of workflow",
  "workflow_type": "langgraph",
  "tags": ["ai", "automation"],
  "is_template": false,
  "rete_data": {}
}
```

**Fields**:
- `name` (required): Workflow name
- `description` (optional): Workflow description
- `workflow_type` (optional): "custom" or "langgraph" (use "langgraph" for streaming)
- `tags` (optional): Array of tags
- `is_template` (optional): Make available as template
- `rete_data` (optional): Visual editor state (managed by UI)

**Response** (201 Created):
```json
{
  "id": "workflow-uuid",
  "user_id": "user-uuid",
  "name": "My AI Workflow",
  "description": "Description of workflow",
  "tags": ["ai", "automation"],
  "is_template": false,
  "rete_data": {},
  "created_at": "2025-12-03T10:00:00",
  "updated_at": "2025-12-03T10:00:00"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/plugins/langgraph/workflows \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Text Summarizer",
    "description": "Summarize long texts using GPT-4",
    "workflow_type": "langgraph",
    "tags": ["summarization", "gpt4"]
  }'
```

---

#### 2. List Workflows
`GET /api/v1/plugins/langgraph/workflows`

Get all workflows for the authenticated user.

**Response** (200 OK):
```json
{
  "workflows": [
    {
      "id": "workflow-uuid",
      "name": "Text Summarizer",
      "description": "Summarize long texts",
      "tags": ["summarization"],
      "is_template": false,
      "created_at": "2025-12-03T10:00:00",
      "updated_at": "2025-12-03T10:00:00"
    }
  ],
  "total": 1
}
```

**Example**:
```bash
curl -X GET http://localhost:8000/api/v1/plugins/langgraph/workflows \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

#### 3. Get Workflow
`GET /api/v1/plugins/langgraph/workflows/{workflow_id}`

Get a specific workflow by ID.

**Response** (200 OK):
```json
{
  "id": "workflow-uuid",
  "user_id": "user-uuid",
  "name": "Text Summarizer",
  "description": "Summarize long texts",
  "tags": ["summarization"],
  "is_template": false,
  "rete_data": {},
  "created_at": "2025-12-03T10:00:00",
  "updated_at": "2025-12-03T10:00:00"
}
```

**Example**:
```bash
curl -X GET http://localhost:8000/api/v1/plugins/langgraph/workflows/WORKFLOW_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

#### 4. Update Workflow
`PUT /api/v1/plugins/langgraph/workflows/{workflow_id}`

Update a workflow.

**Request Body**:
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "tags": ["new", "tags"],
  "is_template": true
}
```

**Response** (200 OK): Returns updated workflow

**Example**:
```bash
curl -X PUT http://localhost:8000/api/v1/plugins/langgraph/workflows/WORKFLOW_ID \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Advanced Text Summarizer",
    "tags": ["summarization", "advanced"]
  }'
```

---

#### 5. Delete Workflow
`DELETE /api/v1/plugins/langgraph/workflows/{workflow_id}`

Delete a workflow and all its nodes/edges.

**Response** (204 No Content)

**Example**:
```bash
curl -X DELETE http://localhost:8000/api/v1/plugins/langgraph/workflows/WORKFLOW_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Nodes

#### 6. Create Node
`POST /api/v1/plugins/langgraph/workflows/{workflow_id}/nodes`

Add a node to a workflow.

**Request Body**:
```json
{
  "node_type": "llm",
  "label": "Main LLM",
  "position_x": 100,
  "position_y": 200,
  "config": {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 1000,
    "system_prompt": "You are a helpful assistant."
  }
}
```

**Node Types**:
- `start` - Workflow entry point
- `end` - Workflow exit point
- `llm` - Language model node
- `function` - Custom Python code
- `document_loader` - Load documents (PDF, DOCX, Web)
- `text_splitter` - Chunk documents
- `embedding` - Generate embeddings
- `vector_store` - Vector database
- `deep_agent` - Autonomous agent

**Response** (201 Created):
```json
{
  "id": "node-uuid",
  "workflow_id": "workflow-uuid",
  "node_type": "llm",
  "label": "Main LLM",
  "position_x": 100,
  "position_y": 200,
  "config": {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 1000,
    "system_prompt": "You are a helpful assistant."
  },
  "created_at": "2025-12-03T10:00:00"
}
```

**Example - LLM Node**:
```bash
curl -X POST http://localhost:8000/api/v1/plugins/langgraph/workflows/WORKFLOW_ID/nodes \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "node_type": "llm",
    "label": "Summarizer",
    "position_x": 200,
    "position_y": 100,
    "config": {
      "provider": "anthropic",
      "model": "claude-3-5-sonnet-20241022",
      "temperature": 0.5,
      "max_tokens": 500,
      "system_prompt": "Summarize the following text in 2-3 sentences."
    }
  }'
```

**Example - Function Node**:
```bash
curl -X POST http://localhost:8000/api/v1/plugins/langgraph/workflows/WORKFLOW_ID/nodes \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "node_type": "function",
    "label": "Uppercase Transform",
    "position_x": 300,
    "position_y": 100,
    "config": {
      "code": "output = input.upper()"
    }
  }'
```

**Example - Document Loader Node**:
```bash
curl -X POST http://localhost:8000/api/v1/plugins/langgraph/workflows/WORKFLOW_ID/nodes \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "node_type": "document_loader",
    "label": "Load PDF",
    "position_x": 100,
    "position_y": 100,
    "config": {
      "loader_type": "pdf",
      "source": "/data/document.pdf"
    }
  }'
```

---

#### 7. List Nodes
`GET /api/v1/plugins/langgraph/workflows/{workflow_id}/nodes`

Get all nodes in a workflow.

**Response** (200 OK):
```json
{
  "nodes": [
    {
      "id": "node-uuid",
      "workflow_id": "workflow-uuid",
      "node_type": "llm",
      "label": "Main LLM",
      "config": {...},
      "position_x": 100,
      "position_y": 200
    }
  ],
  "total": 1
}
```

**Example**:
```bash
curl -X GET http://localhost:8000/api/v1/plugins/langgraph/workflows/WORKFLOW_ID/nodes \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

#### 8. Update Node
`PUT /api/v1/plugins/langgraph/workflows/{workflow_id}/nodes/{node_id}`

Update a node's configuration.

**Request Body**:
```json
{
  "label": "Updated Label",
  "config": {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.8
  },
  "position_x": 150,
  "position_y": 250
}
```

**Response** (200 OK): Returns updated node

**Example**:
```bash
curl -X PUT http://localhost:8000/api/v1/plugins/langgraph/workflows/WORKFLOW_ID/nodes/NODE_ID \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "provider": "openai",
      "model": "gpt-4o",
      "temperature": 0.9,
      "max_tokens": 2000
    }
  }'
```

---

#### 9. Delete Node
`DELETE /api/v1/plugins/langgraph/workflows/{workflow_id}/nodes/{node_id}`

Delete a node from a workflow.

**Response** (204 No Content)

**Example**:
```bash
curl -X DELETE http://localhost:8000/api/v1/plugins/langgraph/workflows/WORKFLOW_ID/nodes/NODE_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Edges (Connections)

#### 10. Create Edge
`POST /api/v1/plugins/langgraph/workflows/{workflow_id}/edges`

Connect two nodes.

**Request Body**:
```json
{
  "source_node_id": "node-1-uuid",
  "target_node_id": "node-2-uuid"
}
```

**Response** (201 Created):
```json
{
  "id": "edge-uuid",
  "workflow_id": "workflow-uuid",
  "source_node_id": "node-1-uuid",
  "target_node_id": "node-2-uuid",
  "created_at": "2025-12-03T10:00:00"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/plugins/langgraph/workflows/WORKFLOW_ID/edges \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_node_id": "START_NODE_ID",
    "target_node_id": "LLM_NODE_ID"
  }'
```

---

#### 11. List Edges
`GET /api/v1/plugins/langgraph/workflows/{workflow_id}/edges`

Get all edges in a workflow.

**Response** (200 OK):
```json
{
  "edges": [
    {
      "id": "edge-uuid",
      "workflow_id": "workflow-uuid",
      "source_node_id": "node-1-uuid",
      "target_node_id": "node-2-uuid",
      "created_at": "2025-12-03T10:00:00"
    }
  ],
  "total": 1
}
```

**Example**:
```bash
curl -X GET http://localhost:8000/api/v1/plugins/langgraph/workflows/WORKFLOW_ID/edges \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

#### 12. Delete Edge
`DELETE /api/v1/plugins/langgraph/workflows/{workflow_id}/edges/{edge_id}`

Delete a connection between nodes.

**Response** (204 No Content)

**Example**:
```bash
curl -X DELETE http://localhost:8000/api/v1/plugins/langgraph/workflows/WORKFLOW_ID/edges/EDGE_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Execution

#### 13. Execute Workflow (Non-Streaming)
`POST /api/v1/plugins/langgraph/workflows/{workflow_id}/execute`

Execute a workflow and wait for completion.

**Request Body**:
```json
{
  "input": "Your input text or data here"
}
```

**Response** (200 OK):
```json
{
  "id": "execution-uuid",
  "workflow_id": "workflow-uuid",
  "status": "completed",
  "input_data": "Your input text",
  "output_data": {
    "messages": [
      {
        "role": "assistant",
        "content": "AI response here"
      }
    ],
    "result": "Final output"
  },
  "execution_log": [
    {
      "type": "node_start",
      "node": "llm-1",
      "message": "Starting node: llm-1",
      "timestamp": "2025-12-03T10:00:00"
    },
    {
      "type": "node_complete",
      "node": "llm-1",
      "output": {...},
      "timestamp": "2025-12-03T10:00:05"
    }
  ],
  "started_at": "2025-12-03T10:00:00",
  "completed_at": "2025-12-03T10:00:05",
  "error_message": null
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/plugins/langgraph/workflows/WORKFLOW_ID/execute \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Summarize the benefits of renewable energy."
  }'
```

---

#### 14. Execute Workflow (Streaming) ⭐
`POST /api/v1/plugins/langgraph/workflows/{workflow_id}/execute/stream`

Execute a workflow with real-time streaming (Server-Sent Events).

**Requirements**:
- Workflow must have `workflow_type: "langgraph"`

**Request Body**:
```json
{
  "input": "Your input text or data here"
}
```

**Response** (200 OK - Server-Sent Events):
```
Content-Type: text/event-stream

data: {"type":"info","message":"Generating LangGraph code...","timestamp":"2025-12-03T10:00:00"}

data: {"type":"info","message":"Code generation complete","timestamp":"2025-12-03T10:00:01"}

data: {"type":"node_start","node":"llm-1","message":"Starting node: llm-1","timestamp":"2025-12-03T10:00:02"}

data: {"type":"token","content":"The","timestamp":"2025-12-03T10:00:02"}

data: {"type":"token","content":" benefits","timestamp":"2025-12-03T10:00:02"}

data: {"type":"token","content":" of","timestamp":"2025-12-03T10:00:02"}

data: {"type":"node_complete","node":"llm-1","output":{...},"timestamp":"2025-12-03T10:00:05"}

data: {"type":"execution_complete","message":"Workflow completed","timestamp":"2025-12-03T10:00:05"}
```

**Event Types**:
- `info` - Information message
- `node_start` - Node execution started
- `token` - Individual token from LLM (real-time streaming)
- `node_complete` - Node execution completed
- `execution_complete` - Workflow finished
- `error` - Error occurred

**Example (curl)**:
```bash
curl -N -X POST http://localhost:8000/api/v1/plugins/langgraph/workflows/WORKFLOW_ID/execute/stream \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Explain quantum computing in simple terms."
  }'
```

**Example (JavaScript/Browser)**:
```javascript
const eventSource = new EventSource(
  'http://localhost:8000/api/v1/plugins/langgraph/workflows/WORKFLOW_ID/execute/stream',
  {
    headers: {
      'Authorization': 'Bearer YOUR_TOKEN'
    }
  }
);

let fullResponse = '';

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.type) {
    case 'info':
      console.log('Info:', data.message);
      break;

    case 'node_start':
      console.log('Node started:', data.node);
      break;

    case 'token':
      // Append token to build full response
      fullResponse += data.content;
      document.getElementById('output').textContent = fullResponse;
      break;

    case 'node_complete':
      console.log('Node completed:', data.node);
      break;

    case 'execution_complete':
      console.log('Workflow completed!');
      eventSource.close();
      break;

    case 'error':
      console.error('Error:', data.message);
      eventSource.close();
      break;
  }
};

eventSource.onerror = (error) => {
  console.error('Stream error:', error);
  eventSource.close();
};
```

**Example (Python)**:
```python
import requests
import json

url = "http://localhost:8000/api/v1/plugins/langgraph/workflows/WORKFLOW_ID/execute/stream"
headers = {
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
}
data = {"input": "Explain quantum computing"}

response = requests.post(url, headers=headers, json=data, stream=True)

for line in response.iter_lines():
    if line:
        line = line.decode('utf-8')
        if line.startswith('data: '):
            event_data = json.loads(line[6:])

            if event_data['type'] == 'token':
                print(event_data['content'], end='', flush=True)
            elif event_data['type'] == 'execution_complete':
                print('\n\nWorkflow completed!')
                break
            elif event_data['type'] == 'error':
                print(f"\nError: {event_data['message']}")
                break
```

---

#### 15. List Executions
`GET /api/v1/plugins/langgraph/workflows/{workflow_id}/executions`

Get execution history for a workflow.

**Response** (200 OK):
```json
{
  "executions": [
    {
      "id": "execution-uuid",
      "workflow_id": "workflow-uuid",
      "status": "completed",
      "input_data": "Input text",
      "output_data": {...},
      "started_at": "2025-12-03T10:00:00",
      "completed_at": "2025-12-03T10:00:05"
    }
  ],
  "total": 1
}
```

**Example**:
```bash
curl -X GET http://localhost:8000/api/v1/plugins/langgraph/workflows/WORKFLOW_ID/executions \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

#### 16. Get Templates
`GET /api/v1/plugins/langgraph/templates`

Get all workflow templates.

**Response** (200 OK):
```json
{
  "workflows": [
    {
      "id": "template-uuid",
      "name": "RAG Pipeline Template",
      "description": "Document Q&A system",
      "is_template": true
    }
  ],
  "total": 1
}
```

**Example**:
```bash
curl -X GET http://localhost:8000/api/v1/plugins/langgraph/templates \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🚀 Complete Workflow Example (BaaS Style)

Here's a complete example of creating and executing a workflow via API:

```bash
#!/bin/bash

# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@fastcms.dev","password":"admin"}' \
  | jq -r '.access_token')

echo "Token: $TOKEN"

# 2. Create Workflow
WORKFLOW=$(curl -s -X POST http://localhost:8000/api/v1/plugins/langgraph/workflows \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "API Text Summarizer",
    "description": "Summarize text using GPT-4",
    "workflow_type": "langgraph",
    "tags": ["api", "summarization"]
  }')

WORKFLOW_ID=$(echo $WORKFLOW | jq -r '.id')
echo "Workflow ID: $WORKFLOW_ID"

# 3. Add Start Node
START_NODE=$(curl -s -X POST http://localhost:8000/api/v1/plugins/langgraph/workflows/$WORKFLOW_ID/nodes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "node_type": "start",
    "label": "Start",
    "position_x": 0,
    "position_y": 100
  }')

START_NODE_ID=$(echo $START_NODE | jq -r '.id')
echo "Start Node ID: $START_NODE_ID"

# 4. Add LLM Node
LLM_NODE=$(curl -s -X POST http://localhost:8000/api/v1/plugins/langgraph/workflows/$WORKFLOW_ID/nodes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "node_type": "llm",
    "label": "Summarizer",
    "position_x": 200,
    "position_y": 100,
    "config": {
      "provider": "openai",
      "model": "gpt-4o-mini",
      "temperature": 0.5,
      "max_tokens": 200,
      "system_prompt": "Summarize the following text in 2-3 sentences."
    }
  }')

LLM_NODE_ID=$(echo $LLM_NODE | jq -r '.id')
echo "LLM Node ID: $LLM_NODE_ID"

# 5. Add End Node
END_NODE=$(curl -s -X POST http://localhost:8000/api/v1/plugins/langgraph/workflows/$WORKFLOW_ID/nodes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "node_type": "end",
    "label": "End",
    "position_x": 400,
    "position_y": 100
  }')

END_NODE_ID=$(echo $END_NODE | jq -r '.id')
echo "End Node ID: $END_NODE_ID"

# 6. Connect Nodes
curl -s -X POST http://localhost:8000/api/v1/plugins/langgraph/workflows/$WORKFLOW_ID/edges \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"source_node_id\":\"$START_NODE_ID\",\"target_node_id\":\"$LLM_NODE_ID\"}"

curl -s -X POST http://localhost:8000/api/v1/plugins/langgraph/workflows/$WORKFLOW_ID/edges \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"source_node_id\":\"$LLM_NODE_ID\",\"target_node_id\":\"$END_NODE_ID\"}"

echo "Edges created!"

# 7. Execute Workflow
echo "Executing workflow..."
curl -X POST http://localhost:8000/api/v1/plugins/langgraph/workflows/$WORKFLOW_ID/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Renewable energy sources like solar and wind power are becoming increasingly important in the fight against climate change. They provide clean, sustainable alternatives to fossil fuels, reducing greenhouse gas emissions and air pollution. As technology improves and costs decrease, renewable energy is becoming more accessible and economically viable for communities worldwide."
  }' | jq '.'
```

---

## 🔗 SDK Examples

### JavaScript/TypeScript

```typescript
class LangGraphClient {
  private baseUrl = 'http://localhost:8000/api/v1/plugins/langgraph';
  private token: string;

  constructor(token: string) {
    this.token = token;
  }

  async createWorkflow(data: {
    name: string;
    description?: string;
    workflow_type?: 'custom' | 'langgraph';
    tags?: string[];
  }) {
    const response = await fetch(`${this.baseUrl}/workflows`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    return response.json();
  }

  async executeWorkflow(workflowId: string, input: any) {
    const response = await fetch(`${this.baseUrl}/workflows/${workflowId}/execute`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ input })
    });
    return response.json();
  }

  async executeWorkflowStreaming(
    workflowId: string,
    input: any,
    onToken: (token: string) => void,
    onComplete: () => void,
    onError: (error: string) => void
  ) {
    const eventSource = new EventSource(
      `${this.baseUrl}/workflows/${workflowId}/execute/stream`
    );

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'token') {
        onToken(data.content);
      } else if (data.type === 'execution_complete') {
        onComplete();
        eventSource.close();
      } else if (data.type === 'error') {
        onError(data.message);
        eventSource.close();
      }
    };

    eventSource.onerror = () => {
      onError('Stream error');
      eventSource.close();
    };
  }
}

// Usage
const client = new LangGraphClient('YOUR_TOKEN');

// Create workflow
const workflow = await client.createWorkflow({
  name: 'My AI App',
  workflow_type: 'langgraph',
  tags: ['ai', 'automation']
});

// Execute
const result = await client.executeWorkflow(workflow.id, 'Hello AI!');
console.log(result.output_data);

// Execute with streaming
client.executeWorkflowStreaming(
  workflow.id,
  'Tell me about AI',
  (token) => console.log(token), // onToken
  () => console.log('Done!'),     // onComplete
  (error) => console.error(error) // onError
);
```

### Python

```python
import requests
from typing import Callable, Optional

class LangGraphClient:
    def __init__(self, token: str, base_url: str = "http://localhost:8000"):
        self.token = token
        self.base_url = f"{base_url}/api/v1/plugins/langgraph"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def create_workflow(self, name: str, description: Optional[str] = None,
                       workflow_type: str = "langgraph", tags: list = None):
        data = {
            "name": name,
            "description": description,
            "workflow_type": workflow_type,
            "tags": tags or []
        }
        response = requests.post(
            f"{self.base_url}/workflows",
            headers=self.headers,
            json=data
        )
        return response.json()

    def execute_workflow(self, workflow_id: str, input_data):
        response = requests.post(
            f"{self.base_url}/workflows/{workflow_id}/execute",
            headers=self.headers,
            json={"input": input_data}
        )
        return response.json()

    def execute_workflow_streaming(self, workflow_id: str, input_data,
                                   on_token: Callable[[str], None],
                                   on_complete: Callable[[], None],
                                   on_error: Callable[[str], None]):
        response = requests.post(
            f"{self.base_url}/workflows/{workflow_id}/execute/stream",
            headers=self.headers,
            json={"input": input_data},
            stream=True
        )

        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    event = json.loads(line[6:])

                    if event['type'] == 'token':
                        on_token(event['content'])
                    elif event['type'] == 'execution_complete':
                        on_complete()
                        break
                    elif event['type'] == 'error':
                        on_error(event['message'])
                        break

# Usage
client = LangGraphClient('YOUR_TOKEN')

# Create workflow
workflow = client.create_workflow(
    name='My AI App',
    workflow_type='langgraph',
    tags=['ai', 'automation']
)

# Execute
result = client.execute_workflow(workflow['id'], 'Hello AI!')
print(result['output_data'])

# Execute with streaming
client.execute_workflow_streaming(
    workflow['id'],
    'Tell me about AI',
    on_token=lambda t: print(t, end='', flush=True),
    on_complete=lambda: print('\nDone!'),
    on_error=lambda e: print(f'\nError: {e}')
)
```

---

## 📖 Summary

The LangGraph plugin provides a **complete BaaS API** for building AI workflows:

1. **Interactive Docs**: Test APIs at `http://localhost:8000/docs`
2. **RESTful API**: Complete CRUD operations for workflows, nodes, edges
3. **Streaming Support**: Real-time token streaming with Server-Sent Events
4. **Authentication**: Secure Bearer token authentication
5. **Multi-LLM**: OpenAI, Anthropic, Google support
6. **Programmatic**: Build workflows entirely via API

Start building AI-powered applications today! 🚀
