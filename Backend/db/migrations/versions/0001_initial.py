"""Create initial persisted dataset tables."""

from alembic import op
import sqlalchemy as sa


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "datasets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("columns", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "dataset_mappings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("dataset_id", sa.Integer(), sa.ForeignKey("datasets.id"), nullable=False, unique=True),
        sa.Column("agent_response", sa.JSON(), nullable=False),
    )
    op.create_table(
        "partner_rows",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("dataset_id", sa.Integer(), sa.ForeignKey("datasets.id"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("identifier_norm", sa.Text(), nullable=True),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("dataset_id", "identifier_norm", name="uq_partner_rows_dataset_identifier"),
    )
    op.create_index("ix_partner_rows_dataset_position", "partner_rows", ["dataset_id", "position"])


def downgrade() -> None:
    op.drop_index("ix_partner_rows_dataset_position", table_name="partner_rows")
    op.drop_table("partner_rows")
    op.drop_table("dataset_mappings")
    op.drop_table("datasets")
