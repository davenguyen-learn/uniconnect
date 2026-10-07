"""Add live checkin columns to activities table

Revision ID: 0f1e2d3c4b5a
Revises: f3e2d1c0b9a8
Create Date: 2026-10-07 10:38:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0f1e2d3c4b5a'
down_revision: Union[str, None] = 'f3e2d1c0b9a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'activities',
        sa.Column('live_checkin_lat', sa.Float(), nullable=True)
    )
    op.add_column(
        'activities',
        sa.Column('live_checkin_lng', sa.Float(), nullable=True)
    )
    op.add_column(
        'activities',
        sa.Column('live_checkin_radius', sa.Integer(), server_default='50', nullable=True)
    )
    op.add_column(
        'activities',
        sa.Column('live_checkin_expires_at', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('activities', 'live_checkin_expires_at')
    op.drop_column('activities', 'live_checkin_radius')
    op.drop_column('activities', 'live_checkin_lng')
    op.drop_column('activities', 'live_checkin_lat')
