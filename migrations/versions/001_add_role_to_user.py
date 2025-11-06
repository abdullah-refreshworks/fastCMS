"""add role to user model

Revision ID: 001_add_role_to_user
Revises:
Create Date: 2025-11-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_role_to_user'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add role column to users table."""
    # Add role column with default value 'user'
    op.add_column('users', sa.Column('role', sa.String(length=50), nullable=False, server_default='user'))


def downgrade() -> None:
    """Remove role column from users table."""
    op.drop_column('users', 'role')
