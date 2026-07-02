"""Initial migration: create all tables

Revision ID: 001
Revises:
Create Date: 2026-07-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # datasources table
    op.create_table(
        "datasources",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("host", sa.String(255), nullable=False),
        sa.Column("port", sa.Integer, nullable=False),
        sa.Column("username", sa.String(255), nullable=False),
        sa.Column("password", sa.Text, nullable=False),
        sa.Column("database", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("tables_count", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # training_data table
    op.create_table(
        "training_data",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("datasource_id", UUID(as_uuid=True), sa.ForeignKey("datasources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("sql", sa.Text, nullable=False),
        sa.Column("source", sa.String(20), default="manual"),
        sa.Column("is_approved", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # query_history table
    op.create_table(
        "query_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("datasource_id", UUID(as_uuid=True), sa.ForeignKey("datasources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("generated_sql", sa.Text),
        sa.Column("final_sql", sa.Text),
        sa.Column("executed", sa.Boolean, default=False),
        sa.Column("result_rows", sa.Integer, default=0),
        sa.Column("execution_time", sa.Float),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # system_config table
    op.create_table(
        "system_config",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("key", sa.String(255), unique=True, nullable=False),
        sa.Column("value", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def downgrade() -> None:
    op.drop_table("system_config")
    op.drop_table("query_history")
    op.drop_table("training_data")
    op.drop_table("datasources")
