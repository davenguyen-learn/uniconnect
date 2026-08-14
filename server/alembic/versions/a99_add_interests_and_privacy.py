"""Add interests, private_description, and group_privacy

Revision ID: a99_add_interests_and_privacy
Revises: 0188dd62b116
Create Date: 2026-07-31 08:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic. Max length 32 chars!
revision: str = 'a99_add_interests_and_privacy'
down_revision: Union[str, None] = '0188dd62b116'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add interests to users
    op.add_column('users', sa.Column('interests', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # 2. Add private_description to activities
    op.add_column('activities', sa.Column('private_description', sa.Text(), nullable=True))

    # 3. Add privacy enum & column to groups
    group_privacy_enum = postgresql.ENUM('public', 'private', name='group_privacy')
    group_privacy_enum.create(op.get_bind(), checkfirst=True)
    op.add_column('groups', sa.Column('privacy', sa.Enum('public', 'private', name='group_privacy'), server_default='public', nullable=False))


def downgrade() -> None:
    op.drop_column('groups', 'privacy')
    op.execute('DROP TYPE IF EXISTS group_privacy')
    op.drop_column('activities', 'private_description')
    op.drop_column('users', 'interests')
