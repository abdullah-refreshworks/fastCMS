/**
 * Visual Workflow Editor - Alpine.js Component
 * Drag-and-drop canvas-based workflow builder
 */

document.addEventListener('alpine:init', () => {
  Alpine.data('visualEditor', () => ({
    // State
    workflow: {
      id: null,
      name: 'Untitled Workflow',
      description: '',
    },
    nodes: [],
    edges: [],

    // Drag state
    isDragging: false,
    draggedNode: null,
    dragOffset: { x: 0, y: 0 },
    dragStartPos: { x: 0, y: 0 },
    hasDragged: false,

    // Connection state
    isDrawingConnection: false,
    connectionStart: { x: 0, y: 0 },
    connectionSourceNode: null,
    mousePosition: { x: 0, y: 0 },

    // UI state
    showConfigModal: false,
    currentNode: null,

    // Initialize
    async init() {
      const urlParams = new URLSearchParams(window.location.search);
      const workflowId = window.location.pathname.split('/').pop();

      if (workflowId && workflowId !== 'editor') {
        await this.loadWorkflow(workflowId);
      }
    },

    // Node Management
    addNode(type, x = null, y = null) {
      const posX = x !== null ? x : 100 + Math.random() * 200;
      const posY = y !== null ? y : 100 + Math.random() * 200;

      const node = {
        id: 'temp_' + Date.now() + '_' + Math.random(),
        node_type: type,
        label: `${type.charAt(0).toUpperCase() + type.slice(1)} Node`,
        position_x: posX,
        position_y: posY,
        config: this.getDefaultConfig(type),
      };

      this.nodes.push(node);
      this.showToast('Node added', 'success');
    },

    getDefaultConfig(type) {
      switch(type) {
        case 'llm':
          return {
            model: 'gpt-4o-mini',
            system_prompt: 'You are a helpful assistant.',
            temperature: 0.7,
            max_tokens: 1000,
          };
        case 'function':
          return {
            code: '# Input is available as \'input\' variable\n# Set \'output\' variable with your result\n\noutput = input'
          };
        default:
          return {};
      }
    },

    deleteNode(node) {
      if (confirm(`Delete "${node.label}"?`)) {
        this.nodes = this.nodes.filter(n => n.id !== node.id);
        this.edges = this.edges.filter(e =>
          e.source_node_id !== node.id && e.target_node_id !== node.id
        );
        this.showToast('Node deleted', 'info');
      }
    },

    openNodeConfig(node) {
      this.currentNode = node;
      this.showConfigModal = true;
    },

    // Drag and Drop
    startDrag(event, node) {
      // Don't drag if clicking on inputs, buttons, or icons
      if (event.target.tagName === 'INPUT' ||
          event.target.tagName === 'TEXTAREA' ||
          event.target.tagName === 'BUTTON' ||
          event.target.tagName === 'I' ||
          event.target.closest('button')) {
        return;
      }

      this.isDragging = true;
      this.draggedNode = node;
      this.hasDragged = false;

      const canvas = document.getElementById('canvas');
      const canvasRect = canvas.getBoundingClientRect();
      const nodeElement = document.getElementById('node-' + node.id);
      const rect = nodeElement.getBoundingClientRect();

      this.dragStartPos = {
        x: event.clientX,
        y: event.clientY,
      };

      this.dragOffset = {
        x: event.clientX - canvasRect.left - node.position_x,
        y: event.clientY - canvasRect.top - node.position_y,
      };

      nodeElement.classList.add('dragging');
    },

    onMouseMove(event) {
      if (this.isDragging && this.draggedNode) {
        // Check if mouse has moved more than 5px (drag threshold)
        const deltaX = Math.abs(event.clientX - this.dragStartPos.x);
        const deltaY = Math.abs(event.clientY - this.dragStartPos.y);

        if (deltaX > 5 || deltaY > 5) {
          this.hasDragged = true;
        }

        const canvas = document.getElementById('canvas');
        const canvasRect = canvas.getBoundingClientRect();

        this.draggedNode.position_x = event.clientX - canvasRect.left - this.dragOffset.x;
        this.draggedNode.position_y = event.clientY - canvasRect.top - this.dragOffset.y;
      } else if (this.isDrawingConnection) {
        const canvas = document.getElementById('canvas');
        const canvasRect = canvas.getBoundingClientRect();

        this.mousePosition.x = event.clientX - canvasRect.left;
        this.mousePosition.y = event.clientY - canvasRect.top;
      }
    },

    onMouseUp(event) {
      if (this.isDragging && this.draggedNode) {
        const nodeElement = document.getElementById('node-' + this.draggedNode.id);
        if (nodeElement) {
          nodeElement.classList.remove('dragging');
        }
      }

      this.isDragging = false;
      this.draggedNode = null;

      // Reset hasDragged after a short delay to allow click event to check it
      setTimeout(() => {
        this.hasDragged = false;
      }, 10);

      if (this.isDrawingConnection) {
        this.isDrawingConnection = false;
        this.connectionSourceNode = null;
      }
    },

    // Connection Management
    startConnection(event, node) {
      event.stopPropagation();

      this.isDrawingConnection = true;
      this.connectionSourceNode = node;

      const canvas = document.getElementById('canvas');
      const canvasRect = canvas.getBoundingClientRect();
      const nodeElement = document.getElementById('node-' + node.id);
      const nodeRect = nodeElement.getBoundingClientRect();

      // Start from output port (right side of node)
      this.connectionStart.x = nodeRect.right - canvasRect.left;
      this.connectionStart.y = nodeRect.top + nodeRect.height / 2 - canvasRect.top;

      this.mousePosition.x = this.connectionStart.x;
      this.mousePosition.y = this.connectionStart.y;
    },

    endConnection(targetNode) {
      if (!this.isDrawingConnection || !this.connectionSourceNode) {
        return;
      }

      // Don't connect to self
      if (this.connectionSourceNode.id === targetNode.id) {
        this.isDrawingConnection = false;
        this.connectionSourceNode = null;
        return;
      }

      // Check if edge already exists
      const exists = this.edges.some(e =>
        e.source_node_id === this.connectionSourceNode.id &&
        e.target_node_id === targetNode.id
      );

      if (exists) {
        this.showToast('Connection already exists', 'warning');
        this.isDrawingConnection = false;
        this.connectionSourceNode = null;
        return;
      }

      // Create edge
      const edge = {
        id: 'temp_edge_' + Date.now() + '_' + Math.random(),
        source_node_id: this.connectionSourceNode.id,
        target_node_id: targetNode.id,
      };

      this.edges.push(edge);
      this.showToast('Connection created', 'success');

      this.isDrawingConnection = false;
      this.connectionSourceNode = null;
    },

    getEdgePath(edge) {
      const sourceNode = this.nodes.find(n => n.id === edge.source_node_id);
      const targetNode = this.nodes.find(n => n.id === edge.target_node_id);

      if (!sourceNode || !targetNode) return '';

      // Calculate positions (output port of source, input port of target)
      const x1 = sourceNode.position_x + 220; // Node width
      const y1 = sourceNode.position_y + 60;  // Approximate middle
      const x2 = targetNode.position_x;
      const y2 = targetNode.position_y + 60;

      // Create curved path
      const midX = (x1 + x2) / 2;

      return `M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`;
    },

    // Workflow Management
    async loadWorkflow(workflowId) {
      try {
        // Load workflow
        const workflowRes = await fetch(`/api/v1/plugins/langgraph/workflows/${workflowId}`);
        if (!workflowRes.ok) throw new Error('Failed to load workflow');

        this.workflow = await workflowRes.json();

        // Load nodes
        const nodesRes = await fetch(`/api/v1/plugins/langgraph/workflows/${workflowId}/nodes`);
        if (nodesRes.ok) {
          this.nodes = await nodesRes.json();
        }

        // Load edges
        const edgesRes = await fetch(`/api/v1/plugins/langgraph/workflows/${workflowId}/edges`);
        if (edgesRes.ok) {
          this.edges = await edgesRes.json();
        }

        this.showToast('Workflow loaded', 'success');
      } catch (error) {
        console.error('Load error:', error);
        this.showToast('Failed to load workflow', 'error');
      }
    },

    async saveWorkflow() {
      try {
        let workflowId = this.workflow.id;

        // Create or update workflow
        if (!workflowId) {
          const res = await fetch('/api/v1/plugins/langgraph/workflows', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              name: this.workflow.name,
              description: this.workflow.description,
            }),
          });

          if (!res.ok) throw new Error('Failed to create workflow');

          const data = await res.json();
          workflowId = data.id;
          this.workflow.id = workflowId;

          // Update URL
          window.history.pushState({}, '', `/admin/langgraph/editor/${workflowId}`);
        } else {
          const res = await fetch(`/api/v1/plugins/langgraph/workflows/${workflowId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              name: this.workflow.name,
              description: this.workflow.description,
            }),
          });

          if (!res.ok) throw new Error('Failed to update workflow');
        }

        // Save nodes
        const savedNodes = new Map(); // Map temp IDs to real IDs

        for (const node of this.nodes) {
          if (node.id.startsWith('temp_')) {
            // Create new node
            const res = await fetch(`/api/v1/plugins/langgraph/workflows/${workflowId}/nodes`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                workflow_id: workflowId,
                node_type: node.node_type,
                label: node.label,
                position_x: node.position_x,
                position_y: node.position_y,
                config: node.config,
              }),
            });

            if (!res.ok) throw new Error('Failed to create node');

            const data = await res.json();
            savedNodes.set(node.id, data.id);
            node.id = data.id;
          } else {
            // Update existing node
            const res = await fetch(`/api/v1/plugins/langgraph/workflows/${workflowId}/nodes/${node.id}`, {
              method: 'PUT',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                node_type: node.node_type,
                label: node.label,
                position_x: node.position_x,
                position_y: node.position_y,
                config: node.config,
              }),
            });

            if (!res.ok) throw new Error('Failed to update node');
          }
        }

        // Save edges
        for (const edge of this.edges) {
          if (edge.id.startsWith('temp_edge_')) {
            // Map temp node IDs to real IDs
            const sourceId = savedNodes.get(edge.source_node_id) || edge.source_node_id;
            const targetId = savedNodes.get(edge.target_node_id) || edge.target_node_id;

            // Create new edge
            const res = await fetch(`/api/v1/plugins/langgraph/workflows/${workflowId}/edges`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                workflow_id: workflowId,
                source_node_id: sourceId,
                target_node_id: targetId,
              }),
            });

            if (!res.ok) throw new Error('Failed to create edge');

            const data = await res.json();
            edge.id = data.id;
            edge.source_node_id = sourceId;
            edge.target_node_id = targetId;
          }
        }

        this.showToast('Workflow saved successfully!', 'success');
      } catch (error) {
        console.error('Save error:', error);
        this.showToast('Failed to save workflow: ' + error.message, 'error');
      }
    },

    async executeWorkflow() {
      if (!this.workflow.id) {
        this.showToast('Please save the workflow first', 'warning');
        return;
      }

      if (this.nodes.length === 0) {
        this.showToast('Add nodes to the workflow first', 'warning');
        return;
      }

      const input = prompt('Enter input data for the workflow:');
      if (input === null) return;

      try {
        this.showToast('Executing workflow...', 'info');

        const res = await fetch(`/api/v1/plugins/langgraph/workflows/${this.workflow.id}/execute`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ input }),
        });

        if (!res.ok) {
          const error = await res.json();
          throw new Error(error.detail || 'Execution failed');
        }

        const result = await res.json();

        // Show result
        const output = result.output_data || 'No output';
        const logs = result.execution_log || [];

        let message = `Execution completed!\n\nOutput: ${JSON.stringify(output, null, 2)}`;

        if (logs.length > 0) {
          message += `\n\nLogs:\n${logs.map(log => `- ${log.message}`).join('\n')}`;
        }

        alert(message);
        this.showToast('Execution completed', 'success');
      } catch (error) {
        console.error('Execution error:', error);
        this.showToast('Execution failed: ' + error.message, 'error');
      }
    },

    clearCanvas() {
      if (confirm('Clear all nodes and connections?')) {
        this.nodes = [];
        this.edges = [];
        this.showToast('Canvas cleared', 'info');
      }
    },

    // UI Helpers
    getNodeIcon(type) {
      const icons = {
        llm: 'brain',
        function: 'code',
        start: 'play',
        end: 'stop',
        tool: 'wrench',
        condition: 'code-branch',
      };
      return icons[type] || 'circle';
    },

    getNodeBgColor(type) {
      const colors = {
        llm: 'bg-purple-500',
        function: 'bg-blue-500',
        start: 'bg-green-500',
        end: 'bg-red-500',
        tool: 'bg-yellow-500',
        condition: 'bg-orange-500',
      };
      return colors[type] || 'bg-gray-500';
    },

    getNodeBorderColor(type) {
      const colors = {
        llm: 'border-purple-300',
        function: 'border-blue-300',
        start: 'border-green-300',
        end: 'border-red-300',
        tool: 'border-yellow-300',
        condition: 'border-orange-300',
      };
      return colors[type] || 'border-gray-300';
    },

    showToast(message, type = 'info') {
      const container = document.getElementById('toast-container');
      const toast = document.createElement('div');

      const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        warning: 'bg-yellow-500',
        info: 'bg-blue-500',
      };

      toast.className = `${colors[type]} text-white px-4 py-3 rounded shadow-lg mb-2 animate-fade-in`;
      toast.textContent = message;

      container.appendChild(toast);

      setTimeout(() => {
        toast.classList.add('animate-fade-out');
        setTimeout(() => toast.remove(), 300);
      }, 3000);
    },
  }));
});
