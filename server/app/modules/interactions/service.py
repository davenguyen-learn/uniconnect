"""Business logic for comments and likes (polymorphic)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.modules.interactions import repository
from app.modules.interactions.schemas import (
    CommentCreate,
    CommentListResponse,
    CommentResponse,
    CommentUpdate,
    ContentStatsResponse,
    LikeResponse,
)

# Valid target types — extend this when adding new content types
VALID_TARGET_TYPES = {"activity", "document"}


async def _validate_target(db: AsyncSession, target_type: str, target_id: uuid.UUID):
    """Verify the target exists and is not deleted."""
    if target_type not in VALID_TARGET_TYPES:
        raise ValidationError(f"Invalid target type: {target_type}")

    if target_type == "activity":
        from app.modules.activities.repository import get_by_id
        obj = await get_by_id(db, target_id)
        if not obj:
            raise NotFoundError("Activity not found.")
        return obj

    raise ValidationError(f"Unsupported target type: {target_type}")


# ── Comments ──


async def create_comment(
    db: AsyncSession,
    target_type: str,
    target_id: uuid.UUID,
    user_id: uuid.UUID,
    data: CommentCreate,
) -> CommentResponse:
    """Create a comment or reply on an activity."""
    target_obj = await _validate_target(db, target_type, target_id)

    # Validate parent exists and enforce 1-level nesting
    if data.parent_id:
        parent = await repository.get_comment_by_id(db, data.parent_id)
        if not parent or parent.is_deleted:
            raise NotFoundError("Parent comment not found.")
        if parent.parent_id is not None:
            raise ValidationError("Replies can only be one level deep.")
        if parent.activity_id != target_id:
            raise ValidationError("Parent comment does not belong to this activity.")

    comment = await repository.create_comment(
        db,
        activity_id=target_id,
        user_id=user_id,
        content=data.content,
        parent_id=data.parent_id,
    )
    
    # Notify activity host
    from app.modules.notifications.service import create_interaction_notification
    owner_id = getattr(target_obj, "host_id", getattr(target_obj, "author_id", None))
    if owner_id:
        title = getattr(target_obj, "title", "activity")
        await create_interaction_notification(db, user_id, owner_id, "comment", target_id, title)
        
    return CommentResponse.model_validate(comment)

async def list_comments(
    db: AsyncSession,
    target_type: str,
    target_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0,
) -> CommentListResponse:
    """List top-level comments with their replies."""
    await _validate_target(db, target_type, target_id)

    comments, total = await repository.list_comments(db, target_id, limit, offset)
    return CommentListResponse(
        items=[CommentResponse.model_validate(c) for c in comments],
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )


async def update_comment(
    db: AsyncSession,
    comment_id: uuid.UUID,
    user_id: uuid.UUID,
    data: CommentUpdate,
) -> CommentResponse:
    """Update a comment (author only)."""
    comment = await repository.get_comment_by_id(db, comment_id)
    if not comment or comment.is_deleted:
        raise NotFoundError("Comment not found.")
    if comment.user_id != user_id:
        raise ForbiddenError("You can only edit your own comments.")

    updated = await repository.update_comment(db, comment, data.content)
    return CommentResponse.model_validate(updated)


async def delete_comment(
    db: AsyncSession,
    comment_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """Soft-delete a comment (author only)."""
    comment = await repository.get_comment_by_id(db, comment_id)
    if not comment or comment.is_deleted:
        raise NotFoundError("Comment not found.")
    if comment.user_id != user_id:
        raise ForbiddenError("You can only delete your own comments.")

    await repository.soft_delete_comment(db, comment)


# ── Likes ──


async def toggle_like(
    db: AsyncSession,
    target_type: str,
    target_id: uuid.UUID,
    user_id: uuid.UUID,
) -> LikeResponse:
    """Toggle like on an activity."""
    target_obj = await _validate_target(db, target_type, target_id)

    liked = await repository.toggle_like(db, target_id, user_id)
    
    if liked:
        # Notify activity host
        from app.modules.notifications.service import create_interaction_notification
        owner_id = getattr(target_obj, "host_id", getattr(target_obj, "author_id", None))
        if owner_id:
            title = getattr(target_obj, "title", "activity")
            await create_interaction_notification(db, user_id, owner_id, "like", target_id, title)
            
    total = await repository.count_likes(db, target_id)
    return LikeResponse(liked=liked, total_likes=total)


async def get_like_status(
    db: AsyncSession,
    target_type: str,
    target_id: uuid.UUID,
    user_id: uuid.UUID,
) -> LikeResponse:
    """Get like status and count for an activity."""
    await _validate_target(db, target_type, target_id)

    liked = await repository.is_liked_by_user(db, target_id, user_id)
    total = await repository.count_likes(db, target_id)
    return LikeResponse(liked=liked, total_likes=total)


async def get_content_stats(
    db: AsyncSession,
    target_type: str,
    target_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ContentStatsResponse:
    """Get aggregated stats (like count, comment count, user like status)."""
    await _validate_target(db, target_type, target_id)

    like_count = await repository.count_likes(db, target_id)
    comment_count = await repository.count_comments(db, target_id)
    is_liked = await repository.is_liked_by_user(db, target_id, user_id)

    return ContentStatsResponse(
        like_count=like_count,
        comment_count=comment_count,
        is_liked=is_liked,
    )
