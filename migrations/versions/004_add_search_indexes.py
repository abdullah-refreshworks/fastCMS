"""add search indexes table

Revision ID: 004
Revises: 003
Create Date: 2025-11-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create search_indexes table"""
    op.create_table(
        "search_indexes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("collection_name", sa.String(100), nullable=False, unique=True),
        sa.Column("indexed_fields", sa.Text(), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_search_collection", "search_indexes", ["collection_name"])


def downgrade() -> None:
    """Drop search_indexes table"""
    op.drop_index("idx_search_collection", "search_indexes")
    op.drop_table("search_indexes")
