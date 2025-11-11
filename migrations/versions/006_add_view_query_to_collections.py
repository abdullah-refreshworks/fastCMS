"""add view_query to collections

Revision ID: 006
Revises: 005
Create Date: 2025-11-11

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add view_query column to collections table"""
    op.add_column(
        "collections",
        sa.Column("view_query", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Remove view_query column from collections table"""
    op.drop_column("collections", "view_query")
