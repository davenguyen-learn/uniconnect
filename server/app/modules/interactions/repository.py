"""Data access layer for comments and likes (polymorphic)."""

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.interactions.models import Comment, ContentLike


# ── Comments ──


async def create_comment(
    db: AsyncSession,
    target_type: str,
    target_id: uuid.UUID,
    user_id: uuid.UUID,
    content: str,
    parent_id: uuid.UUID | None = None,
) -> Comment:
    """Insert a new comment."""
    comment = Comment(
        target_type=target_type,
        target_id=target_id,
        user_id=user_id,
        content=content,
        parent_id=parent_id,
    )
    db.add(comment)
    await db.flush()
    # Reload with user relationship
    result = await db.execute(
        select(Comment)
        .options(joinedload(Comment.user))
        .where(Comment.id == comment.id)
    )
    return result.scalar_one()


async def get_comment_by_id(db: AsyncSession, comment_id: uuid.UUID) -> Comment | None:
    """Fetch a single comment by ID."""
    result = await db.execute(
        select(Comment)
        .options(joinedload(Comment.user))
        .where(Comment.id == comment_id)
    )
    return result.scalar_one_or_none()


async def list_comments(
    db: AsyncSession,
    target_type: str,
    target_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Comment], int]:
    """List top-level comments for a target with their replies.

    Returns (comments, total_count).
    """
    target_filter = (
        Comment.target_type == target_type,
        Comment.target_id == target_id,
    )

    # Count total top-level comments
    count_q = (
        select(func.count())
        .select_from(Comment)
        .where(
            *target_filter,
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
            *target_filter,
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


async def count_comments(db: AsyncSession, target_type: str, target_id: uuid.UUID) -> int:
    """Count all non-deleted comments for a target."""
    result = await db.execute(
        select(func.count())
        .select_from(Comment)
        .where(
            Comment.target_type == target_type,
            Comment.target_id == target_id,
            Comment.is_deleted.is_(False),
        )
    )
    return result.scalar() or 0


# ── Likes ──


async def toggle_like(
    db: AsyncSession, target_type: str, target_id: uuid.UUID, user_id: uuid.UUID
) -> bool:
    """Toggle like. Returns True if liked, False if unliked."""
    existing = await db.execute(
        select(ContentLike).where(
            ContentLike.target_type == target_type,
            ContentLike.target_id == target_id,
            ContentLike.user_id == user_id,
        )
    )
    like = existing.scalar_one_or_none()

    if like:
        await db.execute(delete(ContentLike).where(ContentLike.id == like.id))
        await db.flush()
        return False
    else:
        db.add(ContentLike(target_type=target_type, target_id=target_id, user_id=user_id))
        await db.flush()
        return True


async def is_liked_by_user(
    db: AsyncSession, target_type: str, target_id: uuid.UUID, user_id: uuid.UUID
) -> bool:
    """Check if a user has liked a target."""
    result = await db.execute(
        select(func.count())
        .select_from(ContentLike)
        .where(
            ContentLike.target_type == target_type,
            ContentLike.target_id == target_id,
            ContentLike.user_id == user_id,
        )
    )
    return (result.scalar() or 0) > 0


async def count_likes(db: AsyncSession, target_type: str, target_id: uuid.UUID) -> int:
    """Count total likes for a target."""
    result = await db.execute(
        select(func.count())
        .select_from(ContentLike)
        .where(
            ContentLike.target_type == target_type,
            ContentLike.target_id == target_id,
        )
    )
    return result.scalar() or 0
