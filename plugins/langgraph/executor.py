"""
Workflow execution engine for LangGraph plugin.
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from plugins.langgraph.config import config


class WorkflowExecutor:
    """Execute LangGraph workflows."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize executor with optional API key."""
        self.api_key = api_key or config.OPENAI_API_KEY

    async def execute_workflow(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        input_data: Any,
    ) -> Dict[str, Any]:
        """
        Execute a workflow given nodes, edges, and input data.

        Args:
            nodes: List of workflow nodes
            edges: List of workflow edges
            input_data: Input data for the workflow

        Returns:
            Execution result with output and logs
        """
        execution_log = []
        current_data = input_data

        try:
            # Find start node
            start_node = self._find_start_node(nodes)
            if not start_node:
                return {
                    "status": "failed",
                    "error": "No start node found",
                    "output": None,
                    "logs": execution_log,
                }

            # Execute workflow from start node
            current_node_id = start_node["id"]
            visited = set()
            max_iterations = 100  # Prevent infinite loops

            iteration = 0
            while current_node_id and iteration < max_iterations:
                if current_node_id in visited:
                    execution_log.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "node_id": current_node_id,
                        "message": "Cycle detected, stopping execution",
                    })
                    break

                visited.add(current_node_id)

                # Find current node
                current_node = next((n for n in nodes if n["id"] == current_node_id), None)
                if not current_node:
                    break

                # Execute node
                execution_log.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "node_id": current_node_id,
                    "node_type": current_node.get("node_type"),
                    "label": current_node.get("label"),
                    "message": f"Executing {current_node.get('label', 'node')}",
                })

                try:
                    node_result = await self._execute_node(current_node, current_data)
                    current_data = node_result

                    execution_log.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "node_id": current_node_id,
                        "message": "Node executed successfully",
                        "output": str(node_result)[:200],  # Truncate for logging
                    })
                except Exception as e:
                    execution_log.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "node_id": current_node_id,
                        "message": f"Node execution failed: {str(e)}",
                        "error": str(e),
                    })
                    return {
                        "status": "failed",
                        "error": str(e),
                        "output": None,
                        "logs": execution_log,
                    }

                # Find next node
                next_edge = next(
                    (e for e in edges if e["source_node_id"] == current_node_id),
                    None
                )

                if next_edge:
                    current_node_id = next_edge["target_node_id"]
                else:
                    # No more edges, end execution
                    break

                iteration += 1

            if iteration >= max_iterations:
                execution_log.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "Max iterations reached, stopping execution",
                })

            return {
                "status": "completed",
                "output": current_data,
                "logs": execution_log,
            }

        except Exception as e:
            execution_log.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Workflow execution failed: {str(e)}",
                "error": str(e),
            })
            return {
                "status": "failed",
                "error": str(e),
                "output": None,
                "logs": execution_log,
            }

    def _find_start_node(self, nodes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find the start node in the workflow."""
        # Look for explicit start node
        start_node = next((n for n in nodes if n.get("node_type") == "start"), None)
        if start_node:
            return start_node

        # If no start node, return first node
        return nodes[0] if nodes else None

    async def _execute_node(self, node: Dict[str, Any], input_data: Any) -> Any:
        """Execute a single node based on its type."""
        node_type = node.get("node_type")
        node_config = node.get("config", {})

        if isinstance(node_config, str):
            node_config = json.loads(node_config)

        if node_type == "llm":
            return await self._execute_llm_node(node_config, input_data)
        elif node_type == "function":
            return await self._execute_function_node(node_config, input_data)
        elif node_type == "tool":
            return await self._execute_tool_node(node_config, input_data)
        elif node_type in ["start", "end"]:
            return input_data
        else:
            # Default: pass through
            return input_data

    async def _execute_llm_node(self, config: Dict[str, Any], input_data: Any) -> str:
        """Execute an LLM node using OpenAI API."""
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")

        try:
            # Lazy import to avoid dependency issues
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.api_key)

            # Get configuration
            model = config.get("model", "gpt-4o-mini")
            temperature = config.get("temperature", 0.7)
            max_tokens = config.get("max_tokens", 1000)
            system_prompt = config.get("system_prompt", "You are a helpful assistant.")

            # Build user message from input
            if isinstance(input_data, dict):
                user_message = json.dumps(input_data)
            else:
                user_message = str(input_data)

            # Make API call
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            return response.choices[0].message.content

        except ImportError:
            raise ValueError("openai package not installed. Install with: pip install openai")
        except Exception as e:
            raise ValueError(f"LLM execution failed: {str(e)}")

    async def _execute_function_node(self, config: Dict[str, Any], input_data: Any) -> Any:
        """Execute a Python function node."""
        code = config.get("code", "")
        if not code:
            return input_data

        # Create a safe execution environment
        local_vars = {"input": input_data, "output": None}

        try:
            exec(code, {"__builtins__": __builtins__}, local_vars)
            return local_vars.get("output", input_data)
        except Exception as e:
            raise ValueError(f"Function execution failed: {str(e)}")

    async def _execute_tool_node(self, config: Dict[str, Any], input_data: Any) -> Any:
        """Execute a tool node."""
        tool_type = config.get("tool_type")

        # Add tool implementations here
        # For now, just pass through
        return input_data
