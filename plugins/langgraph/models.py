"""
Database models for LangGraph plugin.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text, Boolean, Float
from sqlalchemy.orm import relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.user import User


class Workflow(Base):
    """Workflow model - represents a LangGraph workflow."""

    __tablename__ = "langgraph_workflows"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_template = Column(Boolean, default=False)
    tags = Column(Text, default="[]")  # JSON string for SQLite
    rete_data = Column(Text, default="{}")  # JSON string for SQLite
    workflow_type = Column(String(20), default="custom", nullable=False)  # 'custom' or 'langgraph'
    graph_code = Column(Text, nullable=True)  # Python code for LangGraph workflows
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="langgraph_workflows")
    nodes = relationship("WorkflowNode", back_populates="workflow", cascade="all, delete-orphan")
    edges = relationship("WorkflowEdge", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_langgraph_workflows_user_id", "user_id"),
        Index("idx_langgraph_workflows_is_template", "is_template"),
    )

    def __repr__(self):
        return f"<Workflow(id={self.id}, name={self.name})>"


class WorkflowNode(Base):
    """Workflow node model - represents a node in the workflow."""

    __tablename__ = "langgraph_nodes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String(36), ForeignKey("langgraph_workflows.id", ondelete="CASCADE"), nullable=False)
    node_type = Column(String(50), nullable=False)  # 'agent', 'tool', 'conditional', 'function'
    label = Column(String(255), nullable=False)
    position_x = Column(Float, nullable=False)
    position_y = Column(Float, nullable=False)
    config = Column(Text, nullable=False, default="{}")  # JSON string for SQLite
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workflow = relationship("Workflow", back_populates="nodes")

    # Indexes
    __table_args__ = (Index("idx_langgraph_nodes_workflow_id", "workflow_id"),)

    def __repr__(self):
        return f"<WorkflowNode(id={self.id}, type={self.node_type}, label={self.label})>"


class WorkflowEdge(Base):
    """Workflow edge model - represents a connection between nodes."""

    __tablename__ = "langgraph_edges"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String(36), ForeignKey("langgraph_workflows.id", ondelete="CASCADE"), nullable=False)
    source_node_id = Column(String(36), ForeignKey("langgraph_nodes.id", ondelete="CASCADE"), nullable=False)
    target_node_id = Column(String(36), ForeignKey("langgraph_nodes.id", ondelete="CASCADE"), nullable=False)
    source_output = Column(String(50), nullable=True)  # Which output socket
    target_input = Column(String(50), nullable=True)  # Which input socket
    condition = Column(Text, nullable=True)  # JSON string for SQLite
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    workflow = relationship("Workflow", back_populates="edges")

    # Indexes
    __table_args__ = (
        Index("idx_langgraph_edges_workflow_id", "workflow_id"),
        Index("idx_langgraph_edges_source_node_id", "source_node_id"),
        Index("idx_langgraph_edges_target_node_id", "target_node_id"),
    )

    def __repr__(self):
        return f"<WorkflowEdge(id={self.id}, source={self.source_node_id}, target={self.target_node_id})>"


class WorkflowExecution(Base):
    """Workflow execution model - represents an execution of a workflow."""

    __tablename__ = "langgraph_executions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String(36), ForeignKey("langgraph_workflows.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    input_data = Column(Text, nullable=False)  # JSON string for SQLite
    output_data = Column(Text, nullable=True)  # JSON string for SQLite
    status = Column(String(20), nullable=False, default="pending")  # 'pending', 'running', 'completed', 'failed'
    error = Column(Text, nullable=True)
    execution_log = Column(Text, default="[]")  # JSON string for SQLite
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    user = relationship("User", backref="langgraph_executions")

    # Indexes
    __table_args__ = (
        Index("idx_langgraph_executions_workflow_id", "workflow_id"),
        Index("idx_langgraph_executions_user_id", "user_id"),
        Index("idx_langgraph_executions_status", "status"),
    )

    def __repr__(self):
        return f"<WorkflowExecution(id={self.id}, status={self.status})>"


class WorkflowCheckpoint(Base):
    """Workflow checkpoint model - stores LangGraph checkpoints for state persistence."""

    __tablename__ = "langgraph_checkpoints"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String(36), ForeignKey("langgraph_workflows.id", ondelete="CASCADE"), nullable=False)
    thread_id = Column(String(255), nullable=False)  # Unique conversation/session ID
    checkpoint_data = Column(Text, nullable=False)  # Serialized checkpoint state
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    workflow = relationship("Workflow", backref="checkpoints")

    # Indexes
    __table_args__ = (
        Index("idx_langgraph_checkpoints_workflow_id", "workflow_id"),
        Index("idx_langgraph_checkpoints_thread_id", "thread_id"),
    )

    def __repr__(self):
        return f"<WorkflowCheckpoint(id={self.id}, thread_id={self.thread_id})>"
