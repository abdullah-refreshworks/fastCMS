"""add oauth providers

Revision ID: 007
Revises: fb06c7171ada
Create Date: 2025-12-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "007"
down_revision: Union[str, None] = "57348398da9a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create oauth_providers table for database-configured OAuth providers."""

    # Create oauth_providers table
    op.create_table(
        "oauth_providers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("provider_type", sa.String(50), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, default=False),
        sa.Column("client_id", sa.Text(), nullable=False),
        sa.Column("client_secret", sa.Text(), nullable=False),
        sa.Column("extra_config", sa.JSON(), nullable=False, default=dict),
        sa.Column("custom_scopes", sa.Text(), nullable=True),
        sa.Column("collection_id", sa.String(36), nullable=True, index=True),
        sa.Column("display_order", sa.Integer(), nullable=False, default=0),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
    )

    # Create unique index on provider_type (only one config per provider type)
    op.create_index(
        "ix_oauth_providers_type_unique",
        "oauth_providers",
        ["provider_type"],
        unique=True,
    )


def downgrade() -> None:
    """Drop oauth_providers table."""
    op.drop_index("ix_oauth_providers_type_unique", table_name="oauth_providers")
    op.drop_table("oauth_providers")
