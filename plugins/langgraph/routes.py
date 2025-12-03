"""
API routes for LangGraph plugin.
"""

import json
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, UserContext
from app.db.session import get_db
from plugins.langgraph.models import Workflow, WorkflowExecution, WorkflowNode, WorkflowEdge
from plugins.langgraph.schemas import (
    ExecutionInput,
    ExecutionListResponse,
    ExecutionResponse,
    NodeCreate,
    NodeResponse,
    NodeUpdate,
    EdgeCreate,
    EdgeResponse,
    WorkflowCreate,
    WorkflowListResponse,
    WorkflowResponse,
    WorkflowUpdate,
)
from plugins.langgraph.executor import execute_langgraph_workflow

router = APIRouter()


# Workflow endpoints

@router.post("/workflows", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow: WorkflowCreate,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new workflow."""
    new_workflow = Workflow(
        user_id=user.user_id,
        name=workflow.name,
        description=workflow.description,
        tags=json.dumps(workflow.tags) if workflow.tags else "[]",
        is_template=workflow.is_template,
        rete_data=json.dumps(workflow.rete_data) if workflow.rete_data else "{}",
    )

    db.add(new_workflow)

    # Ensure tags and rete_data are always strings (SQLite requirement)
    if isinstance(new_workflow.tags, (list, dict)):
        new_workflow.tags = json.dumps(new_workflow.tags)
    if isinstance(new_workflow.rete_data, dict):
        new_workflow.rete_data = json.dumps(new_workflow.rete_data)

    await db.commit()
    await db.refresh(new_workflow)

    # Convert to dict for response - don't modify the model object
    response_data = {
        "id": new_workflow.id,
        "user_id": new_workflow.user_id,
        "name": new_workflow.name,
        "description": new_workflow.description,
        "tags": json.loads(new_workflow.tags) if isinstance(new_workflow.tags, str) else new_workflow.tags,
        "is_template": new_workflow.is_template,
        "rete_data": json.loads(new_workflow.rete_data) if isinstance(new_workflow.rete_data, str) else new_workflow.rete_data,
        "created_at": new_workflow.created_at,
        "updated_at": new_workflow.updated_at,
    }

    return response_data


@router.get("/workflows", response_model=WorkflowListResponse)
async def list_workflows(
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all workflows for the current user."""
    result = await db.execute(
        select(Workflow).where(Workflow.user_id == user.user_id).order_by(Workflow.updated_at.desc())
    )
    workflows = result.scalars().all()

    # Convert to dicts to avoid SQLAlchemy tracking JSON parsing
    workflows_data = []
    for wf in workflows:
        workflows_data.append({
            "id": wf.id,
            "user_id": wf.user_id,
            "name": wf.name,
            "description": wf.description,
            "tags": json.loads(wf.tags) if isinstance(wf.tags, str) else wf.tags,
            "is_template": wf.is_template,
            "rete_data": json.loads(wf.rete_data) if isinstance(wf.rete_data, str) else wf.rete_data,
            "created_at": wf.created_at,
            "updated_at": wf.updated_at,
        })

    return {"workflows": workflows_data, "total": len(workflows_data)}


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: UUID,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific workflow."""
    result = await db.execute(select(Workflow).where(Workflow.id == str(workflow_id), Workflow.user_id == user.user_id))
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    # Convert to dict to avoid SQLAlchemy tracking JSON parsing
    return {
        "id": workflow.id,
        "user_id": workflow.user_id,
        "name": workflow.name,
        "description": workflow.description,
        "tags": json.loads(workflow.tags) if isinstance(workflow.tags, str) else workflow.tags,
        "is_template": workflow.is_template,
        "rete_data": json.loads(workflow.rete_data) if isinstance(workflow.rete_data, str) else workflow.rete_data,
        "created_at": workflow.created_at,
        "updated_at": workflow.updated_at,
    }


@router.put("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: UUID,
    workflow_update: WorkflowUpdate,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a workflow."""
    result = await db.execute(select(Workflow).where(Workflow.id == str(workflow_id), Workflow.user_id == user.user_id))
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    # Update fields - serialize JSON fields
    update_data = workflow_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "tags" and value is not None:
            setattr(workflow, field, json.dumps(value))
        elif field == "rete_data" and value is not None:
            setattr(workflow, field, json.dumps(value))
        else:
            setattr(workflow, field, value)

    # Ensure tags and rete_data are always strings (SQLite requirement)
    if isinstance(workflow.tags, (list, dict)):
        workflow.tags = json.dumps(workflow.tags)
    if isinstance(workflow.rete_data, dict):
        workflow.rete_data = json.dumps(workflow.rete_data)

    await db.commit()
    await db.refresh(workflow)

    # Convert to dict to avoid SQLAlchemy tracking JSON parsing
    return {
        "id": workflow.id,
        "user_id": workflow.user_id,
        "name": workflow.name,
        "description": workflow.description,
        "tags": json.loads(workflow.tags) if isinstance(workflow.tags, str) else workflow.tags,
        "is_template": workflow.is_template,
        "rete_data": json.loads(workflow.rete_data) if isinstance(workflow.rete_data, str) else workflow.rete_data,
        "created_at": workflow.created_at,
        "updated_at": workflow.updated_at,
    }


@router.delete("/workflows/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: UUID,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a workflow."""
    result = await db.execute(select(Workflow).where(Workflow.id == str(workflow_id), Workflow.user_id == user.user_id))
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    await db.delete(workflow)
    await db.commit()


# Node endpoints

@router.post("/workflows/{workflow_id}/nodes", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
async def create_node(
    workflow_id: UUID,
    node: NodeCreate,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new node in a workflow."""
    # Verify workflow ownership (convert UUID to string for SQLite comparison)
    result = await db.execute(select(Workflow).where(Workflow.id == str(workflow_id), Workflow.user_id == user.user_id))
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    # Create node (convert UUID to string for SQLite)
    new_node = WorkflowNode(
        workflow_id=str(workflow_id),
        node_type=node.node_type,
        label=node.label,
        position_x=node.position_x,
        position_y=node.position_y,
        config=json.dumps(node.config) if node.config else "{}",
    )

    db.add(new_node)
    await db.commit()
    await db.refresh(new_node)

    return {
        "id": new_node.id,
        "workflow_id": new_node.workflow_id,
        "node_type": new_node.node_type,
        "label": new_node.label,
        "position_x": new_node.position_x,
        "position_y": new_node.position_y,
        "config": json.loads(new_node.config) if isinstance(new_node.config, str) else new_node.config,
        "created_at": new_node.created_at,
        "updated_at": new_node.updated_at,
    }


@router.get("/workflows/{workflow_id}/nodes")
async def list_nodes(
    workflow_id: UUID,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all nodes in a workflow."""
    # Verify workflow ownership
    result = await db.execute(select(Workflow).where(Workflow.id == str(workflow_id), Workflow.user_id == user.user_id))
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    # Get nodes
    result = await db.execute(select(WorkflowNode).where(WorkflowNode.workflow_id == str(workflow_id)))
    nodes = result.scalars().all()

    return {
        "nodes": [
            {
                "id": node.id,
                "workflow_id": node.workflow_id,
                "node_type": node.node_type,
                "label": node.label,
                "position_x": node.position_x,
                "position_y": node.position_y,
                "config": json.loads(node.config) if isinstance(node.config, str) else node.config,
                "created_at": node.created_at,
                "updated_at": node.updated_at,
            }
            for node in nodes
        ]
    }


@router.put("/workflows/{workflow_id}/nodes/{node_id}", response_model=NodeResponse)
async def update_node(
    workflow_id: UUID,
    node_id: UUID,
    node_update: NodeUpdate,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a node."""
    # Verify workflow ownership
    result = await db.execute(select(Workflow).where(Workflow.id == str(workflow_id), Workflow.user_id == user.user_id))
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    # Get node
    result = await db.execute(select(WorkflowNode).where(WorkflowNode.id == str(node_id), WorkflowNode.workflow_id == str(workflow_id)))
    node = result.scalar_one_or_none()

    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

    # Update fields
    update_data = node_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "config" and value is not None:
            setattr(node, field, json.dumps(value))
        else:
            setattr(node, field, value)

    await db.commit()
    await db.refresh(node)

    return {
        "id": node.id,
        "workflow_id": node.workflow_id,
        "node_type": node.node_type,
        "label": node.label,
        "position_x": node.position_x,
        "position_y": node.position_y,
        "config": json.loads(node.config) if isinstance(node.config, str) else node.config,
        "created_at": node.created_at,
        "updated_at": node.updated_at,
    }


@router.delete("/workflows/{workflow_id}/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(
    workflow_id: UUID,
    node_id: UUID,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a node."""
    # Verify workflow ownership
    result = await db.execute(select(Workflow).where(Workflow.id == str(workflow_id), Workflow.user_id == user.user_id))
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    # Get node
    result = await db.execute(select(WorkflowNode).where(WorkflowNode.id == str(node_id), WorkflowNode.workflow_id == str(workflow_id)))
    node = result.scalar_one_or_none()

    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

    await db.delete(node)
    await db.commit()


# Edge endpoints

@router.post("/workflows/{workflow_id}/edges", response_model=EdgeResponse, status_code=status.HTTP_201_CREATED)
async def create_edge(
    workflow_id: UUID,
    edge: EdgeCreate,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new edge in a workflow."""
    # Verify workflow ownership
    result = await db.execute(select(Workflow).where(Workflow.id == str(workflow_id), Workflow.user_id == user.user_id))
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    # Create edge (convert UUID to string for SQLite)
    new_edge = WorkflowEdge(
        workflow_id=str(workflow_id),
        source_node_id=str(edge.source_node_id),
        target_node_id=str(edge.target_node_id),
        source_output=edge.source_output,
        target_input=edge.target_input,
        condition=json.dumps(edge.condition) if edge.condition else None,
    )

    db.add(new_edge)
    await db.commit()
    await db.refresh(new_edge)

    return {
        "id": new_edge.id,
        "workflow_id": new_edge.workflow_id,
        "source_node_id": new_edge.source_node_id,
        "target_node_id": new_edge.target_node_id,
        "source_output": new_edge.source_output,
        "target_input": new_edge.target_input,
        "condition": json.loads(new_edge.condition) if new_edge.condition and isinstance(new_edge.condition, str) else new_edge.condition,
        "created_at": new_edge.created_at,
    }


@router.get("/workflows/{workflow_id}/edges")
async def list_edges(
    workflow_id: UUID,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all edges in a workflow."""
    # Verify workflow ownership
    result = await db.execute(select(Workflow).where(Workflow.id == str(workflow_id), Workflow.user_id == user.user_id))
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    # Get edges
    result = await db.execute(select(WorkflowEdge).where(WorkflowEdge.workflow_id == str(workflow_id)))
    edges = result.scalars().all()

    return {
        "edges": [
            {
                "id": edge.id,
                "workflow_id": edge.workflow_id,
                "source_node_id": edge.source_node_id,
                "target_node_id": edge.target_node_id,
                "source_output": edge.source_output,
                "target_input": edge.target_input,
                "condition": json.loads(edge.condition) if edge.condition and isinstance(edge.condition, str) else edge.condition,
                "created_at": edge.created_at,
            }
            for edge in edges
        ]
    }


@router.delete("/workflows/{workflow_id}/edges/{edge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_edge(
    workflow_id: UUID,
    edge_id: UUID,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an edge."""
    # Verify workflow ownership
    result = await db.execute(select(Workflow).where(Workflow.id == str(workflow_id), Workflow.user_id == user.user_id))
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    # Get edge
    result = await db.execute(select(WorkflowEdge).where(WorkflowEdge.id == str(edge_id), WorkflowEdge.workflow_id == str(workflow_id)))
    edge = result.scalar_one_or_none()

    if not edge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Edge not found")

    await db.delete(edge)
    await db.commit()


# Execution endpoints

@router.post("/workflows/{workflow_id}/execute", response_model=ExecutionResponse)
async def execute_workflow(
    workflow_id: UUID,
    execution_input: ExecutionInput,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute a workflow."""
    from plugins.langgraph.executor import WorkflowExecutor
    from plugins.langgraph.models import WorkflowNode, WorkflowEdge

    # Get workflow
    result = await db.execute(select(Workflow).where(Workflow.id == str(workflow_id), Workflow.user_id == user.user_id))
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    # Get workflow nodes and edges
    nodes_result = await db.execute(
        select(WorkflowNode).where(WorkflowNode.workflow_id == str(workflow_id))
    )
    nodes = nodes_result.scalars().all()

    edges_result = await db.execute(
        select(WorkflowEdge).where(WorkflowEdge.workflow_id == str(workflow_id))
    )
    edges = edges_result.scalars().all()

    # Create execution record (convert UUID to string for SQLite)
    # Always store input_data as JSON string for consistency
    execution = WorkflowExecution(
        workflow_id=str(workflow_id),
        user_id=user.user_id,
        input_data=json.dumps(execution_input.input),
        status="running",
    )

    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    try:
        # Convert nodes and edges to dicts for executor
        nodes_data = [
            {
                "id": str(node.id),
                "node_type": node.node_type,
                "label": node.label,
                "config": json.loads(node.config) if isinstance(node.config, str) else node.config,
            }
            for node in nodes
        ]

        edges_data = [
            {
                "id": str(edge.id),
                "source_node_id": str(edge.source_node_id),
                "target_node_id": str(edge.target_node_id),
            }
            for edge in edges
        ]

        # Execute workflow
        executor = WorkflowExecutor()
        result = await executor.execute_workflow(nodes_data, edges_data, execution_input.input)

        # Update execution record
        execution.status = result["status"]
        execution.output_data = json.dumps(result["output"]) if result["output"] is not None else None
        execution.error = result.get("error")
        execution.execution_log = json.dumps(result["logs"])
        execution.completed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(execution)

        # Return as dict to avoid SQLAlchemy tracking
        # Parse JSON strings back to Python objects
        return {
            "id": execution.id,
            "workflow_id": execution.workflow_id,
            "user_id": execution.user_id,
            "input_data": json.loads(execution.input_data) if execution.input_data else None,
            "output_data": json.loads(execution.output_data) if execution.output_data else None,
            "status": execution.status,
            "error": execution.error,
            "execution_log": json.loads(execution.execution_log) if execution.execution_log else [],
            "started_at": execution.started_at,
            "completed_at": execution.completed_at,
        }

    except Exception as e:
        # Update execution as failed
        execution.status = "failed"
        error_message = str(e)
        execution.error = error_message
        execution.completed_at = datetime.utcnow()

        # Add error to logs
        try:
            import traceback
            error_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "error",
                "message": f"Workflow execution failed: {error_message}",
                "traceback": traceback.format_exc()
            }
            current_logs = json.loads(execution.execution_log) if execution.execution_log else []
            current_logs.append(error_log)
            execution.execution_log = json.dumps(current_logs)
        except:
            pass  # If logging fails, just skip it

        await db.commit()
        await db.refresh(execution)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message
        )


@router.post("/workflows/{workflow_id}/execute/stream")
async def execute_workflow_stream(
    workflow_id: UUID,
    execution_input: ExecutionInput,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute workflow with LangGraph and stream results using Server-Sent Events."""
    # Verify workflow ownership
    result = await db.execute(select(Workflow).where(Workflow.id == str(workflow_id), Workflow.user_id == user.user_id))
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    # Check if workflow is LangGraph type (can be None for older workflows, treat as custom)
    workflow_type = getattr(workflow, 'workflow_type', 'custom')

    if workflow_type != 'langgraph':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint only supports LangGraph workflows. Use /execute for custom workflows."
        )

    # Get nodes and edges
    nodes_result = await db.execute(
        select(WorkflowNode).where(WorkflowNode.workflow_id == str(workflow_id))
    )
    nodes = nodes_result.scalars().all()

    edges_result = await db.execute(
        select(WorkflowEdge).where(WorkflowEdge.workflow_id == str(workflow_id))
    )
    edges = edges_result.scalars().all()

    # Convert to dict format for executor
    nodes_data = [
        {
            "id": str(node.id),
            "type": node.node_type,
            "label": node.label,
            "config": json.loads(node.config) if isinstance(node.config, str) else node.config,
        }
        for node in nodes
    ]

    edges_data = [
        {
            "id": str(edge.id),
            "source_node_id": str(edge.source_node_id),
            "target_node_id": str(edge.target_node_id),
        }
        for edge in edges
    ]

    workflow_data = {
        "nodes": nodes_data,
        "edges": edges_data,
    }

    # Create execution record
    execution = WorkflowExecution(
        workflow_id=str(workflow_id),
        user_id=user.user_id,
        input_data=json.dumps(execution_input.input),
        status="running",
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    # Stream execution
    async def event_generator():
        """Generate SSE events from LangGraph execution"""
        execution_logs = []
        final_output = None
        has_error = False

        try:
            async for event in execute_langgraph_workflow(workflow_data, execution_input.input, stream=True):
                # Store logs
                execution_logs.append(event)

                # Track final output
                if event.get("type") == "execution_complete":
                    final_output = event.get("output")
                elif event.get("type") == "error":
                    has_error = True

                # Send as SSE
                yield f"data: {json.dumps(event)}\n\n"

            # Update execution record
            execution.status = "failed" if has_error else "completed"
            execution.output_data = json.dumps(final_output) if final_output else None
            execution.execution_log = json.dumps(execution_logs)
            execution.completed_at = datetime.utcnow()
            await db.commit()

        except Exception as e:
            # Send error event
            error_event = {
                "type": "error",
                "message": f"Streaming failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
            yield f"data: {json.dumps(error_event)}\n\n"

            # Update execution
            execution.status = "failed"
            execution.error = str(e)
            execution.execution_log = json.dumps(execution_logs)
            execution.completed_at = datetime.utcnow()
            await db.commit()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


@router.get("/workflows/{workflow_id}/executions", response_model=ExecutionListResponse)
async def list_executions(
    workflow_id: UUID,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List executions for a workflow."""
    # Verify workflow ownership
    result = await db.execute(select(Workflow).where(Workflow.id == str(workflow_id), Workflow.user_id == user.user_id))
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    # Get executions
    result = await db.execute(
        select(WorkflowExecution)
        .where(WorkflowExecution.workflow_id == str(workflow_id))
        .order_by(WorkflowExecution.started_at.desc())
    )
    executions = result.scalars().all()

    return {"executions": executions, "total": len(executions)}


# Template endpoints

@router.get("/templates", response_model=WorkflowListResponse)
async def list_templates(
    db: AsyncSession = Depends(get_db),
):
    """List all workflow templates."""
    result = await db.execute(select(Workflow).where(Workflow.is_template == True).order_by(Workflow.created_at.desc()))
    templates = result.scalars().all()

    # Convert to dicts to avoid SQLAlchemy tracking JSON parsing
    templates_data = []
    for tpl in templates:
        templates_data.append({
            "id": tpl.id,
            "user_id": tpl.user_id,
            "name": tpl.name,
            "description": tpl.description,
            "tags": json.loads(tpl.tags) if isinstance(tpl.tags, str) else tpl.tags,
            "is_template": tpl.is_template,
            "rete_data": json.loads(tpl.rete_data) if isinstance(tpl.rete_data, str) else tpl.rete_data,
            "created_at": tpl.created_at,
            "updated_at": tpl.updated_at,
        })

    return {"workflows": templates_data, "total": len(templates_data)}
