"""Drop documents table and group allow_member_documents column

Revision ID: d8e9f0a1b2c3
Revises: b7c8d9e0f1a2
Create Date: 2026-09-16 17:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd8e9f0a1b2c3'
down_revision: Union[str, None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop allow_member_documents from groups table
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    group_columns = [col['name'] for col in inspector.get_columns('groups')]
    if 'allow_member_documents' in group_columns:
        op.drop_column('groups', 'allow_member_documents')

    # 2. Drop documents table if exists
    tables = inspector.get_table_names()
    if 'documents' in tables:
        indexes = [idx['name'] for idx in inspector.get_indexes('documents')]
        for idx_name in ['ix_documents_created_at', 'ix_documents_group', 'ix_documents_author']:
            if idx_name in indexes:
                op.drop_index(idx_name, table_name='documents')
        op.drop_table('documents')


def downgrade() -> None:
    op.add_column('groups', sa.Column('allow_member_documents', sa.Boolean(), server_default='true', nullable=False))
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_url', sa.String(length=500), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_type', sa.String(length=100), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_documents_author', 'documents', ['author_id'])
    op.create_index('ix_documents_group', 'documents', ['group_id'])
    op.create_index('ix_documents_created_at', 'documents', ['created_at'])
