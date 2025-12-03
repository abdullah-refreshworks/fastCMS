# LangGraph Plugin for FastCMS

A powerful visual workflow builder that integrates **LangGraph 1.0** and **LangChain** ecosystems, enabling you to build sophisticated AI workflows with streaming execution, multi-LLM support, and RAG capabilities.

## 🚀 Features

### Core Capabilities
- ✅ **Visual Workflow Builder** - Drag-and-drop interface powered by LangGraph StateGraph
- ✅ **Multi-LLM Support** - OpenAI, Anthropic (Claude), Google (Gemini)
- ✅ **Real-time Streaming** - Token-by-token streaming with Server-Sent Events (SSE)
- ✅ **Deep Agents** - Latest autonomous agent framework with planning capabilities
- ✅ **RAG Pipeline** - Complete document processing, embeddings, and vector stores
- ✅ **LangChain Ecosystem** - 500+ integrations available
- ✅ **Code Generation** - Converts visual workflows to executable Python code
- ✅ **Execution History** - Track all workflow runs with detailed event logs
- ✅ **RESTful API** - Full API access for programmatic control

### Advanced Features
- **Streaming Execution** - Watch workflows execute in real-time with token streaming
- **State Management** - LangGraph StateGraph with persistent checkpoints
- **Custom Functions** - Execute Python code with full LangChain context
- **Document Loaders** - PDF, DOCX, Web content processing
- **Text Splitters** - Intelligent chunking for large documents
- **Vector Stores** - FAISS, Pinecone, Chroma support
- **Embeddings** - OpenAI, Sentence Transformers integration
- **Multi-Provider** - Switch between LLM providers seamlessly

## 📋 Requirements

```bash
# Core dependencies
langgraph==1.0.3
langchain==1.1.0
langchain-openai==1.2.0
langchain-anthropic==1.2.0
langchain-google-genai==3.2.0
deepagents==0.2.8

# RAG & Document Processing
faiss-cpu==1.13.0
pypdf2==4.0.0
python-docx==1.2.0
beautifulsoup4==4.12.3
sentence-transformers==5.1.2

# ML Backend
torch==2.9.1
transformers==4.57.3
```

## 🛠️ Quick Start

### 1. Install Dependencies

All dependencies are included in the main `requirements.txt`:

```bash
.venv/bin/pip install -r requirements.txt
```

### 2. Configure API Keys

Set up your LLM provider API keys:

```bash
# .env file
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
```

### 3. Run Database Migrations

```bash
.venv/bin/alembic upgrade head
```

### 4. Access the Plugin

Navigate to: **http://localhost:8000/admin/langgraph**

## 🎯 Node Types

### 1. LLM Node (Brain Icon - Purple)

Execute language models with full streaming support.

**Supported Providers:**
- **OpenAI**: GPT-4o, GPT-4o Mini, GPT-4 Turbo, GPT-3.5 Turbo
- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku
- **Google**: Gemini Pro, Gemini Pro Vision

**Configuration:**
```json
{
  "provider": "openai",
  "model": "gpt-4o",
  "temperature": 0.7,
  "max_tokens": 1000,
  "system_prompt": "You are a helpful assistant..."
}
```

**Use Cases:**
- Text generation and summarization
- Question answering
- Content creation
- Translation
- Sentiment analysis

### 2. Deep Agent Node (Robot Icon - Teal)

Autonomous agent with planning and tool usage capabilities.

**Configuration:**
```json
{
  "model": "claude-sonnet-4-5-20250929",
  "max_iterations": 10
}
```

**Capabilities:**
- Multi-step planning
- Tool usage and function calling
- Autonomous task completion
- Self-correction

### 3. Document Loader Node (Document Icon - Green)

Load and process documents from various sources.

**Supported Formats:**
- **PDF**: PyPDFLoader
- **DOCX**: Docx2txtLoader
- **Web**: WebBaseLoader

**Configuration:**
```json
{
  "loader_type": "pdf",
  "source": "/path/to/document.pdf"
}
```

### 4. Text Splitter Node (Scissors Icon - Orange)

Intelligently chunk documents for processing.

**Configuration:**
```json
{
  "chunk_size": 1000,
  "chunk_overlap": 200
}
```

**Use Cases:**
- Prepare documents for embeddings
- Process large texts
- Optimize for vector search

### 5. Embedding Node (Vector Icon - Pink)

Generate embeddings for semantic search.

**Configuration:**
```json
{
  "provider": "openai",
  "model": "text-embedding-3-small"
}
```

### 6. Vector Store Node (Database Icon - Indigo)

Store and search document embeddings.

**Supported Stores:**
- **FAISS**: Local vector store
- **Pinecone**: Cloud vector database
- **Chroma**: Open-source vector store

**Configuration (Store):**
```json
{
  "provider": "faiss",
  "action": "store",
  "index_name": "my_documents"
}
```

**Configuration (Search):**
```json
{
  "provider": "faiss",
  "action": "search",
  "index_name": "my_documents"
}
```

### 7. Function Node (Code Icon - Blue)

Execute custom Python code with full LangChain context.

**Configuration:**
```json
{
  "code": "output = input.upper()"
}
```

**Available Variables:**
- `input`: Data from previous node
- `output`: Set this variable with your result
- Full Python standard library access

**Example - Data Transformation:**
```python
import json
data = json.loads(input)
output = {
    "processed": data.get("field"),
    "timestamp": datetime.now().isoformat()
}
```

### 8. Start & End Nodes

- **Start Node** (Play Icon - Green): Workflow entry point
- **End Node** (Stop Icon - Red): Workflow exit point

## 🔥 Example Workflows

### 1. RAG Pipeline (Retrieval-Augmented Generation)

Build a complete RAG system for document Q&A:

**Nodes:**
1. **Start** →
2. **Document Loader** (load PDF) →
3. **Text Splitter** (chunk documents) →
4. **Embedding** (generate vectors) →
5. **Vector Store** (store in FAISS) →
6. **LLM** (answer questions) →
7. **End**

**Use Case:** Upload documents and ask questions about their content.

### 2. Multi-LLM Comparison

Compare responses from different LLM providers:

**Nodes:**
1. **Start** →
2. **LLM** (OpenAI GPT-4o) →
3. **LLM** (Anthropic Claude) →
4. **LLM** (Google Gemini) →
5. **Function** (compare outputs) →
6. **End**

### 3. Deep Agent Workflow

Autonomous agent that plans and executes tasks:

**Nodes:**
1. **Start** →
2. **Deep Agent** (analyze task) →
3. **Function** (extract results) →
4. **LLM** (summarize) →
5. **End**

### 4. Content Pipeline

Generate, enhance, and format content:

**Nodes:**
1. **Start** →
2. **LLM** (draft content) →
3. **LLM** (improve grammar) →
4. **Function** (format as markdown) →
5. **End**

## 🌊 Streaming Execution

### Real-time Token Streaming

The plugin supports Server-Sent Events (SSE) for real-time streaming:

```bash
# Streaming endpoint
POST /api/v1/plugins/langgraph/workflows/{workflow_id}/execute/stream

# JavaScript client example
const eventSource = new EventSource('/api/v1/plugins/langgraph/workflows/{id}/execute/stream');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.type) {
    case 'token':
      // Real-time token from LLM
      console.log(data.content);
      break;
    case 'node_start':
      console.log(`Starting: ${data.node}`);
      break;
    case 'node_complete':
      console.log(`Completed: ${data.node}`);
      break;
    case 'execution_complete':
      console.log('Workflow finished!');
      break;
  }
};
```

### Event Types

| Event Type | Description |
|------------|-------------|
| `info` | Information message during setup |
| `node_start` | Node execution started |
| `token` | Individual token from LLM (streaming) |
| `node_complete` | Node execution completed |
| `execution_complete` | Entire workflow finished |
| `error` | Error occurred during execution |

## 📡 API Reference

### Workflows

#### Create Workflow
```bash
POST /api/v1/plugins/langgraph/workflows
Content-Type: application/json

{
  "name": "My RAG Pipeline",
  "description": "Document Q&A system",
  "workflow_type": "langgraph",
  "tags": ["rag", "qa"],
  "is_template": false
}
```

#### Execute Workflow (Non-Streaming)
```bash
POST /api/v1/plugins/langgraph/workflows/{workflow_id}/execute
Content-Type: application/json

{
  "input": "Your input text or question here"
}
```

**Response:**
```json
{
  "id": "execution_id",
  "workflow_id": "...",
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
      "type": "token",
      "content": "Hello",
      "timestamp": "2025-12-03T10:30:01"
    }
  ]
}
```

#### Execute Workflow (Streaming)
```bash
POST /api/v1/plugins/langgraph/workflows/{workflow_id}/execute/stream
Content-Type: application/json

{
  "input": "Your input text or question here"
}
```

**Response:** Server-Sent Events stream with real-time updates

### Nodes

#### Create Node
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

#### Delete Node
```bash
DELETE /api/v1/plugins/langgraph/workflows/{workflow_id}/nodes/{node_id}
```

### Edges

#### Create Edge
```bash
POST /api/v1/plugins/langgraph/workflows/{workflow_id}/edges

{
  "source_node_id": "node-1-id",
  "target_node_id": "node-2-id"
}
```

#### Delete Edge
```bash
DELETE /api/v1/plugins/langgraph/workflows/{workflow_id}/edges/{edge_id}
```

## 🏗️ Architecture

### Code Generation

The plugin generates executable LangGraph Python code from visual workflows:

**Visual Workflow** → **LangGraphCodeGenerator** → **Python Code** → **StateGraph** → **Execution**

Example generated code:

```python
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from typing import TypedDict, Annotated

class State(TypedDict):
    messages: Annotated[list, add_messages]
    input: Any
    output: Any

def node_llm_1(state: State) -> dict:
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

def build_graph():
    graph = StateGraph(State)
    graph.add_node("llm-1", node_llm_1)
    graph.add_edge(START, "llm-1")
    graph.add_edge("llm-1", END)
    return graph.compile()

app = build_graph()
```

### Execution Flow

1. **Visual Workflow** → User creates workflow in visual editor
2. **Code Generation** → `LangGraphCodeGenerator` converts to Python
3. **Graph Compilation** → LangGraph builds `StateGraph`
4. **Streaming Execution** → `astream_events()` provides real-time updates
5. **Event Processing** → SSE sends events to client
6. **Result Storage** → Execution saved to database

### State Management

LangGraph manages workflow state with:
- **TypedDict State**: Strongly-typed state object
- **add_messages**: Built-in message accumulation
- **Custom Fields**: Any additional state fields needed
- **Checkpointing**: Persistent state across executions

## 🔧 Development

### Project Structure

```
plugins/langgraph/
├── __init__.py
├── routes.py                      # API endpoints
├── models.py                      # SQLAlchemy models
├── executor_v2.py                 # LangGraph executor with streaming
├── admin_routes.py                # Admin UI routes
├── templates/                     # Jinja2 templates
│   └── visual_editor.html
├── langgraph_integration/
│   ├── __init__.py
│   └── code_generator.py          # Visual → Python code generator
└── README.md
```

### Key Components

**LangGraphCodeGenerator** (`code_generator.py`):
- Converts visual workflows to Python code
- Supports all LangChain integrations
- Generates StateGraph definitions
- Handles imports dynamically

**Executor V2** (`executor_v2.py`):
- Executes LangGraph workflows
- Streams events in real-time
- Supports both streaming and non-streaming modes
- Error handling and recovery

**API Routes** (`routes.py`):
- RESTful API endpoints
- SSE streaming support
- Authentication and authorization
- Database operations

### Database Models

**Workflow** - Stores workflow definitions
- `workflow_type`: 'custom' or 'langgraph'
- `graph_code`: Generated Python code (nullable)

**WorkflowNode** - Individual nodes in workflow
- `node_type`: llm, function, document_loader, etc.
- `config`: JSON configuration

**WorkflowEdge** - Connections between nodes

**WorkflowExecution** - Execution history
- `execution_log`: Complete event stream
- `output_data`: Final results

**WorkflowCheckpoint** - State persistence
- `checkpoint_data`: Serialized state
- `thread_id`: Execution thread identifier

## 🎓 Best Practices

### 1. LLM Node Configuration

✅ **Do:**
- Use GPT-4o for complex reasoning tasks
- Use Claude for long-context tasks (200K tokens)
- Use GPT-4o Mini for simple, fast tasks
- Write clear, specific system prompts
- Set appropriate token limits

❌ **Don't:**
- Use expensive models for simple tasks
- Set max_tokens too high unnecessarily
- Leave system prompts empty
- Use temperature > 1.0 for factual tasks

### 2. RAG Pipeline Design

✅ **Do:**
- Chunk documents at 500-1500 characters
- Use overlap of 100-200 characters
- Store embeddings in vector store
- Use semantic search with k=3-5 results
- Provide context to LLM with retrieved docs

❌ **Don't:**
- Process entire documents without chunking
- Skip the embedding step
- Retrieve too many or too few results
- Send raw chunks without formatting

### 3. Streaming Performance

✅ **Do:**
- Use streaming for user-facing applications
- Handle connection errors gracefully
- Buffer events on client side
- Show progress indicators

❌ **Don't:**
- Use streaming for batch processing
- Block UI during streaming
- Ignore error events
- Send huge chunks without chunking

### 4. Function Node Security

✅ **Do:**
- Validate input data
- Use try-except for error handling
- Keep functions focused and simple
- Test code before deploying

❌ **Don't:**
- Execute untrusted code
- Access file system without validation
- Make external API calls without rate limiting
- Store secrets in function code

## 🐛 Troubleshooting

### "No module named 'langgraph'"

**Solution:** Install dependencies
```bash
.venv/bin/pip install -r requirements.txt
```

### "API key not configured"

**Solution:** Set environment variables in `.env`:
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### "Workflow type must be 'langgraph'"

**Cause:** Trying to use streaming on legacy custom workflow

**Solution:** Create new workflow with `workflow_type: "langgraph"`

### Streaming connection drops

**Cause:** Network timeout or server restart

**Solution:** Implement reconnection logic:
```javascript
eventSource.onerror = (error) => {
  console.error('Stream error:', error);
  eventSource.close();
  // Retry connection after delay
  setTimeout(() => reconnect(), 5000);
};
```

### "Code generation failed"

**Cause:** Invalid workflow structure

**Solution:** Ensure:
1. At least one node exists
2. Nodes have valid configuration
3. Edges connect valid nodes
4. No circular dependencies

## 📊 Performance Tips

1. **Use appropriate models:**
   - GPT-4o Mini: 3-5x faster than GPT-4o
   - Claude 3 Haiku: Fastest for simple tasks
   - GPT-4o: Best for complex reasoning

2. **Optimize prompts:**
   - Shorter prompts = faster responses
   - Cache system prompts when possible
   - Use streaming for better UX

3. **RAG optimization:**
   - Use smaller chunk sizes (500-1000)
   - Limit vector search to k=3-5
   - Cache embeddings when possible

4. **Parallel execution:**
   - LangGraph can run independent nodes in parallel
   - Use conditional edges for branching

## 📄 License

Part of FastCMS - Open Source

## 🤝 Contributing

This is an open-source project. Contributions welcome!

## 🔗 Resources

- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [LangChain Documentation](https://python.langchain.com/docs/)
- [Deep Agents](https://github.com/anthropics/deepagents)
- [FastCMS Repository](https://github.com/yourusername/fastcms)

---

**Built with LangGraph 1.0 🚀**
