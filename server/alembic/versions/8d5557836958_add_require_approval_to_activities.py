"""add require_approval to activities

Revision ID: 8d5557836958
Revises: 003_join_requests
Create Date: 2026-06-29 15:32:41.626022

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8d5557836958'
down_revision: Union[str, None] = '003_join_requests'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add require_approval to activities
    op.add_column('activities', sa.Column('require_approval', sa.Boolean(), server_default=sa.text('true'), nullable=False))


def downgrade() -> None:
    # Remove require_approval from activities
    op.drop_column('activities', 'require_approval')
