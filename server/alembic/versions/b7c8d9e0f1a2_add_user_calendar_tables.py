"""Add user calendar tables (user_busy_slots, busy_slot_exceptions, user_vacation_periods)

Revision ID: b7c8d9e0f1a2
Revises: 1e6fb1fb3bc2
Create Date: 2026-09-16 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, None] = '1e6fb1fb3bc2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. user_busy_slots
    op.create_table(
        'user_busy_slots',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('recurrence', sa.String(length=20), server_default='none', nullable=False),
        sa.Column('start_datetime', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_datetime', sa.DateTime(timezone=True), nullable=True),
        sa.Column('day_of_week', sa.Integer(), nullable=True),
        sa.Column('start_time_of_day', sa.Time(), nullable=True),
        sa.Column('end_time_of_day', sa.Time(), nullable=True),
        sa.Column('valid_from', sa.Date(), nullable=True),
        sa.Column('valid_until', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_busy_user_weekly', 'user_busy_slots', ['user_id', 'day_of_week', 'start_time_of_day', 'end_time_of_day'])
    op.create_index('idx_busy_user_onetime', 'user_busy_slots', ['user_id', 'start_datetime', 'end_datetime'])
    op.create_index(op.f('ix_user_busy_slots_user_id'), 'user_busy_slots', ['user_id'])

    # 2. busy_slot_exceptions
    op.create_table(
        'busy_slot_exceptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('busy_slot_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('skip_date', sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(['busy_slot_id'], ['user_busy_slots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_busy_exception_slot_date', 'busy_slot_exceptions', ['busy_slot_id', 'skip_date'], unique=True)
    op.create_index(op.f('ix_busy_slot_exceptions_busy_slot_id'), 'busy_slot_exceptions', ['busy_slot_id'])

    # 3. user_vacation_periods
    op.create_table(
        'user_vacation_periods',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_vacation_user_dates', 'user_vacation_periods', ['user_id', 'start_date', 'end_date'])
    op.create_index(op.f('ix_user_vacation_periods_user_id'), 'user_vacation_periods', ['user_id'])


def downgrade() -> None:
    op.drop_table('user_vacation_periods')
    op.drop_table('busy_slot_exceptions')
    op.drop_table('user_busy_slots')
