"""Rename activity location to marker_location and location_name to meeting_location

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-09-22 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2a3b4c5d6e7'
down_revision: Union[str, None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('activities', 'location', new_column_name='marker_location')
    op.alter_column('activities', 'location_name', new_column_name='meeting_location')


def downgrade() -> None:
    op.alter_column('activities', 'marker_location', new_column_name='location')
    op.alter_column('activities', 'meeting_location', new_column_name='location_name')
