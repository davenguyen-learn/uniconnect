"""add_reports

Revision ID: 0df18bb8179e
Revises: c9de6a84bcb5
Create Date: 2026-07-02 07:59:52.640935

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0df18bb8179e'
down_revision: Union[str, None] = 'c9de6a84bcb5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('reports',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('reporter_id', sa.UUID(), nullable=False),
    sa.Column('target_type', sa.String(length=50), nullable=False),
    sa.Column('target_id', sa.Uuid(), nullable=False),
    sa.Column('reason', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['reporter_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reports_reporter_id'), 'reports', ['reporter_id'], unique=False)
    op.create_index(op.f('ix_reports_status'), 'reports', ['status'], unique=False)
    op.create_index(op.f('ix_reports_target_id'), 'reports', ['target_id'], unique=False)
    op.create_index(op.f('ix_reports_target_type'), 'reports', ['target_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_reports_target_type'), table_name='reports')
    op.drop_index(op.f('ix_reports_target_id'), table_name='reports')
    op.drop_index(op.f('ix_reports_status'), table_name='reports')
    op.drop_index(op.f('ix_reports_reporter_id'), table_name='reports')
    op.drop_table('reports')
