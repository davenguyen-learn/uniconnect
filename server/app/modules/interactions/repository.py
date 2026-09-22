"""Data access layer for comments and likes (polymorphic)."""

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.interactions.models import Comment, ContentLike


# ── Comments ──


async def create_comment(
    db: AsyncSession,
    activity_id: uuid.UUID,
    user_id: uuid.UUID,
    content: str,
    parent_id: uuid.UUID | None = None,
    **kwargs,
) -> Comment:
    """Insert a new comment on an activity."""
    comment = Comment(
        activity_id=activity_id,
        user_id=user_id,
        content=content,
        parent_id=parent_id,
    )
    db.add(comment)
    await db.flush()
    # Reload with user relationship
    result = await db.execute(
        select(Comment)
        .options(
            joinedload(Comment.user),
            joinedload(Comment.replies)
        )
        .where(Comment.id == comment.id)
    )
    return result.unique().scalar_one()


async def get_comment_by_id(db: AsyncSession, comment_id: uuid.UUID) -> Comment | None:
    """Fetch a single comment by ID."""
    result = await db.execute(
        select(Comment)
        .options(
            joinedload(Comment.user),
            joinedload(Comment.replies)
        )
        .where(Comment.id == comment_id)
    )
    return result.unique().scalar_one_or_none()


async def list_comments(
    db: AsyncSession,
    activity_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0,
    **kwargs,
) -> tuple[list[Comment], int]:
    """List top-level comments for an activity with their replies.

    Returns (comments, total_count).
    """
    # Count total top-level comments
    count_q = (
        select(func.count())
        .select_from(Comment)
        .where(
            Comment.activity_id == activity_id,
            Comment.parent_id.is_(None),
            Comment.is_deleted.is_(False),
        )
    )
    total = (await db.execute(count_q)).scalar() or 0

    # Fetch top-level comments with user + replies
    q = (
        select(Comment)
        .options(
            joinedload(Comment.user),
            joinedload(Comment.replies).joinedload(Comment.user),
        )
        .where(
            Comment.activity_id == activity_id,
            Comment.parent_id.is_(None),
            Comment.is_deleted.is_(False),
        )
        .order_by(Comment.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(q)
    comments = result.unique().scalars().all()
    return list(comments), total


async def update_comment(db: AsyncSession, comment: Comment, content: str) -> Comment:
    """Update a comment's content."""
    comment.content = content
    await db.flush()
    return comment


async def soft_delete_comment(db: AsyncSession, comment: Comment) -> Comment:
    """Soft-delete a comment (keeps replies visible)."""
    comment.is_deleted = True
    comment.content = "[deleted]"
    await db.flush()
    return comment


async def count_comments(db: AsyncSession, activity_id: uuid.UUID, **kwargs) -> int:
    """Count all non-deleted comments for an activity."""
    result = await db.execute(
        select(func.count())
        .select_from(Comment)
        .where(
            Comment.activity_id == activity_id,
            Comment.is_deleted.is_(False),
        )
    )
    return result.scalar() or 0


# ── Likes ──


async def toggle_like(
    db: AsyncSession, activity_id: uuid.UUID, user_id: uuid.UUID, **kwargs
) -> bool:
    """Toggle like. Returns True if liked, False if unliked."""
    existing = await db.execute(
        select(ContentLike).where(
            ContentLike.activity_id == activity_id,
            ContentLike.user_id == user_id,
        )
    )
    like = existing.scalar_one_or_none()

    if like:
        await db.execute(delete(ContentLike).where(ContentLike.id == like.id))
        await db.flush()
        return False
    else:
        db.add(ContentLike(activity_id=activity_id, user_id=user_id))
        await db.flush()
        return True


async def is_liked_by_user(
    db: AsyncSession, activity_id: uuid.UUID, user_id: uuid.UUID, **kwargs
) -> bool:
    """Check if a user has liked an activity."""
    result = await db.execute(
        select(func.count())
        .select_from(ContentLike)
        .where(
            ContentLike.activity_id == activity_id,
            ContentLike.user_id == user_id,
        )
    )
    return (result.scalar() or 0) > 0


async def count_likes(db: AsyncSession, activity_id: uuid.UUID, **kwargs) -> int:
    """Count total likes for an activity."""
    result = await db.execute(
        select(func.count())
        .select_from(ContentLike)
        .where(
            ContentLike.activity_id == activity_id,
        )
    )
    return result.scalar() or 0
