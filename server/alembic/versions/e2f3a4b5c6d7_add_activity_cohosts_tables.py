"""add activity cohosts tables

Revision ID: e2f3a4b5c6d7
Revises: c7d8e9f0a1b2
Create Date: 2026-09-25 12:55:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e2f3a4b5c6d7'
down_revision = 'c7d8e9f0a1b2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE IF NOT EXISTS activity_cohosts (
        id UUID PRIMARY KEY,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
        activity_id UUID NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
        group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
        CONSTRAINT uq_activity_cohost UNIQUE (activity_id, group_id)
    )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_cohost_group ON activity_cohosts(group_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_cohost_activity ON activity_cohosts(activity_id)")

    op.execute("""
    CREATE TABLE IF NOT EXISTS activity_cohost_invitations (
        id UUID PRIMARY KEY,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
        activity_id UUID NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
        host_group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
        invited_group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
        status VARCHAR(20) NOT NULL DEFAULT 'pending',
        message TEXT
    )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_invite_group_status ON activity_cohost_invitations(invited_group_id, status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_invite_act_status ON activity_cohost_invitations(activity_id, status)")


def downgrade() -> None:
    op.drop_table('activity_cohost_invitations')
    op.drop_table('activity_cohosts')
