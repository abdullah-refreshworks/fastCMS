"""add_api_keys_table

Revision ID: 621bae4ce6a1
Revises: add_2fa_fields
Create Date: 2025-12-22 11:04:44.035726

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "621bae4ce6a1"
down_revision: Union[str, None] = "add_2fa_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create api_keys table."""
    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("key_prefix", sa.String(8), nullable=False, index=True),
        sa.Column("key_hash", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("user_id", sa.String(36), nullable=False, index=True),
        sa.Column("scopes", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("last_used_ip", sa.String(45), nullable=True),
        sa.Column("created", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Drop api_keys table."""
    op.drop_table("api_keys")
