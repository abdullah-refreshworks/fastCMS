"""add_langgraph_integration_support

Revision ID: 57348398da9a
Revises: 57ded8edb60e
Create Date: 2025-12-03 10:55:19.262339

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "57348398da9a"
down_revision: Union[str, None] = "57ded8edb60e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Add new columns to langgraph_workflows table
    op.add_column(
        "langgraph_workflows",
        sa.Column("workflow_type", sa.String(20), nullable=False, server_default="custom"),
    )
    op.add_column(
        "langgraph_workflows", sa.Column("graph_code", sa.Text(), nullable=True)
    )

    # Create langgraph_checkpoints table
    op.create_table(
        "langgraph_checkpoints",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "workflow_id",
            sa.String(36),
            sa.ForeignKey("langgraph_workflows.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("thread_id", sa.String(255), nullable=False),
        sa.Column("checkpoint_data", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # Create indexes for checkpoints table
    op.create_index(
        "idx_langgraph_checkpoints_workflow_id",
        "langgraph_checkpoints",
        ["workflow_id"],
    )
    op.create_index(
        "idx_langgraph_checkpoints_thread_id", "langgraph_checkpoints", ["thread_id"]
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop indexes
    op.drop_index("idx_langgraph_checkpoints_thread_id", "langgraph_checkpoints")
    op.drop_index("idx_langgraph_checkpoints_workflow_id", "langgraph_checkpoints")

    # Drop checkpoints table
    op.drop_table("langgraph_checkpoints")

    # Remove columns from workflows table
    op.drop_column("langgraph_workflows", "graph_code")
    op.drop_column("langgraph_workflows", "workflow_type")
