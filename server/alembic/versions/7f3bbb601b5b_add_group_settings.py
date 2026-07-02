"""Add group settings

Revision ID: 7f3bbb601b5b
Revises: 006_user_follows
Create Date: 2026-07-02 02:39:25.269862

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7f3bbb601b5b'
down_revision: Union[str, None] = '006_user_follows'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('groups', sa.Column('allow_member_activities', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('groups', sa.Column('allow_member_documents', sa.Boolean(), server_default='true', nullable=False))


def downgrade() -> None:
    op.drop_column('groups', 'allow_member_documents')
    op.drop_column('groups', 'allow_member_activities')
