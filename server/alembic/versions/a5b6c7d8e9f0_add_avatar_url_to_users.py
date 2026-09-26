"""Add avatar_url to users table

Revision ID: a5b6c7d8e9f0
Revises: f4b5c6d7e8f9
Create Date: 2026-09-23 11:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5b6c7d8e9f0'
down_revision: Union[str, None] = 'f4b5c6d7e8f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('avatar_url', sa.String(length=500), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('users', 'avatar_url')
