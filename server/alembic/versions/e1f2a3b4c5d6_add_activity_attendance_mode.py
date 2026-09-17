"""Add activity attendance_mode, check_in_code, check_in_radius

Revision ID: e1f2a3b4c5d6
Revises: d8e9f0a1b2c3
Create Date: 2026-09-16 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, None] = 'd8e9f0a1b2c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('activities', sa.Column('attendance_mode', sa.String(length=20), server_default='manual', nullable=False))
    op.add_column('activities', sa.Column('check_in_code', sa.String(length=64), nullable=True))
    op.add_column('activities', sa.Column('check_in_radius', sa.Integer(), server_default='300', nullable=False))
    op.create_index(op.f('ix_activities_check_in_code'), 'activities', ['check_in_code'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_activities_check_in_code'), table_name='activities')
    op.drop_column('activities', 'check_in_radius')
    op.drop_column('activities', 'check_in_code')
    op.drop_column('activities', 'attendance_mode')
