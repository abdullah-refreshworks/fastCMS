"""add verification and webhook models

Revision ID: 002
Revises: 001
Create Date: 2025-11-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create verification_tokens, password_reset_tokens, and webhooks tables."""

    # Create verification_tokens table
    op.create_table(
        "verification_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False, index=True),
        sa.Column("token", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("expires_at", sa.String(50), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, default=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
    )

    # Create password_reset_tokens table
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False, index=True),
        sa.Column("token", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("expires_at", sa.String(50), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, default=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
    )

    # Create webhooks table
    op.create_table(
        "webhooks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("collection_name", sa.String(100), nullable=False, index=True),
        sa.Column("events", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, default=True),
        sa.Column("secret", sa.String(255), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, default=3),
        sa.Column("last_triggered_at", sa.String(50), nullable=True),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    """Drop verification_tokens, password_reset_tokens, and webhooks tables."""
    op.drop_table("webhooks")
    op.drop_table("password_reset_tokens")
    op.drop_table("verification_tokens")
