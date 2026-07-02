"""003 - Create join_requests table with partial unique index.

Revision ID: 003_join_requests
Revises: 002_activities
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "003_join_requests"
down_revision = "002_activities"
branch_labels = None
depends_on = None


def upgrade() -> None:


    op.create_table(
        "join_requests",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("activity_id", UUID(as_uuid=True), sa.ForeignKey("activities.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("status", sa.Enum("pending", "approved", "declined", "cancelled", name="request_status"), server_default="pending", nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Partial unique index: one active request per user per activity
    op.execute("""
        CREATE UNIQUE INDEX uq_active_request_per_user
        ON join_requests (activity_id, user_id)
        WHERE status IN ('pending', 'approved')
    """)


def downgrade() -> None:
    op.drop_index("uq_active_request_per_user")
    op.drop_table("join_requests")
    op.execute("DROP TYPE IF EXISTS request_status")
