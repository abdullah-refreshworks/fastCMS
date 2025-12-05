"""add_langgraph_integration_support

Revision ID: 57348398da9a
Revises: fb06c7171ada
Create Date: 2025-12-03 10:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "57348398da9a"
down_revision: Union[str, None] = "fb06c7171ada"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add langgraph integration tables - already applied."""
    # Tables already exist in database, this is a stub migration
    pass


def downgrade() -> None:
    """Remove langgraph integration tables."""
    # Would drop langgraph_* tables if needed
    pass
