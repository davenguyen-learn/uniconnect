"""add_admin_fields_to_reports

Revision ID: a1b2c3d4e5f6
Revises: 0df18bb8179e
Create Date: 2026-07-10 02:33:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '0df18bb8179e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('reports', sa.Column('admin_note', sa.Text(), nullable=True))
    op.add_column('reports', sa.Column('resolved_by', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_reports_resolved_by_users',
        'reports', 'users',
        ['resolved_by'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_reports_resolved_by_users', 'reports', type_='foreignkey')
    op.drop_column('reports', 'resolved_by')
    op.drop_column('reports', 'admin_note')
