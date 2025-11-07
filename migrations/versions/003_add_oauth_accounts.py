"""add oauth accounts

Revision ID: 003
Revises: 002
Create Date: 2025-11-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create oauth_accounts table."""

    # Create oauth_accounts table
    op.create_table(
        "oauth_accounts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False, index=True),
        sa.Column("provider", sa.String(50), nullable=False, index=True),
        sa.Column("provider_user_id", sa.String(255), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.String(50), nullable=True),
        sa.Column("token_type", sa.String(50), nullable=True),
        sa.Column("scope", sa.Text(), nullable=True),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
    )

    # Create unique index on provider + provider_user_id
    op.create_index(
        "ix_oauth_accounts_provider_user",
        "oauth_accounts",
        ["provider", "provider_user_id"],
        unique=True,
    )


def downgrade() -> None:
    """Drop oauth_accounts table."""
    op.drop_index("ix_oauth_accounts_provider_user", table_name="oauth_accounts")
    op.drop_table("oauth_accounts")
