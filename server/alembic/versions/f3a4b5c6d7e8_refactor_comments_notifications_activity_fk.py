"""Refactor comments, content_likes, and notifications to use activity_id foreign key

Revision ID: f3a4b5c6d7e8
Revises: f2a3b4c5d6e7
Create Date: 2026-09-22 17:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f3a4b5c6d7e8'
down_revision: Union[str, None] = 'f2a3b4c5d6e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. COMMENTS ──
    op.add_column('comments', sa.Column('activity_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute("UPDATE comments SET activity_id = target_id")
    op.alter_column('comments', 'activity_id', nullable=False)
    op.create_foreign_key(
        'fk_comments_activity_id', 'comments', 'activities', ['activity_id'], ['id'], ondelete='CASCADE'
    )
    # Drop old indexes & columns
    op.execute("DROP INDEX IF EXISTS ix_comments_target_type")
    op.execute("DROP INDEX IF EXISTS ix_comments_target_id")
    op.execute("DROP INDEX IF EXISTS ix_comments_target")
    op.drop_column('comments', 'target_type')
    op.drop_column('comments', 'target_id')
    op.create_index('ix_comments_activity', 'comments', ['activity_id', 'created_at'])

    # ── 2. CONTENT LIKES ──
    op.add_column('content_likes', sa.Column('activity_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute("UPDATE content_likes SET activity_id = target_id")
    op.alter_column('content_likes', 'activity_id', nullable=False)
    op.create_foreign_key(
        'fk_content_likes_activity_id', 'content_likes', 'activities', ['activity_id'], ['id'], ondelete='CASCADE'
    )
    op.execute("ALTER TABLE content_likes DROP CONSTRAINT IF EXISTS uq_content_like_per_user")
    op.execute("DROP INDEX IF EXISTS ix_content_likes_target_type")
    op.execute("DROP INDEX IF EXISTS ix_content_likes_target_id")
    op.execute("DROP INDEX IF EXISTS ix_content_likes_target")
    op.drop_column('content_likes', 'target_type')
    op.drop_column('content_likes', 'target_id')
    op.create_unique_constraint('uq_content_like_per_user', 'content_likes', ['activity_id', 'user_id'])
    op.create_index('ix_content_likes_activity', 'content_likes', ['activity_id'])

    # ── 3. NOTIFICATIONS ──
    op.add_column('notifications', sa.Column('activity_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute("UPDATE notifications SET activity_id = target_id WHERE target_type = 'activity'")
    op.create_foreign_key(
        'fk_notifications_activity_id', 'notifications', 'activities', ['activity_id'], ['id'], ondelete='SET NULL'
    )
    op.drop_column('notifications', 'target_type')
    op.drop_column('notifications', 'target_id')
    op.create_index('ix_notifications_activity_id', 'notifications', ['activity_id'])


def downgrade() -> None:
    # ── 3. NOTIFICATIONS ──
    op.drop_index('ix_notifications_activity_id', table_name='notifications')
    op.drop_constraint('fk_notifications_activity_id', 'notifications', type_='foreignkey')
    op.add_column('notifications', sa.Column('target_type', sa.String(length=50), nullable=True))
    op.add_column('notifications', sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute("UPDATE notifications SET target_type = 'activity', target_id = activity_id WHERE activity_id IS NOT NULL")
    op.drop_column('notifications', 'activity_id')

    # ── 2. CONTENT LIKES ──
    op.drop_index('ix_content_likes_activity', table_name='content_likes')
    op.drop_constraint('uq_content_like_per_user', 'content_likes', type_='unique')
    op.drop_constraint('fk_content_likes_activity_id', 'content_likes', type_='foreignkey')
    op.add_column('content_likes', sa.Column('target_type', sa.String(length=20), nullable=True))
    op.add_column('content_likes', sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute("UPDATE content_likes SET target_type = 'activity', target_id = activity_id")
    op.alter_column('content_likes', 'target_type', nullable=False)
    op.alter_column('content_likes', 'target_id', nullable=False)
    op.drop_column('content_likes', 'activity_id')
    op.create_unique_constraint('uq_content_like_per_user', 'content_likes', ['target_type', 'target_id', 'user_id'])

    # ── 1. COMMENTS ──
    op.drop_index('ix_comments_activity', table_name='comments')
    op.drop_constraint('fk_comments_activity_id', 'comments', type_='foreignkey')
    op.add_column('comments', sa.Column('target_type', sa.String(length=20), nullable=True))
    op.add_column('comments', sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute("UPDATE comments SET target_type = 'activity', target_id = activity_id")
    op.alter_column('comments', 'target_type', nullable=False)
    op.alter_column('comments', 'target_id', nullable=False)
    op.drop_column('comments', 'activity_id')
