# LangGraph Plugin Implementation Plan

## Overview

This document outlines the implementation plan for the LangGraph visual workflow builder plugin for FastCMS. The plugin will provide a drag-and-drop interface (similar to Flowise/n8n) for building AI agent workflows using LangGraph, while maintaining simplicity by using Jinja2 templates and **Rete.js via CDN** for the visual editor.

**Key Design Principle: Python-Only Deployment** - No Node.js, no npm, no build process required!

---

## Technology Stack

### Backend (Python Only!)
- **FastAPI**: API endpoints for workflow CRUD operations
- **SQLAlchemy**: Database models for workflows, nodes, edges
- **LangGraph**: Core workflow execution engine
- **LangChain**: Integration with LLMs and tools
- **Pydantic**: Schema validation

### Frontend (No Build Required!)
- **Jinja2**: Server-side HTML templating (served by FastAPI)
- **Alpine.js**: Reactive state management (via CDN, already in FastCMS)
- **Tailwind CSS**: Styling (via CDN, already in FastCMS)
- **Rete.js**: Visual node editor (via CDN - **NEW!**)
  - Version: 2.0.6
  - 11.6k GitHub stars
  - Actively maintained (updated Jan 2025)
  - Purpose-built for visual programming interfaces
  - No framework required - works with vanilla JavaScript

### Why Rete.js?
✅ **CDN-based** - No npm, no build step
✅ **Purpose-built** for workflow editors (dataflow & control flow)
✅ **Well-documented** - https://retejs.org/docs/
✅ **Actively maintained** - Latest release June 2024
✅ **Perfect for LangGraph** - Designed for node-based visual programming
✅ **Python-only deployment** - Just include script tags!

### Deployment Environment
```bash
# Only Python needed!
python -m venv .venv
pip install -r requirements.txt
uvicorn app.main:app

# NO Node.js, NO npm, NO webpack!
```

---

## Plugin Architecture

### Directory Structure

```
plugins/
└── langgraph/
    ├── __init__.py                 # Plugin entry point
    ├── plugin.py                   # LangGraphPlugin class
    ├── config.py                   # Plugin configuration
    ├── requirements.txt            # Python packages only!
    │
    ├── models.py                   # Database models
    │   ├── Workflow
    │   ├── WorkflowNode
    │   ├── WorkflowEdge
    │   └── WorkflowExecution
    │
    ├── schemas.py                  # Pydantic schemas
    │   ├── WorkflowCreate
    │   ├── NodeCreate
    │   ├── EdgeCreate
    │   └── ExecutionResponse
    │
    ├── routes.py                   # API endpoints
    │   ├── POST /workflows
    │   ├── GET /workflows
    │   ├── PUT /workflows/{id}
    │   ├── DELETE /workflows/{id}
    │   ├── POST /workflows/{id}/execute
    │   ├── GET /workflows/{id}/executions
    │   └── GET /templates
    │
    ├── admin_routes.py             # Admin UI routes (Jinja2)
    │   ├── GET /admin/langgraph
    │   ├── GET /admin/langgraph/editor/{workflow_id}
    │   └── GET /admin/langgraph/executions
    │
    ├── services/
    │   ├── workflow_service.py     # Business logic
    │   ├── execution_service.py    # LangGraph execution
    │   ├── node_registry.py        # Available node types
    │   └── template_service.py     # Workflow templates
    │
    ├── templates/                  # Jinja2 templates
    │   ├── workflows.html          # List of workflows
    │   ├── editor.html             # Visual workflow editor (Rete.js)
    │   └── execution.html          # Execution results
    │
    ├── static/                     # Static files (vanilla JS only!)
    │   ├── css/
    │   │   └── langgraph.css       # Plugin-specific styles
    │   └── js/
    │       ├── editor.js           # Rete.js integration
    │       ├── nodes.js            # Node definitions
    │       └── execution.js        # Workflow execution UI
    │
    ├── migrations/                 # Alembic migrations
    │   └── 001_initial_schema.py
    │
    └── README.md                   # Plugin documentation
```

**Note**: No `node_modules/`, no `package.json`, no build tools!

---

## Database Schema

### Workflows Table

```sql
CREATE TABLE langgraph_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_template BOOLEAN DEFAULT FALSE,
    tags JSONB DEFAULT '[]',
    rete_data JSONB DEFAULT '{}',  -- Full Rete.js editor state
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Nodes Table

```sql
CREATE TABLE langgraph_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES langgraph_workflows(id) ON DELETE CASCADE,
    node_type VARCHAR(50) NOT NULL,  -- 'agent', 'tool', 'conditional', 'function'
    label VARCHAR(255) NOT NULL,
    position_x FLOAT NOT NULL,
    position_y FLOAT NOT NULL,
    config JSONB NOT NULL,  -- Node-specific configuration
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_workflow_nodes (workflow_id)
);
```

### Edges Table

```sql
CREATE TABLE langgraph_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES langgraph_workflows(id) ON DELETE CASCADE,
    source_node_id UUID NOT NULL REFERENCES langgraph_nodes(id) ON DELETE CASCADE,
    target_node_id UUID NOT NULL REFERENCES langgraph_nodes(id) ON DELETE CASCADE,
    source_output VARCHAR(50),  -- Which output socket
    target_input VARCHAR(50),   -- Which input socket
    condition JSONB,  -- For conditional edges
    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_workflow_edges (workflow_id),
    UNIQUE (workflow_id, source_node_id, target_node_id, source_output, target_input)
);
```

### Executions Table

```sql
CREATE TABLE langgraph_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES langgraph_workflows(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    input_data JSONB NOT NULL,
    output_data JSONB,
    status VARCHAR(20) NOT NULL,  -- 'pending', 'running', 'completed', 'failed'
    error TEXT,
    execution_log JSONB DEFAULT '[]',  -- Step-by-step execution log
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,

    INDEX idx_workflow_executions (workflow_id),
    INDEX idx_user_executions (user_id),
    INDEX idx_status (status)
);
```

---

## Visual Editor Implementation with Rete.js

### Editor Template (Jinja2)

```html
<!-- templates/editor.html -->
{% extends "base.html" %}

{% block title %}Workflow Editor{% endblock %}

{% block head %}
<!-- Rete.js via CDN - No npm needed! -->
<script src="https://cdn.jsdelivr.net/npm/rete@2.0.6/rete.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/rete-area-plugin@2.0.5/rete-area-plugin.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/rete-connection-plugin@2.0.3/rete-connection-plugin.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/rete-render-utils@2.0.2/rete-render-utils.min.js"></script>

<!-- Plugin-specific CSS -->
<link rel="stylesheet" href="/static/plugins/langgraph/css/langgraph.css">
{% endblock %}

{% block content %}
<div class="h-screen flex flex-col" x-data="workflowEditor">
  <!-- Toolbar -->
  <div class="bg-white border-b px-4 py-3 flex items-center justify-between">
    <div class="flex items-center space-x-4">
      <a href="/admin/langgraph" class="text-gray-600 hover:text-gray-900">
        <i class="fas fa-arrow-left"></i>
      </a>
      <input
        type="text"
        x-model="workflow.name"
        @blur="saveWorkflow()"
        class="text-xl font-bold border-none focus:outline-none focus:ring-2 focus:ring-blue-500 rounded px-2"
        placeholder="Untitled Workflow"
      />
    </div>

    <div class="flex items-center space-x-2">
      <button @click="saveWorkflow()" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
        <i class="fas fa-save mr-2"></i>Save
      </button>
      <button @click="executeWorkflow()" class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700">
        <i class="fas fa-play mr-2"></i>Run
      </button>
      <button @click="exportWorkflow()" class="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700">
        <i class="fas fa-download mr-2"></i>Export
      </button>
    </div>
  </div>

  <!-- Rete.js Editor Container -->
  <div id="rete-editor" class="flex-1 bg-gray-50"></div>

  <!-- Mini-map (optional) -->
  <div id="rete-minimap" class="absolute bottom-4 right-4 w-64 h-40 bg-white border shadow-lg rounded"></div>
</div>
{% endblock %}

{% block scripts %}
<!-- Our Rete.js integration -->
<script src="/static/plugins/langgraph/js/nodes.js"></script>
<script src="/static/plugins/langgraph/js/editor.js"></script>
<script src="/static/plugins/langgraph/js/execution.js"></script>
{% endblock %}
```

---

## Rete.js Integration (Vanilla JavaScript)

### 1. Node Definitions

```javascript
// static/js/nodes.js

// Base node class for all LangGraph nodes
class BaseNode extends Rete.Node {
  constructor(label, type) {
    super(label);
    this.type = type;
  }

  // Override to customize node appearance
  data = {};
}

// Agent Node (LLM)
class AgentNode extends BaseNode {
  constructor() {
    super('Agent');
    this.type = 'agent';

    // Input socket
    const input = new Rete.Input('input', 'Input', Rete.Socket.anyTypeSocket());
    this.addInput(input);

    // Output socket
    const output = new Rete.Output('output', 'Output', Rete.Socket.anyTypeSocket());
    this.addOutput(output);

    // Node configuration
    this.data = {
      model: 'gpt-4',
      systemPrompt: 'You are a helpful assistant.',
      temperature: 0.7,
      maxTokens: 1000
    };
  }

  // Execution logic
  async worker(node, inputs, outputs) {
    const input = inputs['input'][0];
    // Call LLM via backend API
    const result = await callLLM(node.data, input);
    outputs['output'] = result;
  }
}

// Tool Node
class ToolNode extends BaseNode {
  constructor() {
    super('Tool');
    this.type = 'tool';

    const input = new Rete.Input('input', 'Input', Rete.Socket.anyTypeSocket());
    this.addInput(input);

    const output = new Rete.Output('output', 'Result', Rete.Socket.anyTypeSocket());
    this.addOutput(output);

    this.data = {
      toolType: 'web_search',
      config: {}
    };
  }

  async worker(node, inputs, outputs) {
    const input = inputs['input'][0];
    const result = await executeTool(node.data.toolType, input);
    outputs['output'] = result;
  }
}

// Conditional Node (Router)
class ConditionalNode extends BaseNode {
  constructor() {
    super('Conditional');
    this.type = 'conditional';

    const input = new Rete.Input('input', 'Input', Rete.Socket.anyTypeSocket());
    this.addInput(input);

    // Multiple outputs for different conditions
    const trueOutput = new Rete.Output('true', 'True', Rete.Socket.anyTypeSocket());
    const falseOutput = new Rete.Output('false', 'False', Rete.Socket.anyTypeSocket());
    this.addOutput(trueOutput);
    this.addOutput(falseOutput);

    this.data = {
      condition: 'input.length > 0'
    };
  }

  async worker(node, inputs, outputs) {
    const input = inputs['input'][0];
    const result = evaluateCondition(node.data.condition, input);

    if (result) {
      outputs['true'] = input;
    } else {
      outputs['false'] = input;
    }
  }
}

// Function Node (Custom Code)
class FunctionNode extends BaseNode {
  constructor() {
    super('Function');
    this.type = 'function';

    const input = new Rete.Input('input', 'Input', Rete.Socket.anyTypeSocket());
    this.addInput(input);

    const output = new Rete.Output('output', 'Output', Rete.Socket.anyTypeSocket());
    this.addOutput(output);

    this.data = {
      code: '// Your function here\nreturn input;'
    };
  }

  async worker(node, inputs, outputs) {
    const input = inputs['input'][0];
    const result = await executeFunction(node.data.code, input);
    outputs['output'] = result;
  }
}

// Start Node
class StartNode extends BaseNode {
  constructor() {
    super('Start');
    this.type = 'start';

    const output = new Rete.Output('output', 'Start', Rete.Socket.anyTypeSocket());
    this.addOutput(output);

    this.data = {
      inputSchema: {}
    };
  }
}

// End Node
class EndNode extends BaseNode {
  constructor() {
    super('End');
    this.type = 'end';

    const input = new Rete.Input('input', 'Result', Rete.Socket.anyTypeSocket());
    this.addInput(input);

    this.data = {
      outputSchema: {}
    };
  }
}
```

### 2. Editor Initialization

```javascript
// static/js/editor.js

let editor = null;
let engine = null;

document.addEventListener('alpine:init', () => {
  Alpine.data('workflowEditor', () => ({
    workflow: {
      id: null,
      name: 'Untitled Workflow',
      description: ''
    },

    async init() {
      // Initialize Rete.js editor
      await initializeReteEditor();

      // Load workflow if editing existing
      const workflowId = this.getWorkflowIdFromURL();
      if (workflowId) {
        await this.loadWorkflow(workflowId);
      }
    },

    getWorkflowIdFromURL() {
      const path = window.location.pathname;
      const match = path.match(/\/editor\/([a-f0-9-]+)/);
      return match ? match[1] : null;
    },

    async loadWorkflow(id) {
      try {
        const response = await fetch(`/api/v1/plugins/langgraph/workflows/${id}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        });

        if (!response.ok) throw new Error('Failed to load workflow');

        const data = await response.json();
        this.workflow = data;

        // Load into Rete editor
        if (data.rete_data) {
          await editor.fromJSON(data.rete_data);
        }

        showToast('Workflow loaded successfully', 'success');
      } catch (error) {
        showToast('Failed to load workflow: ' + error.message, 'error');
      }
    },

    async saveWorkflow() {
      try {
        // Export Rete editor state
        const reteData = await editor.toJSON();

        const payload = {
          name: this.workflow.name,
          description: this.workflow.description,
          rete_data: reteData
        };

        const method = this.workflow.id ? 'PUT' : 'POST';
        const url = this.workflow.id
          ? `/api/v1/plugins/langgraph/workflows/${this.workflow.id}`
          : '/api/v1/plugins/langgraph/workflows';

        const response = await fetch(url, {
          method,
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          },
          body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error('Failed to save workflow');

        const data = await response.json();
        this.workflow.id = data.id;

        showToast('Workflow saved successfully', 'success');
      } catch (error) {
        showToast('Failed to save workflow: ' + error.message, 'error');
      }
    },

    async executeWorkflow() {
      if (!this.workflow.id) {
        showToast('Please save the workflow first', 'warning');
        return;
      }

      // Show input modal
      const input = prompt('Enter input for workflow:');
      if (!input) return;

      try {
        const response = await fetch(`/api/v1/plugins/langgraph/workflows/${this.workflow.id}/execute`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          },
          body: JSON.stringify({ input })
        });

        if (!response.ok) throw new Error('Execution failed');

        const result = await response.json();

        // Show result modal
        showExecutionResult(result);
      } catch (error) {
        showToast('Execution failed: ' + error.message, 'error');
      }
    },

    async exportWorkflow() {
      const reteData = await editor.toJSON();
      const dataStr = JSON.stringify(reteData, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });

      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${this.workflow.name || 'workflow'}.json`;
      link.click();

      showToast('Workflow exported', 'success');
    }
  }));
});

// Initialize Rete.js Editor
async function initializeReteEditor() {
  const container = document.getElementById('rete-editor');

  // Create editor
  editor = new Rete.NodeEditor('langgraph@0.1.0', container);

  // Register node components
  editor.register(new AgentNode());
  editor.register(new ToolNode());
  editor.register(new ConditionalNode());
  editor.register(new FunctionNode());
  editor.register(new StartNode());
  editor.register(new EndNode());

  // Add plugins
  const { AreaPlugin } = ReteAreaPlugin;
  const { ConnectionPlugin } = ReteConnectionPlugin;
  const { RenderPlugin } = ReteRenderUtils;

  // Area plugin (zoom, pan, drag)
  const areaPlugin = new AreaPlugin(container);
  editor.use(areaPlugin);

  // Connection plugin (edges)
  const connectionPlugin = new ConnectionPlugin();
  editor.use(connectionPlugin);

  // Rendering
  const renderPlugin = new RenderPlugin();
  editor.use(renderPlugin);

  // Engine for processing
  engine = new Rete.Engine('langgraph@0.1.0');
  engine.register(new AgentNode());
  engine.register(new ToolNode());
  engine.register(new ConditionalNode());
  engine.register(new FunctionNode());
  engine.register(new StartNode());
  engine.register(new EndNode());

  // Context menu for adding nodes
  setupContextMenu(editor, areaPlugin);

  // Auto-arrange nodes
  setupAutoArrange(editor, areaPlugin);

  console.log('✅ Rete.js editor initialized');
}

// Context menu for adding nodes
function setupContextMenu(editor, areaPlugin) {
  areaPlugin.addPipe((context) => {
    if (context.type === 'contextmenu') {
      context.data.event.preventDefault();

      // Show custom context menu
      const menu = createContextMenu([
        { label: 'Agent Node', action: () => addNode(editor, 'agent') },
        { label: 'Tool Node', action: () => addNode(editor, 'tool') },
        { label: 'Conditional Node', action: () => addNode(editor, 'conditional') },
        { label: 'Function Node', action: () => addNode(editor, 'function') },
        { label: 'Start Node', action: () => addNode(editor, 'start') },
        { label: 'End Node', action: () => addNode(editor, 'end') }
      ]);

      menu.style.left = context.data.event.clientX + 'px';
      menu.style.top = context.data.event.clientY + 'px';
      document.body.appendChild(menu);
    }
    return context;
  });
}

// Add node to editor
async function addNode(editor, type) {
  let node;

  switch (type) {
    case 'agent':
      node = new AgentNode();
      break;
    case 'tool':
      node = new ToolNode();
      break;
    case 'conditional':
      node = new ConditionalNode();
      break;
    case 'function':
      node = new FunctionNode();
      break;
    case 'start':
      node = new StartNode();
      break;
    case 'end':
      node = new EndNode();
      break;
  }

  if (node) {
    await editor.addNode(node);
    editor.view.updateConnections({ node });
  }
}

// Create context menu
function createContextMenu(items) {
  const menu = document.createElement('div');
  menu.className = 'absolute bg-white shadow-lg rounded-lg py-2 z-50 border border-gray-200';
  menu.style.minWidth = '200px';

  items.forEach(item => {
    const button = document.createElement('button');
    button.className = 'w-full text-left px-4 py-2 hover:bg-gray-100 text-sm';
    button.textContent = item.label;
    button.onclick = () => {
      item.action();
      menu.remove();
    };
    menu.appendChild(button);
  });

  // Remove on click outside
  setTimeout(() => {
    document.addEventListener('click', () => menu.remove(), { once: true });
  }, 100);

  return menu;
}
```

### 3. Execution Visualization

```javascript
// static/js/execution.js

function showExecutionResult(result) {
  // Create modal
  const modal = document.createElement('div');
  modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
  modal.innerHTML = `
    <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-auto">
      <div class="border-b px-6 py-4 flex items-center justify-between">
        <h2 class="text-xl font-bold">Execution Result</h2>
        <button onclick="this.closest('.fixed').remove()" class="text-gray-500 hover:text-gray-700">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <div class="p-6">
        <div class="mb-4">
          <span class="inline-block px-3 py-1 rounded-full text-sm font-semibold ${
            result.status === 'completed' ? 'bg-green-100 text-green-800' :
            result.status === 'failed' ? 'bg-red-100 text-red-800' :
            'bg-yellow-100 text-yellow-800'
          }">
            ${result.status.toUpperCase()}
          </span>
        </div>

        ${result.error ? `
          <div class="bg-red-50 border border-red-200 rounded p-4 mb-4">
            <p class="text-red-800 font-semibold mb-2">Error</p>
            <p class="text-red-700 text-sm">${result.error}</p>
          </div>
        ` : ''}

        <div class="mb-4">
          <h3 class="font-semibold mb-2">Output</h3>
          <pre class="bg-gray-50 border rounded p-4 text-sm overflow-auto">${
            JSON.stringify(result.output_data, null, 2)
          }</pre>
        </div>

        ${result.execution_log && result.execution_log.length > 0 ? `
          <div>
            <h3 class="font-semibold mb-2">Execution Log</h3>
            <div class="space-y-2">
              ${result.execution_log.map((log, i) => `
                <div class="bg-gray-50 border rounded p-3 text-sm">
                  <div class="flex items-center justify-between mb-1">
                    <span class="font-medium">${log.node_name || `Step ${i + 1}`}</span>
                    <span class="text-xs text-gray-500">${log.timestamp || ''}</span>
                  </div>
                  <pre class="text-xs text-gray-700">${JSON.stringify(log.data, null, 2)}</pre>
                </div>
              `).join('')}
            </div>
          </div>
        ` : ''}
      </div>

      <div class="border-t px-6 py-4 flex justify-end">
        <button onclick="this.closest('.fixed').remove()" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
          Close
        </button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);
}

// Helper functions for node execution
async function callLLM(config, input) {
  const response = await fetch('/api/v1/plugins/langgraph/execute/llm', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    },
    body: JSON.stringify({ config, input })
  });

  const data = await response.json();
  return data.output;
}

async function executeTool(toolType, input) {
  const response = await fetch('/api/v1/plugins/langgraph/execute/tool', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    },
    body: JSON.stringify({ toolType, input })
  });

  const data = await response.json();
  return data.output;
}

function evaluateCondition(condition, input) {
  try {
    // Safe evaluation in sandboxed context
    const func = new Function('input', `return ${condition}`);
    return func(input);
  } catch (error) {
    console.error('Condition evaluation error:', error);
    return false;
  }
}

async function executeFunction(code, input) {
  // Execute on backend for security
  const response = await fetch('/api/v1/plugins/langgraph/execute/function', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    },
    body: JSON.stringify({ code, input })
  });

  const data = await response.json();
  return data.output;
}
```

---

## CSS Styling

```css
/* static/css/langgraph.css */

/* Rete.js editor styling */
#rete-editor {
  position: relative;
  background:
    linear-gradient(90deg, rgba(0, 0, 0, 0.03) 1px, transparent 1px),
    linear-gradient(rgba(0, 0, 0, 0.03) 1px, transparent 1px);
  background-size: 20px 20px;
  background-color: #f9fafb;
}

/* Custom node styling for Rete.js */
.rete-node {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.2s;
}

.rete-node:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Node types colors */
.rete-node[data-type="agent"] {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border: 2px solid #3b82f6;
}

.rete-node[data-type="tool"] {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  border: 2px solid #10b981;
}

.rete-node[data-type="conditional"] {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border: 2px solid #f59e0b;
}

.rete-node[data-type="function"] {
  background: linear-gradient(135deg, #e9d5ff 0%, #d8b4fe 100%);
  border: 2px solid #a855f7;
}

.rete-node[data-type="start"] {
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
  border: 2px solid #6b7280;
}

.rete-node[data-type="end"] {
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
  border: 2px solid #6b7280;
}

/* Connection lines */
.rete-connection path {
  stroke: #6366f1;
  stroke-width: 2px;
  fill: none;
}

.rete-connection:hover path {
  stroke: #4f46e5;
  stroke-width: 3px;
}

/* Sockets (connection points) */
.rete-socket {
  width: 14px;
  height: 14px;
  border: 2px solid white;
  background: #6366f1;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s;
}

.rete-socket:hover {
  transform: scale(1.3);
  background: #4f46e5;
}

/* Minimap */
#rete-minimap {
  pointer-events: none;
  opacity: 0.8;
}

/* Context menu */
.rete-context-menu {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  padding: 8px 0;
  min-width: 200px;
}

.rete-context-menu-item {
  padding: 8px 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.rete-context-menu-item:hover {
  background: #f3f4f6;
}

/* Execution animation */
@keyframes node-executing {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.7);
  }
  50% {
    box-shadow: 0 0 0 10px rgba(99, 102, 241, 0);
  }
}

.rete-node.executing {
  animation: node-executing 1s infinite;
}
```

---

## LangGraph Node Types

### 1. Agent Node
- **Purpose**: LLM-powered agent that processes input
- **Config**: Model, system prompt, temperature, max tokens
- **Sockets**: 1 input, 1 output
- **Execution**: Calls LLM with context

### 2. Tool Node
- **Purpose**: Executes a specific tool/function
- **Config**: Tool type (web search, calculator, API call, etc.)
- **Sockets**: 1 input, 1 output
- **Execution**: Runs tool and returns result

### 3. Conditional Node
- **Purpose**: Routes flow based on conditions
- **Config**: Condition expression
- **Sockets**: 1 input, 2+ outputs (true/false/custom)
- **Execution**: Evaluates condition and routes to appropriate edge

### 4. Function Node
- **Purpose**: Custom Python code execution
- **Config**: Python code snippet
- **Sockets**: 1 input, 1 output
- **Execution**: Executes code in sandboxed environment

### 5. Human-in-the-Loop Node
- **Purpose**: Pauses execution for human input
- **Config**: Prompt for human, timeout
- **Sockets**: 1 input, 1 output
- **Execution**: Waits for user input before continuing

### 6. Start/End Nodes
- **Purpose**: Define workflow entry and exit points
- **Config**: Input/output schema
- **Sockets**: Start (0 input, 1 output), End (1 input, 0 output)
- **Execution**: Special handling for workflow boundaries

---

## API Endpoints

### Workflow Management

```python
# routes.py

from fastapi import APIRouter, Depends, HTTPException
from app.core.dependencies import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db

router = APIRouter(prefix="/plugins/langgraph")

@router.post("/workflows")
async def create_workflow(
    workflow: WorkflowCreate,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new workflow."""
    # Implementation here
    pass

@router.get("/workflows")
async def list_workflows(
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's workflows."""
    pass

@router.get("/workflows/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get workflow details including Rete.js state."""
    pass

@router.put("/workflows/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    workflow: WorkflowUpdate,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update workflow including Rete.js state."""
    pass

@router.delete("/workflows/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete workflow."""
    pass

@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    input_data: dict,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Execute workflow with given input."""
    # Convert Rete.js graph to LangGraph
    # Execute via LangGraph
    # Return results
    pass

@router.get("/workflows/{workflow_id}/executions")
async def list_executions(
    workflow_id: str,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List execution history."""
    pass

@router.get("/templates")
async def list_templates(db: AsyncSession = Depends(get_db)):
    """List available workflow templates."""
    pass

# Helper endpoints for node execution
@router.post("/execute/llm")
async def execute_llm(
    config: dict,
    input_data: dict,
    user = Depends(get_current_user)
):
    """Execute LLM call for Agent node."""
    pass

@router.post("/execute/tool")
async def execute_tool(
    tool_type: str,
    input_data: dict,
    user = Depends(get_current_user)
):
    """Execute tool for Tool node."""
    pass

@router.post("/execute/function")
async def execute_function(
    code: str,
    input_data: dict,
    user = Depends(get_current_user)
):
    """Execute function code in sandboxed environment."""
    pass
```

---

## Workflow Execution Service

```python
# services/execution_service.py

from langgraph.graph import StateGraph, END
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

class WorkflowExecutionService:
    """Executes LangGraph workflows from Rete.js definitions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute(self, workflow_id: str, input_data: Dict[str, Any]):
        """
        Convert Rete.js workflow to LangGraph and execute.

        Steps:
        1. Load workflow from database (includes rete_data JSON)
        2. Parse Rete.js graph structure
        3. Build LangGraph StateGraph
        4. Execute graph with input
        5. Store execution results
        6. Return output
        """
        workflow = await self.load_workflow(workflow_id)
        graph = await self.build_langgraph(workflow.rete_data)
        result = await self.run_graph(graph, input_data)
        await self.store_execution(workflow_id, input_data, result)
        return result

    async def build_langgraph(self, rete_data: dict):
        """
        Build LangGraph from Rete.js JSON.

        Rete.js format:
        {
          "nodes": {
            "1": { "id": "1", "name": "Agent", "data": {...}, "position": [x, y] },
            "2": { "id": "2", "name": "Tool", "data": {...}, "position": [x, y] }
          },
          "connections": [
            {
              "source": "1",
              "sourceOutput": "output",
              "target": "2",
              "targetInput": "input"
            }
          ]
        }
        """
        graph = StateGraph(WorkflowState)

        # Add nodes
        for node_id, node_data in rete_data['nodes'].items():
            node_func = self.create_node_function(node_data)
            graph.add_node(node_data['name'], node_func)

        # Add edges
        for conn in rete_data['connections']:
            source_node = rete_data['nodes'][conn['source']]
            target_node = rete_data['nodes'][conn['target']]

            # Check if conditional edge
            if source_node['type'] == 'conditional':
                condition_func = self.create_condition_function(source_node['data'])
                graph.add_conditional_edges(
                    source_node['name'],
                    condition_func,
                    {target_node['name']: target_node['name']}
                )
            else:
                graph.add_edge(source_node['name'], target_node['name'])

        # Find start node
        start_node = next(
            (node for node in rete_data['nodes'].values() if node['type'] == 'start'),
            None
        )
        if start_node:
            graph.set_entry_point(start_node['name'])

        # Find end node
        end_node = next(
            (node for node in rete_data['nodes'].values() if node['type'] == 'end'),
            None
        )
        if end_node:
            graph.add_edge(end_node['name'], END)

        return graph.compile()

    def create_node_function(self, node_data: dict):
        """Create executable function for Rete node."""
        node_type = node_data['type']
        config = node_data['data']

        if node_type == 'agent':
            return self.create_agent_function(config)
        elif node_type == 'tool':
            return self.create_tool_function(config)
        elif node_type == 'function':
            return self.create_custom_function(config)
        elif node_type == 'conditional':
            return self.create_conditional_function(config)
        # ... more node types

    def create_agent_function(self, config: dict):
        """Create LLM agent function."""
        async def agent_func(state):
            from langchain.chat_models import ChatOpenAI

            llm = ChatOpenAI(
                model=config['model'],
                temperature=config['temperature'],
                max_tokens=config['maxTokens']
            )

            messages = [
                {"role": "system", "content": config['systemPrompt']},
                {"role": "user", "content": state['input']}
            ]

            response = await llm.ainvoke(messages)
            state['output'] = response.content
            return state

        return agent_func

    def create_tool_function(self, config: dict):
        """Create tool execution function."""
        async def tool_func(state):
            tool_type = config['toolType']

            if tool_type == 'web_search':
                # Implement web search
                pass
            elif tool_type == 'calculator':
                # Implement calculator
                pass
            # ... more tools

            return state

        return tool_func
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Create plugin directory structure
- [ ] Implement database models and migrations
- [ ] Create basic plugin class with registration
- [ ] Add plugin to FastCMS sidebar navigation
- [ ] Set up Rete.js CDN integration

### Phase 2: Basic Editor (Week 2)
- [ ] Create workflow list page (Jinja2)
- [ ] Initialize Rete.js editor with CDN
- [ ] Create basic node types (Agent, Tool)
- [ ] Test node creation and connections
- [ ] Implement save/load workflow

### Phase 3: All Node Types (Week 3)
- [ ] Implement Conditional node
- [ ] Implement Function node
- [ ] Implement Start/End nodes
- [ ] Add node configuration forms
- [ ] Test complex workflows

### Phase 4: Backend Integration (Week 4)
- [ ] Implement all API endpoints
- [ ] Create workflow CRUD operations
- [ ] Build node registry system
- [ ] Add workflow validation
- [ ] Test API with Rete.js frontend

### Phase 5: LangGraph Integration (Week 5)
- [ ] Implement Rete.js → LangGraph conversion
- [ ] Create execution service
- [ ] Add execution monitoring and logging
- [ ] Build execution history UI
- [ ] Test end-to-end workflow execution

### Phase 6: Advanced Features (Week 6)
- [ ] Add workflow templates
- [ ] Implement human-in-the-loop nodes
- [ ] Create execution visualization
- [ ] Add minimap for large workflows
- [ ] Implement auto-arrange nodes

### Phase 7: Polish & Testing (Week 7)
- [ ] Add error handling and validation
- [ ] Write unit and integration tests
- [ ] Create documentation
- [ ] Performance optimization
- [ ] User acceptance testing

---

## Example Workflow Templates

### 1. Simple Chat Bot

```
[Start] → [Agent: GPT-4] → [End]
```

### 2. Research Assistant

```
[Start] → [Agent: Query Analyzer] → [Tool: Web Search] → [Agent: Summarizer] → [End]
```

### 3. Conditional Flow

```
[Start] → [Agent: Classifier] → [Conditional: Category]
                                   ├─ "Technical" → [Agent: Tech Expert] → [End]
                                   ├─ "Business" → [Agent: Business Expert] → [End]
                                   └─ "Other" → [Agent: General Assistant] → [End]
```

### 4. Multi-Agent Collaboration

```
[Start] → [Agent: Planner] → [Agent: Researcher] → [Agent: Writer] → [Human Review] → [End]
```

---

## Deployment

### Python Dependencies Only!

```txt
# requirements.txt

# Core dependencies
fastapi>=0.109.0
uvicorn>=0.27.0
sqlalchemy>=2.0.0
alembic>=1.13.0

# LangGraph & LangChain
langgraph>=0.0.20
langchain>=0.1.0
langchain-openai>=0.0.5
langchain-anthropic>=0.1.0

# Other
pydantic>=2.0.0
pydantic-settings>=2.0.0
```

### Environment Variables

```bash
# .env

# LLM API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional
LANGCHAIN_API_KEY=...
LANGCHAIN_TRACING_V2=true
```

### Deployment Steps

```bash
# 1. Clone repository
git clone <repo-url>
cd fastcms

# 2. Create virtual environment (Python only!)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
alembic upgrade head

# 5. Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# NO npm, NO Node.js, NO build step!
```

### Static File Serving

- **Rete.js**: Loaded from CDN (jsdelivr.net)
- **Plugin CSS/JS**: Served by FastAPI from `static/plugins/langgraph/`
- **No bundling required**: All files are vanilla JavaScript

---

## Success Criteria

- [x] Uses Rete.js via CDN (no npm)
- [ ] Users can create workflows visually
- [ ] Drag-and-drop interface works smoothly
- [ ] Nodes can be configured via forms
- [ ] Workflows execute correctly via LangGraph
- [ ] Execution results are displayed clearly
- [ ] Python-only deployment (no Node.js)
- [ ] Plugin can be installed via pip
- [ ] Documentation is complete and clear

---

## Security Considerations

1. **Code Execution**: Sandbox Python code in Function nodes using `RestrictedPython`
2. **Input Validation**: Validate all workflow configurations before execution
3. **Rate Limiting**: Limit workflow executions per user
4. **API Key Management**: Store LLM API keys securely
5. **Access Control**: Users can only access their own workflows
6. **Execution Timeouts**: Prevent infinite loops

---

## Performance Optimization

1. **Lazy Loading**: Load workflow data only when needed
2. **Debouncing**: Debounce save operations
3. **Async Execution**: Execute workflows asynchronously
4. **Caching**: Cache compiled LangGraph workflows
5. **CDN Caching**: Rete.js loaded from fast CDN

---

## Questions to Address

1. Should we support custom node types created by users?
2. Do we need workflow versioning?
3. Should workflows be shareable between users?
4. Do we need a marketplace for workflow templates?
5. Should we support exporting workflows as Python code?

---

## Resources

- **Rete.js Documentation**: https://retejs.org/docs/
- **Rete.js GitHub**: https://github.com/retejs/rete
- **LangGraph Documentation**: https://python.langchain.com/docs/langgraph
- **CDN Links**: https://cdn.jsdelivr.net/npm/rete@2.0.6/

---

This plan provides a complete roadmap for implementing the LangGraph visual workflow builder using **Rete.js via CDN**, ensuring **Python-only deployment** with no Node.js, npm, or build process required!
