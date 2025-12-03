# LangGraph Plugin - Visual AI Workflow Builder

The LangGraph plugin for FastCMS enables you to build, execute, and manage AI-powered workflows using a visual drag-and-drop interface. Powered by **LangGraph 1.0** and **LangChain**, it provides production-ready workflow automation with streaming execution, multi-LLM support, and RAG capabilities.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Creating Workflows](#creating-workflows)
- [Node Types](#node-types)
- [Execution Methods](#execution-methods)
- [API Usage](#api-usage)
- [Examples](#examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

### What is LangGraph?

LangGraph is a production-ready framework for building stateful, multi-actor applications with LLMs. It extends LangChain with:
- **StateGraph**: Manage complex workflow state
- **Streaming**: Real-time token-by-token execution
- **Checkpointing**: Persistent state across runs
- **Multi-step workflows**: Chain multiple AI operations

### Key Features

- ✅ **Visual Editor**: Drag-and-drop workflow builder
- ✅ **7 Node Types**: LLM, Function, Document Loader, Text Splitter, Embedding, Vector Store, Deep Agent
- ✅ **Multi-LLM Support**: OpenAI, Anthropic (Claude), Google (Gemini)
- ✅ **Real-time Streaming**: Server-Sent Events (SSE) with token streaming
- ✅ **RAG Pipeline**: Complete document Q&A workflow
- ✅ **Code Generation**: Visual workflows compile to Python
- ✅ **RESTful API**: Full programmatic control
- ✅ **Execution History**: Track and review all runs

---

## Quick Start

### 1. Setup API Keys

Add your LLM provider API keys to the `.env` file:

```bash
# .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
```

### 2. Access the Plugin

Navigate to the LangGraph admin interface:

```
http://localhost:8000/admin/langgraph
```

### 3. Create Your First Workflow

1. Click **"New Workflow"**
2. Name it (e.g., "Text Summarizer")
3. Add nodes:
   - **Start Node** (automatically added)
   - **LLM Node** (drag from sidebar)
   - **End Node** (drag from sidebar)
4. Connect nodes by dragging between connection points
5. Configure the LLM node (click gear icon):
   ```json
   {
     "provider": "openai",
     "model": "gpt-4o-mini",
     "temperature": 0.7,
     "max_tokens": 500,
     "system_prompt": "You are a helpful assistant that summarizes text concisely."
   }
   ```
6. Click **"Save"**
7. Click **"Run"** and enter text to summarize

---

## Configuration

### Workflow Settings

When creating a workflow, you can configure:

| Field | Description | Default |
|-------|-------------|---------|
| `name` | Workflow name | Required |
| `description` | Workflow description | Optional |
| `workflow_type` | Type: "custom" or "langgraph" | "custom" |
| `tags` | Array of tags for organization | `[]` |
| `is_template` | Make available as template | `false` |

**Important**: To use LangGraph features (streaming, code generation), set `workflow_type: "langgraph"`.

### Provider Configuration

#### OpenAI
```json
{
  "provider": "openai",
  "model": "gpt-4o",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Available Models**:
- `gpt-4o` - Best for complex reasoning
- `gpt-4o-mini` - Fast and cost-effective
- `gpt-4-turbo` - Previous generation flagship
- `gpt-3.5-turbo` - Budget-friendly option

#### Anthropic (Claude)
```json
{
  "provider": "anthropic",
  "model": "claude-3-5-sonnet-20241022",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Available Models**:
- `claude-3-5-sonnet-20241022` - Latest, most capable
- `claude-3-opus-20240229` - Most powerful for complex tasks
- `claude-3-haiku-20240307` - Fastest, most cost-effective

#### Google (Gemini)
```json
{
  "provider": "google",
  "model": "gemini-pro",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Available Models**:
- `gemini-pro` - Multimodal capabilities
- `gemini-pro-vision` - Image understanding

---

## Creating Workflows

### Visual Editor Interface

The visual editor provides:
- **Node Palette** (left sidebar): Drag nodes onto canvas
- **Canvas** (center): Arrange and connect nodes
- **Properties Panel** (right sidebar): Configure selected node
- **Toolbar** (top): Save, Run, Delete actions

### Workflow Structure

Every workflow consists of:
1. **Start Node**: Entry point (required)
2. **Processing Nodes**: LLM, Function, etc.
3. **End Node**: Exit point (optional)
4. **Edges**: Connections between nodes

### Adding Nodes

1. **Drag** a node from the sidebar to the canvas
2. **Click** the node to select it
3. **Configure** using the properties panel
4. **Connect** by dragging from one node's output to another's input

### Connecting Nodes

1. Click and drag from a node's **output connector** (right side)
2. Drop on another node's **input connector** (left side)
3. The edge will be created automatically
4. To delete an edge, click it and press Delete or use the delete button

---

## Node Types

### 1. LLM Node (Brain Icon 🧠)

Execute language models with streaming support.

**Configuration**:
```json
{
  "provider": "openai",
  "model": "gpt-4o-mini",
  "temperature": 0.7,
  "max_tokens": 1000,
  "system_prompt": "You are a helpful assistant..."
}
```

**Use Cases**:
- Text generation
- Summarization
- Question answering
- Translation
- Code generation

**Tips**:
- Lower temperature (0-0.3) for factual tasks
- Higher temperature (0.7-1.0) for creative tasks
- Use specific system prompts for better results
- Choose appropriate model for complexity/cost balance

### 2. Function Node (Code Icon 💻)

Execute custom Python code for data processing.

**Configuration**:
```json
{
  "code": "output = input.upper()"
}
```

**Available Variables**:
- `input` - Data from previous node
- `output` - Set this with your result

**Examples**:

**Transform text**:
```python
# Convert to uppercase
output = input.upper()
```

**Parse JSON**:
```python
import json
data = json.loads(input)
output = data.get('field_name', 'default')
```

**Filter list**:
```python
lines = input.split('\n')
filtered = [line for line in lines if len(line) > 10]
output = '\n'.join(filtered)
```

**Format output**:
```python
output = f"Result: {input}\nProcessed at: {datetime.now()}"
```

### 3. Document Loader Node (Document Icon 📄)

Load documents from various sources.

**Configuration**:
```json
{
  "loader_type": "pdf",
  "source": "/path/to/document.pdf"
}
```

**Supported Types**:
- `pdf` - PDF documents
- `docx` - Microsoft Word documents
- `web` - Web pages (URL)

**Examples**:

**Load PDF**:
```json
{
  "loader_type": "pdf",
  "source": "/data/research.pdf"
}
```

**Load webpage**:
```json
{
  "loader_type": "web",
  "source": "https://example.com/article"
}
```

### 4. Text Splitter Node (Scissors Icon ✂️)

Split documents into chunks for processing.

**Configuration**:
```json
{
  "chunk_size": 1000,
  "chunk_overlap": 200
}
```

**Parameters**:
- `chunk_size` - Characters per chunk (500-2000 recommended)
- `chunk_overlap` - Overlap between chunks (100-300 recommended)

**Best Practices**:
- Use 1000-1500 for general text
- Use 500-800 for dense technical content
- Use 200 overlap to preserve context across chunks

### 5. Embedding Node (Vector Icon 🔢)

Generate embeddings for semantic search.

**Configuration**:
```json
{
  "provider": "openai",
  "model": "text-embedding-3-small"
}
```

**Available Models**:
- `text-embedding-3-small` - Fast and efficient
- `text-embedding-3-large` - Highest quality

### 6. Vector Store Node (Database Icon 🗄️)

Store and search document embeddings.

**Configuration (Store)**:
```json
{
  "provider": "faiss",
  "action": "store",
  "index_name": "my_documents"
}
```

**Configuration (Search)**:
```json
{
  "provider": "faiss",
  "action": "search",
  "index_name": "my_documents"
}
```

**Supported Stores**:
- `faiss` - Local, fast, in-memory
- `pinecone` - Cloud, scalable
- `chroma` - Open-source, persistent

### 7. Deep Agent Node (Robot Icon 🤖)

Autonomous agent with planning and tool usage.

**Configuration**:
```json
{
  "model": "claude-sonnet-4-5-20250929",
  "max_iterations": 10
}
```

**Capabilities**:
- Multi-step planning
- Tool selection and usage
- Self-correction
- Complex task completion

---

## Execution Methods

### 1. UI Execution

**Steps**:
1. Open your workflow in the editor
2. Click **"Run"** button
3. Enter input data in the modal
4. View results and execution log

**When to use**:
- Testing workflows
- Interactive exploration
- Debugging

### 2. API Execution (Non-Streaming)

**Endpoint**: `POST /api/v1/plugins/langgraph/workflows/{workflow_id}/execute`

**Request**:
```bash
curl -X POST \
  http://localhost:8000/api/v1/plugins/langgraph/workflows/WORKFLOW_ID/execute \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Your input text here"
  }'
```

**Response**:
```json
{
  "id": "execution-uuid",
  "workflow_id": "workflow-uuid",
  "status": "completed",
  "output_data": {
    "messages": [...],
    "result": "Final output"
  },
  "execution_log": [
    {
      "type": "node_start",
      "node": "llm-1",
      "timestamp": "2025-12-03T10:30:00"
    },
    {
      "type": "node_complete",
      "node": "llm-1",
      "timestamp": "2025-12-03T10:30:05"
    }
  ],
  "started_at": "2025-12-03T10:30:00",
  "completed_at": "2025-12-03T10:30:05"
}
```

**When to use**:
- Batch processing
- Background jobs
- Simple integrations

### 3. API Execution (Streaming)

**Endpoint**: `POST /api/v1/plugins/langgraph/workflows/{workflow_id}/execute/stream`

**Request**:
```bash
curl -X POST \
  http://localhost:8000/api/v1/plugins/langgraph/workflows/WORKFLOW_ID/execute/stream \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Your input text here"
  }'
```

**Response** (Server-Sent Events):
```
data: {"type":"info","message":"Generating code...","timestamp":"2025-12-03T10:30:00"}

data: {"type":"node_start","node":"llm-1","message":"Starting node: llm-1","timestamp":"2025-12-03T10:30:01"}

data: {"type":"token","content":"Hello","timestamp":"2025-12-03T10:30:02"}

data: {"type":"token","content":" world","timestamp":"2025-12-03T10:30:02"}

data: {"type":"node_complete","node":"llm-1","timestamp":"2025-12-03T10:30:05"}

data: {"type":"execution_complete","message":"Workflow completed","timestamp":"2025-12-03T10:30:05"}
```

**JavaScript Client**:
```javascript
const eventSource = new EventSource(
  '/api/v1/plugins/langgraph/workflows/WORKFLOW_ID/execute/stream'
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.type) {
    case 'token':
      // Append token to UI
      document.getElementById('output').textContent += data.content;
      break;

    case 'node_start':
      console.log(`Starting: ${data.node}`);
      break;

    case 'node_complete':
      console.log(`Completed: ${data.node}`);
      break;

    case 'execution_complete':
      console.log('Workflow finished!');
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

**When to use**:
- User-facing applications
- Real-time feedback
- Interactive chat interfaces
- Long-running workflows

---

## API Usage

### Authentication

All API requests require authentication:

```bash
# Get access token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password"
  }'

# Use token in requests
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  http://localhost:8000/api/v1/plugins/langgraph/workflows
```

### Workflows

**Create Workflow**:
```bash
POST /api/v1/plugins/langgraph/workflows
{
  "name": "My RAG Pipeline",
  "description": "Document Q&A system",
  "workflow_type": "langgraph",
  "tags": ["rag", "qa"]
}
```

**List Workflows**:
```bash
GET /api/v1/plugins/langgraph/workflows
```

**Get Workflow**:
```bash
GET /api/v1/plugins/langgraph/workflows/{workflow_id}
```

**Update Workflow**:
```bash
PUT /api/v1/plugins/langgraph/workflows/{workflow_id}
{
  "name": "Updated Name",
  "description": "Updated description"
}
```

**Delete Workflow**:
```bash
DELETE /api/v1/plugins/langgraph/workflows/{workflow_id}
```

### Nodes

**Create Node**:
```bash
POST /api/v1/plugins/langgraph/workflows/{workflow_id}/nodes
{
  "node_type": "llm",
  "label": "Main LLM",
  "position_x": 100,
  "position_y": 200,
  "config": {
    "provider": "anthropic",
    "model": "claude-3-5-sonnet-20241022",
    "temperature": 0.7,
    "max_tokens": 2000,
    "system_prompt": "You are an expert assistant."
  }
}
```

**List Nodes**:
```bash
GET /api/v1/plugins/langgraph/workflows/{workflow_id}/nodes
```

**Update Node**:
```bash
PUT /api/v1/plugins/langgraph/workflows/{workflow_id}/nodes/{node_id}
{
  "label": "Updated Label",
  "config": { ... }
}
```

**Delete Node**:
```bash
DELETE /api/v1/plugins/langgraph/workflows/{workflow_id}/nodes/{node_id}
```

### Edges

**Create Edge**:
```bash
POST /api/v1/plugins/langgraph/workflows/{workflow_id}/edges
{
  "source_node_id": "node-1-uuid",
  "target_node_id": "node-2-uuid"
}
```

**List Edges**:
```bash
GET /api/v1/plugins/langgraph/workflows/{workflow_id}/edges
```

**Delete Edge**:
```bash
DELETE /api/v1/plugins/langgraph/workflows/{workflow_id}/edges/{edge_id}
```

### Executions

**List Executions**:
```bash
GET /api/v1/plugins/langgraph/workflows/{workflow_id}/executions
```

**Get Execution**:
```bash
GET /api/v1/plugins/langgraph/executions/{execution_id}
```

---

## Examples

### Example 1: Simple Text Summarizer

**Workflow**:
```
Start → LLM (Summarizer) → End
```

**LLM Node Config**:
```json
{
  "provider": "openai",
  "model": "gpt-4o-mini",
  "temperature": 0.5,
  "max_tokens": 200,
  "system_prompt": "Summarize the following text in 2-3 sentences."
}
```

**Usage**:
```bash
curl -X POST .../execute -d '{"input": "Long text to summarize..."}'
```

### Example 2: Multi-Step Content Pipeline

**Workflow**:
```
Start → LLM (Draft) → LLM (Improve) → Function (Format) → End
```

**Node 1 - Draft**:
```json
{
  "provider": "openai",
  "model": "gpt-4o",
  "system_prompt": "Write a blog post about the topic."
}
```

**Node 2 - Improve**:
```json
{
  "provider": "anthropic",
  "model": "claude-3-5-sonnet-20241022",
  "system_prompt": "Improve the grammar and make it more professional."
}
```

**Node 3 - Format**:
```python
# Add markdown formatting
output = f"# Blog Post\n\n{input}\n\n---\n*Generated by AI*"
```

### Example 3: RAG Pipeline (Document Q&A)

**Workflow**:
```
Start → Document Loader → Text Splitter → Embedding → Vector Store → LLM → End
```

**Step 1 - Load Document**:
```json
{
  "loader_type": "pdf",
  "source": "/data/company-handbook.pdf"
}
```

**Step 2 - Split Text**:
```json
{
  "chunk_size": 1000,
  "chunk_overlap": 200
}
```

**Step 3 - Generate Embeddings**:
```json
{
  "provider": "openai",
  "model": "text-embedding-3-small"
}
```

**Step 4 - Store in Vector DB**:
```json
{
  "provider": "faiss",
  "action": "store",
  "index_name": "company_handbook"
}
```

**Step 5 - Query with LLM**:
```json
{
  "provider": "openai",
  "model": "gpt-4o",
  "system_prompt": "Answer questions based on the retrieved context. Only use information from the context."
}
```

**Usage**:
```bash
curl -X POST .../execute -d '{
  "input": "What is the vacation policy?"
}'
```

### Example 4: Multi-LLM Comparison

**Workflow**:
```
Start → LLM (OpenAI) → End
     ↘ LLM (Claude) → End
     ↘ LLM (Gemini) → End
```

**Node Configs** (all with same prompt):
```json
{
  "system_prompt": "Explain quantum computing in simple terms."
}
```

Compare outputs from different models to find the best one for your use case.

### Example 5: Deep Agent Task

**Workflow**:
```
Start → Deep Agent → Function (Extract) → LLM (Summarize) → End
```

**Deep Agent Config**:
```json
{
  "model": "claude-sonnet-4-5-20250929",
  "max_iterations": 10
}
```

**Input**:
```
"Research the latest developments in renewable energy and create a summary report."
```

The agent will autonomously plan steps, search for information, and compile results.

---

## Best Practices

### Workflow Design

1. **Start Simple**
   - Begin with 2-3 nodes
   - Test each node individually
   - Expand complexity gradually

2. **Name Clearly**
   - Use descriptive workflow names
   - Label nodes with their purpose
   - Add workflow descriptions

3. **Organize with Tags**
   - Use tags like "production", "testing", "rag"
   - Filter workflows easily
   - Group related workflows

4. **Version Control**
   - Clone workflows before major changes
   - Keep templates of working configurations
   - Document your workflows

### LLM Node Configuration

1. **Choose the Right Model**
   - GPT-4o: Complex reasoning, coding
   - GPT-4o Mini: Simple tasks, cost-effective
   - Claude 3.5 Sonnet: Long context, analysis
   - Claude 3 Haiku: Speed, simple tasks

2. **Temperature Settings**
   - 0-0.3: Factual, deterministic tasks
   - 0.5-0.7: Balanced creativity/accuracy
   - 0.8-1.0: Creative, varied outputs
   - 1.0+: Highly creative, unpredictable

3. **System Prompts**
   - Be specific about the task
   - Include output format requirements
   - Add constraints if needed
   - Test and refine

4. **Token Limits**
   - Set based on expected output length
   - Monitor costs with large limits
   - Use streaming for better UX

### RAG Workflows

1. **Document Processing**
   - Chunk size: 500-1500 characters
   - Overlap: 100-300 characters
   - Clean text before processing
   - Remove headers/footers if needed

2. **Embeddings**
   - Use `text-embedding-3-small` for most cases
   - Use `text-embedding-3-large` for precision
   - Cache embeddings when possible
   - Batch process large document sets

3. **Vector Search**
   - Retrieve 3-5 chunks for most queries
   - Use similarity threshold if available
   - Re-rank results if needed
   - Provide context to LLM

4. **LLM Configuration**
   - Use models with long context (Claude)
   - Instruct to use only provided context
   - Ask for source citations
   - Handle "not in context" gracefully

### Performance

1. **Optimize Costs**
   - Use Mini models for simple tasks
   - Set reasonable token limits
   - Cache results when possible
   - Batch similar requests

2. **Improve Speed**
   - Use streaming for better UX
   - Choose faster models (Haiku, Mini)
   - Minimize sequential LLM calls
   - Process in parallel when possible

3. **Monitor Usage**
   - Check execution logs
   - Track token consumption
   - Identify bottlenecks
   - Optimize slow nodes

### Security

1. **API Keys**
   - Store in environment variables
   - Never commit to version control
   - Rotate regularly
   - Use separate keys for dev/prod

2. **Input Validation**
   - Validate user inputs
   - Sanitize file paths
   - Limit input length
   - Check file types

3. **Function Nodes**
   - Avoid executing untrusted code
   - Don't expose sensitive data
   - Limit file system access
   - Use timeouts

---

## Troubleshooting

### Common Issues

#### "No module named 'langgraph'"

**Problem**: LangGraph dependencies not installed

**Solution**:
```bash
cd /path/to/fastCMS
.venv/bin/pip install -r requirements.txt
```

#### "API key not configured"

**Problem**: Missing LLM provider API key

**Solution**: Add to `.env` file:
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

Then restart the server:
```bash
# Kill and restart
pkill -f uvicorn
.venv/bin/uvicorn app.main:app --reload
```

#### "Workflow type must be 'langgraph'"

**Problem**: Trying to use streaming on legacy workflow

**Solution**: Create new workflow with:
```json
{
  "workflow_type": "langgraph"
}
```

Or update existing workflow via API.

#### "Code generation failed"

**Problem**: Invalid workflow structure

**Solution**: Ensure:
1. At least one non-start/end node exists
2. All nodes have valid configuration
3. Edges connect valid nodes
4. No circular dependencies

#### Streaming Connection Drops

**Problem**: Network timeout or server restart

**Solution**: Implement reconnection:
```javascript
let retries = 0;
const maxRetries = 3;

function connect() {
  const eventSource = new EventSource(url);

  eventSource.onerror = () => {
    eventSource.close();
    if (retries < maxRetries) {
      retries++;
      setTimeout(connect, 5000);
    }
  };
}
```

#### Function Node Errors

**Common Issues**:
- Syntax errors in Python code
- Undefined variable access
- Missing `output` assignment

**Debug Steps**:
1. Test Python code separately
2. Add print statements (appear in logs)
3. Check execution logs for errors
4. Verify input data format

### Getting Help

1. **Check Logs**
   - Server logs: Check uvicorn output
   - Execution logs: Available in execution response
   - Browser console: Check for client errors

2. **Documentation**
   - Plugin README: `plugins/langgraph/README.md`
   - API Reference: This document
   - LangGraph Docs: https://python.langchain.com/docs/langgraph

3. **Testing**
   - Run test suite: `python plugins/langgraph/test_langgraph_integration.py`
   - Check individual node configs
   - Test with simple workflows first

---

## Advanced Topics

### Code Generation

The plugin generates executable Python code from your visual workflows:

**Visual Workflow** → **Python Code** → **LangGraph StateGraph** → **Execution**

View generated code by checking the `graph_code` field on workflow.

### State Management

LangGraph manages workflow state using:
- **TypedDict State**: Strongly-typed state object
- **add_messages**: Built-in message accumulation
- **Custom Fields**: Additional state fields as needed
- **Checkpointing**: Persistent state (future feature)

### Programmatic Workflow Creation

Create workflows entirely via API:

```python
import httpx

async def create_workflow():
    base = "http://localhost:8000/api/v1/plugins/langgraph"
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create workflow
    workflow = await httpx.post(
        f"{base}/workflows",
        json={
            "name": "AI Pipeline",
            "workflow_type": "langgraph"
        },
        headers=headers
    )
    wf_id = workflow.json()["id"]

    # 2. Add LLM node
    await httpx.post(
        f"{base}/workflows/{wf_id}/nodes",
        json={
            "node_type": "llm",
            "config": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "system_prompt": "Helpful assistant"
            }
        },
        headers=headers
    )

    # 3. Execute
    result = await httpx.post(
        f"{base}/workflows/{wf_id}/execute",
        json={"input": "Hello!"},
        headers=headers
    )
    print(result.json())
```

---

## Summary

The LangGraph plugin provides a powerful, production-ready platform for building AI workflows:

- ✅ **Easy to Use**: Visual editor for non-programmers
- ✅ **Powerful**: Full LangGraph and LangChain capabilities
- ✅ **Flexible**: Multi-LLM support, custom functions, RAG
- ✅ **Real-time**: Streaming execution with SSE
- ✅ **Scalable**: RESTful API for automation
- ✅ **Open Source**: Extend and customize

Start building AI workflows today! 🚀

---

**Related Documentation**:
- [Plugin Development](plugin-development.md)
- [API Reference](api-reference.md)
- [Authentication](authentication.md)
