# LangGraph Plugin - Usage Guide

## Overview

The LangGraph plugin for FastCMS enables you to create, manage, and execute AI-powered workflows using a visual workflow builder. Build powerful automation by chaining together LLM calls, Python functions, and other processing nodes.

## Features

✅ **Visual Workflow Builder** - Drag-and-drop interface to build workflows
✅ **LLM Integration** - Direct OpenAI GPT integration (GPT-4, GPT-4o, GPT-3.5)
✅ **Python Functions** - Execute custom Python code in workflows
✅ **Real-time Execution** - Run workflows and see results instantly
✅ **Execution History** - Track all workflow runs with detailed logs
✅ **RESTful API** - Full API access for programmatic control

## Quick Start

### 1. Setup OpenAI API Key

The plugin requires an OpenAI API key to execute LLM nodes. Add your API key to the environment:

```bash
export OPENAI_API_KEY="sk-..."
```

Or add it to your `.env` file:

```
OPENAI_API_KEY=sk-...
```

### 2. Access the Plugin

1. Navigate to **http://localhost:8000/admin/langgraph**
2. Click **"New Workflow"** to create your first workflow

### 3. Build Your First Workflow

**Example: Simple AI Summarizer**

1. Click "New Workflow"
2. Name it "Text Summarizer"
3. Add nodes in order:
   - **Start Node** (entry point)
   - **LLM Node** (for summarization)
   - **End Node** (exit point)

4. Configure the LLM Node:
   - Click the gear icon ⚙️
   - Set Model: `gpt-4o-mini`
   - System Prompt: `You are a helpful assistant that summarizes text concisely.`
   - Temperature: `0.7`
   - Max Tokens: `500`

5. Click **"Save"** to save the workflow

6. Click **"Run"** and enter text to summarize

## Node Types

### 1. LLM Node (Brain Icon - Purple)

Executes OpenAI GPT models with your configured prompts.

**Configuration:**
- **Model**: Choose from GPT-4o, GPT-4o Mini, GPT-4 Turbo, or GPT-3.5 Turbo
- **System Prompt**: Instructions for the AI (e.g., "You are a helpful assistant...")
- **Temperature**: Controls randomness (0-2, default: 0.7)
- **Max Tokens**: Maximum length of response (default: 1000)

**Example Use Cases:**
- Text summarization
- Content generation
- Question answering
- Translation
- Sentiment analysis

### 2. Function Node (Code Icon - Blue)

Execute custom Python code to process data.

**Configuration:**
- **Python Code**: Write your processing logic

**Available Variables:**
- `input`: Data from previous node
- `output`: Set this variable with your result

**Example:**

```python
# Convert input to uppercase
output = input.upper()
```

```python
# Extract specific data
import json
data = json.loads(input)
output = data.get('field_name', 'default')
```

```python
# Transform list
output = [item.strip() for item in input.split(',')]
```

**Security Note:** Code runs in a restricted environment with basic Python builtins only.

### 3. Start Node (Play Icon - Green)

Marks the entry point of the workflow. The workflow executor begins here.

### 4. End Node (Stop Icon - Red)

Marks the exit point of the workflow. Optional - workflows can end without an explicit end node.

## Workflow Execution

### Running a Workflow

1. Open your workflow in the editor
2. Click the **"Run"** button
3. Enter input data when prompted
4. View the execution result

### Execution Flow

1. **Input Processing**: Your input enters at the Start node
2. **Node Execution**: Each node processes data sequentially
3. **Data Flow**: Output from one node becomes input for the next
4. **Result**: Final output is displayed with execution logs

### Example Workflows

#### Workflow 1: AI Content Enhancer

**Nodes:**
1. Start → 2. LLM (improve grammar) → 3. LLM (make professional) → 4. End

**Node 2 Config:**
```
System: "Fix grammar and spelling errors in the text"
Model: gpt-4o-mini
```

**Node 3 Config:**
```
System: "Make the text more professional and polished"
Model: gpt-4o-mini
```

#### Workflow 2: Data Processor + AI

**Nodes:**
1. Start → 2. Function (clean data) → 3. LLM (analyze) → 4. End

**Node 2 Code:**
```python
# Clean and format input
lines = input.split('\n')
cleaned = [line.strip() for line in lines if line.strip()]
output = '\n'.join(cleaned)
```

**Node 3 Config:**
```
System: "Analyze the data and provide insights"
Model: gpt-4o
```

#### Workflow 3: Multi-Language Translator

**Nodes:**
1. Start → 2. LLM (translate to Spanish) → 3. LLM (translate to French) → 4. Function (format results) → 5. End

## API Reference

### Workflows

**Create Workflow:**
```bash
POST /api/v1/plugins/langgraph/workflows
Content-Type: application/json

{
  "name": "My Workflow",
  "description": "Description here",
  "tags": ["automation", "ai"],
  "is_template": false
}
```

**List Workflows:**
```bash
GET /api/v1/plugins/langgraph/workflows
```

**Get Workflow:**
```bash
GET /api/v1/plugins/langgraph/workflows/{workflow_id}
```

**Update Workflow:**
```bash
PUT /api/v1/plugins/langgraph/workflows/{workflow_id}
```

**Delete Workflow:**
```bash
DELETE /api/v1/plugins/langgraph/workflows/{workflow_id}
```

### Nodes

**Create Node:**
```bash
POST /api/v1/plugins/langgraph/workflows/{workflow_id}/nodes
Content-Type: application/json

{
  "workflow_id": "...",
  "node_type": "llm",
  "label": "Summarizer",
  "position_x": 0,
  "position_y": 0,
  "config": {
    "model": "gpt-4o-mini",
    "system_prompt": "You are a helpful assistant.",
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

**List Nodes:**
```bash
GET /api/v1/plugins/langgraph/workflows/{workflow_id}/nodes
```

**Update Node:**
```bash
PUT /api/v1/plugins/langgraph/workflows/{workflow_id}/nodes/{node_id}
```

**Delete Node:**
```bash
DELETE /api/v1/plugins/langgraph/workflows/{workflow_id}/nodes/{node_id}
```

### Edges

**Create Edge (Connection):**
```bash
POST /api/v1/plugins/langgraph/workflows/{workflow_id}/edges
Content-Type: application/json

{
  "workflow_id": "...",
  "source_node_id": "node1_id",
  "target_node_id": "node2_id"
}
```

**List Edges:**
```bash
GET /api/v1/plugins/langgraph/workflows/{workflow_id}/edges
```

**Delete Edge:**
```bash
DELETE /api/v1/plugins/langgraph/workflows/{workflow_id}/edges/{edge_id}
```

### Execution

**Execute Workflow:**
```bash
POST /api/v1/plugins/langgraph/workflows/{workflow_id}/execute
Content-Type: application/json

{
  "input": "Your input text or data here"
}
```

**Response:**
```json
{
  "id": "execution_id",
  "workflow_id": "...",
  "status": "completed",
  "output_data": "Result from workflow",
  "execution_log": [
    {
      "timestamp": "2024-01-01T12:00:00",
      "node_id": "...",
      "message": "Node executed successfully"
    }
  ],
  "started_at": "2024-01-01T12:00:00",
  "completed_at": "2024-01-01T12:00:05"
}
```

**List Executions:**
```bash
GET /api/v1/plugins/langgraph/workflows/{workflow_id}/executions
```

## Best Practices

### 1. LLM Node Configuration

- **Use appropriate models**: GPT-4o for complex tasks, GPT-4o Mini for simple tasks
- **Write clear system prompts**: Be specific about what you want the AI to do
- **Set reasonable token limits**: Balance between completeness and cost
- **Adjust temperature**: Lower (0-0.3) for factual tasks, higher (0.7-1.0) for creative tasks

### 2. Function Nodes

- **Keep functions focused**: Each function should do one thing well
- **Handle errors**: Add try-except blocks for robustness
- **Document your code**: Add comments for complex logic
- **Test separately**: Test Python code before adding to workflow

### 3. Workflow Design

- **Start simple**: Begin with 2-3 nodes and expand
- **Name nodes clearly**: Use descriptive labels for each node
- **Test incrementally**: Test after adding each node
- **Monitor execution**: Check logs to debug issues

### 4. Performance

- **Chain efficiently**: Avoid unnecessary LLM calls
- **Cache results**: Reuse outputs when possible
- **Optimize prompts**: Shorter prompts = faster + cheaper
- **Batch processing**: Group similar tasks together

## Troubleshooting

### "OpenAI API key not configured"

**Solution:** Set the `OPENAI_API_KEY` environment variable:
```bash
export OPENAI_API_KEY="sk-..."
```

### "Workflow execution failed"

**Check:**
1. All nodes are properly configured
2. Node connections are valid
3. Python code in function nodes is syntactically correct
4. LLM node prompts are not empty

### "Max iterations reached"

**Cause:** Circular reference in workflow (node A → node B → node A)

**Solution:** Remove circular connections between nodes

### Function node errors

**Common issues:**
- Syntax errors in Python code
- Accessing undefined variables
- Missing `output` variable assignment

**Debug:**
1. Test Python code separately first
2. Add print statements (they appear in logs)
3. Check execution logs for detailed errors

## Advanced Usage

### Programmatic Workflow Creation

```python
import httpx

async def create_ai_workflow():
    base_url = "http://localhost:8000/api/v1/plugins/langgraph"
    headers = {"Authorization": f"Bearer {access_token}"}

    # Create workflow
    workflow = await httpx.post(
        f"{base_url}/workflows",
        json={"name": "AI Pipeline", "description": "Automated workflow"},
        headers=headers
    )
    workflow_id = workflow.json()["id"]

    # Add LLM node
    node = await httpx.post(
        f"{base_url}/workflows/{workflow_id}/nodes",
        json={
            "node_type": "llm",
            "label": "Analyzer",
            "position_x": 0,
            "position_y": 0,
            "config": {
                "model": "gpt-4o-mini",
                "system_prompt": "Analyze the input",
                "temperature": 0.7,
                "max_tokens": 1000
            }
        },
        headers=headers
    )

    # Execute
    result = await httpx.post(
        f"{base_url}/workflows/{workflow_id}/execute",
        json={"input": "Test data"},
        headers=headers
    )
    print(result.json())
```

### Webhook Integration (Future)

Coming soon: Trigger workflows via webhooks for event-driven automation.

## Support & Documentation

- **Plugin Repository**: `plugins/langgraph/`
- **Models**: `plugins/langgraph/models.py`
- **API Routes**: `plugins/langgraph/routes.py`
- **Executor**: `plugins/langgraph/executor.py`

## License

Part of FastCMS - see main project license.
