"""Drop LangGraph plugin tables

Revision ID: drop_langgraph_tables
Revises: fb06c7171ada
Create Date: 2025-12-04

This migration removes all tables created by the LangGraph plugin,
which has been replaced by the Langflow integration plugin.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "drop_langgraph_tables"
down_revision: Union[str, None] = "fb06c7171ada"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop LangGraph tables if they exist."""
    # Get connection to check if tables exist
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()

    # Drop tables in correct order (respecting foreign keys)
    tables_to_drop = [
        "langgraph_checkpoints",
        "langgraph_executions",
        "langgraph_edges",
        "langgraph_nodes",
        "langgraph_workflows",
    ]

    for table_name in tables_to_drop:
        if table_name in existing_tables:
            op.drop_table(table_name)


def downgrade() -> None:
    """
    Downgrade is not supported - LangGraph plugin has been removed.

    If you need LangGraph functionality, use the Langflow plugin instead.
    """
    # We don't recreate the tables on downgrade since the plugin is removed
    pass
