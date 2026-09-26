"""Add trophy_grant_requests table and unique constraint on user_trophies

Revision ID: b6c7d8e9f0a1
Revises: a5b6c7d8e9f0
Create Date: 2026-09-23 13:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b6c7d8e9f0a1'
down_revision: Union[str, None] = 'a5b6c7d8e9f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create trophy_grant_requests table
    op.create_table(
        'trophy_grant_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('activity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('activities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('trophy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('trophies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.Enum('insufficient_quorum', 'eligible_for_review', 'approved', 'rejected', name='trophy_grant_status', create_type=True), nullable=False),
        sa.Column('min_participants_required', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('actual_attended_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('activity_id', name='uq_trophy_grant_request_activity'),
        sa.CheckConstraint('actual_attended_count >= 0', name='ck_trophy_request_attended_count_nonneg'),
        sa.CheckConstraint('min_participants_required > 0', name='ck_trophy_request_min_participants_pos'),
    )

    # 3. Add UniqueConstraint on user_trophies (activity_id, user_id)
    op.create_unique_constraint(
        'uq_user_trophy_activity_user',
        'user_trophies',
        ['activity_id', 'user_id']
    )


def downgrade() -> None:
    op.drop_constraint('uq_user_trophy_activity_user', 'user_trophies', type_='unique')
    op.drop_table('trophy_grant_requests')
    op.execute('DROP TYPE IF EXISTS trophy_grant_status;')
