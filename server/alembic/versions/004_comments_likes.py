"""add comments and content_likes (polymorphic)

Revision ID: 004_comments_likes
Revises: 370b82b2f3f4
Create Date: 2026-07-01 23:07:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004_comments_likes'
down_revision: Union[str, None] = '370b82b2f3f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Comments table (Polymorphic) ──
    op.create_table(
        'comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('target_type', sa.String(length=20), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['comments.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_comments_target_type', 'comments', ['target_type'])
    op.create_index('ix_comments_target_id', 'comments', ['target_id'])
    op.create_index('ix_comments_user_id', 'comments', ['user_id'])
    op.create_index('ix_comments_parent_id', 'comments', ['parent_id'])
    op.create_index('ix_comments_target', 'comments', ['target_type', 'target_id', 'created_at'])

    # ── Content likes table (Polymorphic) ──
    op.create_table(
        'content_likes',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('target_type', sa.String(length=20), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('target_type', 'target_id', 'user_id', name='uq_content_like_per_user'),
    )
    op.create_index('ix_content_likes_target_type', 'content_likes', ['target_type'])
    op.create_index('ix_content_likes_target_id', 'content_likes', ['target_id'])
    op.create_index('ix_content_likes_user_id', 'content_likes', ['user_id'])
    op.create_index('ix_content_likes_target', 'content_likes', ['target_type', 'target_id'])


def downgrade() -> None:
    op.drop_table('content_likes')
    op.drop_table('comments')
