"""002 - Create activities table with PostGIS spatial index.

Revision ID: 002_activities
Revises: 001_initial
"""

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geography
from sqlalchemy.dialects.postgresql import UUID

revision = "002_activities"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:


    op.create_table(
        "activities",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("host_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(50), nullable=True, index=True),
        sa.Column("location", Geography(geometry_type="POINT", srid=4326), nullable=True),
        sa.Column("location_name", sa.String(200), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("max_participants", sa.Integer(), nullable=False),
        sa.Column("current_participants", sa.Integer(), server_default="1", nullable=False),
        sa.Column("privacy", sa.Enum("public", "private", name="activity_privacy"), server_default="public", nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False, index=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("max_participants > 0", name="ck_positive_capacity"),
        sa.CheckConstraint("end_time > start_time", name="ck_end_after_start"),
        sa.CheckConstraint("current_participants >= 0", name="ck_nonneg_participants"),
    )

    # GiST spatial index for efficient radius queries
    op.create_index("idx_activity_location", "activities", ["location"], postgresql_using="gist")


def downgrade() -> None:
    op.drop_index("idx_activity_location")
    op.drop_table("activities")
    op.execute("DROP TYPE IF EXISTS activity_privacy")
