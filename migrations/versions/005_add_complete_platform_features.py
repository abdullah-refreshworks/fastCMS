"""add complete platform features

Revision ID: 005
Revises: 004
Create Date: 2025-11-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add all new tables for complete platform"""

    # Request logs
    op.create_table(
        "request_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("user_agent", sa.Text()),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("auth_user_id", sa.String(36)),
        sa.Column("request_body", sa.Text()),
        sa.Column("response_body", sa.Text()),
        sa.Column("error", sa.Text()),
        sa.Column("created", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_logs_created", "request_logs", ["created"])
    op.create_index("idx_logs_status", "request_logs", ["status_code"])
    op.create_index("idx_logs_user", "request_logs", ["auth_user_id"])
    op.create_index("idx_logs_method", "request_logs", ["method"])
    op.create_index("idx_logs_ip", "request_logs", ["ip_address"])

    # Settings
    op.create_table(
        "settings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("key", sa.String(100), unique=True, nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_settings_key", "settings", ["key"])
    op.create_index("idx_settings_category", "settings", ["category"])

    # Backups
    op.create_table(
        "backups",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("location", sa.String(20), nullable=False),
        sa.Column("s3_key", sa.String(500)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("error", sa.Text()),
        sa.Column("created_by", sa.String(36)),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime()),
    )
    op.create_index("idx_backups_status", "backups", ["status"])
    op.create_index("idx_backups_created", "backups", ["created"])

    # Email templates
    op.create_table(
        "email_templates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("key", sa.String(100), unique=True, nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("body_html", sa.Text(), nullable=False),
        sa.Column("body_text", sa.Text()),
        sa.Column("variables", sa.Text()),
        sa.Column("enabled", sa.Boolean(), default=True),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_email_templates_key", "email_templates", ["key"])

    # Add view_query and manage_rule to collections
    with op.batch_alter_table("collections") as batch_op:
        batch_op.add_column(sa.Column("view_query", sa.Text()))
        batch_op.add_column(sa.Column("manage_rule", sa.Text()))


def downgrade() -> None:
    """Drop all new tables"""
    op.drop_table("email_templates")
    op.drop_table("backups")
    op.drop_table("settings")
    op.drop_table("request_logs")

    # Remove new columns from collections
    with op.batch_alter_table("collections") as batch_op:
        batch_op.drop_column("view_query")
        batch_op.drop_column("manage_rule")
