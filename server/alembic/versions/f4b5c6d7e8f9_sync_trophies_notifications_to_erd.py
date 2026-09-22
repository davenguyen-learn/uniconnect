"""Sync trophies and notifications to match ERD 2

Revision ID: f4b5c6d7e8f9
Revises: f3a4b5c6d7e8
Create Date: 2026-09-22 19:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f4b5c6d7e8f9'
down_revision: Union[str, None] = 'f3a4b5c6d7e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. NOTIFICATIONS: Add action_url ──
    op.add_column('notifications', sa.Column('action_url', sa.String(length=255), nullable=True))

    # ── 2. TROPHIES: Add activity_id FK, drop creator_id, points, icon ──
    op.add_column('trophies', sa.Column('activity_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute("UPDATE trophies SET activity_id = a.id FROM activities a WHERE a.trophy_id = trophies.id")
    op.create_foreign_key(
        'fk_trophies_activity_id', 'trophies', 'activities', ['activity_id'], ['id'], ondelete='CASCADE'
    )
    op.create_index('ix_trophies_activity_id', 'trophies', ['activity_id'])

    # Drop creator_id
    op.drop_constraint('trophies_creator_id_fkey', 'trophies', type_='foreignkey')
    op.drop_index('ix_trophies_creator_id', table_name='trophies')
    op.drop_column('trophies', 'creator_id')

    # Drop points and icon
    op.drop_column('trophies', 'points')
    op.drop_column('trophies', 'icon')

    # ── 3. ACTIVITIES: Drop trophy_id ──
    op.drop_constraint('activities_trophy_id_fkey', 'activities', type_='foreignkey')
    op.drop_index('ix_activities_trophy_id', table_name='activities')
    op.drop_column('activities', 'trophy_id')


def downgrade() -> None:
    # ── 3. ACTIVITIES: Re-add trophy_id ──
    op.add_column('activities', sa.Column('trophy_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index('ix_activities_trophy_id', 'activities', ['trophy_id'])
    op.create_foreign_key(
        'activities_trophy_id_fkey', 'activities', 'trophies', ['trophy_id'], ['id'], ondelete='SET NULL'
    )
    op.execute("UPDATE activities SET trophy_id = t.id FROM trophies t WHERE t.activity_id = activities.id")

    # ── 2. TROPHIES: Re-add creator_id, points, icon, drop activity_id ──
    op.add_column('trophies', sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute("UPDATE trophies SET creator_id = a.host_id FROM activities a WHERE a.id = trophies.activity_id")
    op.create_foreign_key(
        'trophies_creator_id_fkey', 'trophies', 'users', ['creator_id'], ['id'], ondelete='CASCADE'
    )
    op.create_index('ix_trophies_creator_id', 'trophies', ['creator_id'])
    op.add_column('trophies', sa.Column('points', sa.Integer(), server_default='0', nullable=False))
    op.add_column('trophies', sa.Column('icon', sa.String(length=50), nullable=True))

    op.drop_index('ix_trophies_activity_id', table_name='trophies')
    op.drop_constraint('fk_trophies_activity_id', 'trophies', type_='foreignkey')
    op.drop_column('trophies', 'activity_id')

    # ── 1. NOTIFICATIONS: Drop action_url ──
    op.drop_column('notifications', 'action_url')
