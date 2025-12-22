"""Add 2FA fields to users table

Revision ID: add_2fa_fields
Revises: 007
Create Date: 2025-12-22

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "add_2fa_fields"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add 2FA fields to users table."""
    # Add two_factor_enabled with default False
    op.add_column(
        "users",
        sa.Column(
            "two_factor_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    # Add two_factor_secret (nullable)
    op.add_column(
        "users",
        sa.Column("two_factor_secret", sa.String(length=255), nullable=True),
    )

    # Add two_factor_backup_codes (nullable)
    op.add_column(
        "users",
        sa.Column("two_factor_backup_codes", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Remove 2FA fields from users table."""
    op.drop_column("users", "two_factor_backup_codes")
    op.drop_column("users", "two_factor_secret")
    op.drop_column("users", "two_factor_enabled")
