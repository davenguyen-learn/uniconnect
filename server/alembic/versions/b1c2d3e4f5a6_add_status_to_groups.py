"""Add status column to groups table

Revision ID: b1c2d3e4f5a6
Revises: 0f1e2d3c4b5a
Create Date: 2026-10-07 10:43:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = '0f1e2d3c4b5a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'groups',
        sa.Column('status', sa.String(length=20), server_default='active', nullable=False)
    )
    op.create_index(
        op.f('ix_groups_status'),
        'groups',
        ['status'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_groups_status'), table_name='groups')
    op.drop_column('groups', 'status')
