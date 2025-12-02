"""
Pydantic schemas for LangGraph plugin API.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Workflow Schemas

class WorkflowBase(BaseModel):
    """Base workflow schema."""

    name: str = Field(..., description="Workflow name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Workflow description")
    tags: List[str] = Field(default_factory=list, description="Workflow tags")
    is_template: bool = Field(False, description="Is this a template workflow?")


class WorkflowCreate(WorkflowBase):
    """Schema for creating a workflow."""

    rete_data: Dict[str, Any] = Field(default_factory=dict, description="Rete.js editor state")


class WorkflowUpdate(BaseModel):
    """Schema for updating a workflow."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_template: Optional[bool] = None
    rete_data: Optional[Dict[str, Any]] = None


class WorkflowResponse(WorkflowBase):
    """Schema for workflow response."""

    id: UUID
    user_id: UUID
    rete_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkflowListResponse(BaseModel):
    """Schema for listing workflows."""

    workflows: List[WorkflowResponse]
    total: int


# Node Schemas

class NodeBase(BaseModel):
    """Base node schema."""

    node_type: str = Field(..., description="Node type (agent, tool, conditional, function)")
    label: str = Field(..., description="Node label", min_length=1, max_length=255)
    position_x: float = Field(..., description="X position on canvas")
    position_y: float = Field(..., description="Y position on canvas")
    config: Dict[str, Any] = Field(default_factory=dict, description="Node configuration")


class NodeCreate(NodeBase):
    """Schema for creating a node."""

    workflow_id: UUID


class NodeUpdate(BaseModel):
    """Schema for updating a node."""

    label: Optional[str] = Field(None, min_length=1, max_length=255)
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    config: Optional[Dict[str, Any]] = None


class NodeResponse(NodeBase):
    """Schema for node response."""

    id: UUID
    workflow_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Edge Schemas

class EdgeBase(BaseModel):
    """Base edge schema."""

    source_node_id: UUID
    target_node_id: UUID
    source_output: Optional[str] = Field(None, description="Source output socket")
    target_input: Optional[str] = Field(None, description="Target input socket")
    condition: Optional[Dict[str, Any]] = Field(None, description="Conditional edge configuration")


class EdgeCreate(EdgeBase):
    """Schema for creating an edge."""

    workflow_id: UUID


class EdgeResponse(EdgeBase):
    """Schema for edge response."""

    id: UUID
    workflow_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# Execution Schemas

class ExecutionInput(BaseModel):
    """Schema for workflow execution input."""

    input: Any = Field(..., description="Input data for workflow execution")


class ExecutionResponse(BaseModel):
    """Schema for execution response."""

    id: UUID
    workflow_id: UUID
    user_id: UUID
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    status: str
    error: Optional[str] = None
    execution_log: List[Dict[str, Any]] = Field(default_factory=list)
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ExecutionListResponse(BaseModel):
    """Schema for listing executions."""

    executions: List[ExecutionResponse]
    total: int


# Template Schemas

class TemplateResponse(BaseModel):
    """Schema for workflow template."""

    id: UUID
    name: str
    description: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# LLM Execution Schemas

class LLMExecuteRequest(BaseModel):
    """Schema for LLM execution request."""

    config: Dict[str, Any] = Field(..., description="LLM configuration")
    input: Any = Field(..., description="Input data")


class LLMExecuteResponse(BaseModel):
    """Schema for LLM execution response."""

    output: Any


# Tool Execution Schemas

class ToolExecuteRequest(BaseModel):
    """Schema for tool execution request."""

    tool_type: str = Field(..., description="Tool type")
    input: Any = Field(..., description="Input data")


class ToolExecuteResponse(BaseModel):
    """Schema for tool execution response."""

    output: Any


# Function Execution Schemas

class FunctionExecuteRequest(BaseModel):
    """Schema for function execution request."""

    code: str = Field(..., description="Python code to execute")
    input: Any = Field(..., description="Input data")


class FunctionExecuteResponse(BaseModel):
    """Schema for function execution response."""

    output: Any
