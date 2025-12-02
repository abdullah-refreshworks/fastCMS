"""Add LangGraph plugin tables

Revision ID: 57ded8edb60e
Revises: fb06c7171ada
Create Date: 2025-12-02 10:59:34.056896

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision: str = "57ded8edb60e"
down_revision: Union[str, None] = "fb06c7171ada"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create langgraph_workflows table
    op.create_table(
        "langgraph_workflows",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_template", sa.Boolean, default=False),
        sa.Column("tags", JSONB, nullable=True, default=sa.text("'[]'")),
        sa.Column("rete_data", JSONB, nullable=True, default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_index("idx_langgraph_workflows_user_id", "langgraph_workflows", ["user_id"])
    op.create_index("idx_langgraph_workflows_is_template", "langgraph_workflows", ["is_template"])

    # Create langgraph_nodes table
    op.create_table(
        "langgraph_nodes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("workflow_id", UUID(as_uuid=True), sa.ForeignKey("langgraph_workflows.id", ondelete="CASCADE"), nullable=False),
        sa.Column("node_type", sa.String(50), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("position_x", sa.Float, nullable=False),
        sa.Column("position_y", sa.Float, nullable=False),
        sa.Column("config", JSONB, nullable=False, default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_index("idx_langgraph_nodes_workflow_id", "langgraph_nodes", ["workflow_id"])

    # Create langgraph_edges table
    op.create_table(
        "langgraph_edges",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("workflow_id", UUID(as_uuid=True), sa.ForeignKey("langgraph_workflows.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_node_id", UUID(as_uuid=True), sa.ForeignKey("langgraph_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_node_id", UUID(as_uuid=True), sa.ForeignKey("langgraph_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_output", sa.String(50), nullable=True),
        sa.Column("target_input", sa.String(50), nullable=True),
        sa.Column("condition", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_index("idx_langgraph_edges_workflow_id", "langgraph_edges", ["workflow_id"])
    op.create_index("idx_langgraph_edges_source_node_id", "langgraph_edges", ["source_node_id"])
    op.create_index("idx_langgraph_edges_target_node_id", "langgraph_edges", ["target_node_id"])

    # Create langgraph_executions table
    op.create_table(
        "langgraph_executions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("workflow_id", UUID(as_uuid=True), sa.ForeignKey("langgraph_workflows.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("input_data", JSONB, nullable=False),
        sa.Column("output_data", JSONB, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="pending"),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("execution_log", JSONB, nullable=True, default=sa.text("'[]'")),
        sa.Column("started_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )

    op.create_index("idx_langgraph_executions_workflow_id", "langgraph_executions", ["workflow_id"])
    op.create_index("idx_langgraph_executions_user_id", "langgraph_executions", ["user_id"])
    op.create_index("idx_langgraph_executions_status", "langgraph_executions", ["status"])


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop tables in reverse order
    op.drop_table("langgraph_executions")
    op.drop_table("langgraph_edges")
    op.drop_table("langgraph_nodes")
    op.drop_table("langgraph_workflows")
