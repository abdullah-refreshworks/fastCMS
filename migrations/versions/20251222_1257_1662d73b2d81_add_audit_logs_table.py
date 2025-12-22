"""add_audit_logs_table

Revision ID: 1662d73b2d81
Revises: 621bae4ce6a1
Create Date: 2025-12-22 12:57:40.797207

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1662d73b2d81"
down_revision: Union[str, None] = "621bae4ce6a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create audit_logs table."""
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False, index=True),
        sa.Column("event_action", sa.String(50), nullable=False, index=True),
        sa.Column("severity", sa.String(20), nullable=False, index=True, server_default="info"),
        sa.Column("user_id", sa.String(36), nullable=True, index=True),
        sa.Column("user_email", sa.String(255), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("outcome", sa.String(20), nullable=False, server_default="success"),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("created", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Create composite indexes
    op.create_index(
        "ix_audit_logs_event_type_action",
        "audit_logs",
        ["event_type", "event_action"],
    )
    op.create_index(
        "ix_audit_logs_user_created",
        "audit_logs",
        ["user_id", "created"],
    )
    op.create_index(
        "ix_audit_logs_severity_created",
        "audit_logs",
        ["severity", "created"],
    )


def downgrade() -> None:
    """Drop audit_logs table."""
    op.drop_index("ix_audit_logs_severity_created", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_created", table_name="audit_logs")
    op.drop_index("ix_audit_logs_event_type_action", table_name="audit_logs")
    op.drop_table("audit_logs")
