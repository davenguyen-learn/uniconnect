import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.notifications import repository
from app.modules.notifications.schemas import NotificationListResponse, NotificationResponse


async def list_notifications(
    db: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0,
) -> NotificationListResponse:
    """List notifications for a user."""
    items, total, unread_count = await repository.list_notifications(db, user_id, limit, offset)
    
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in items],
        total=total,
        unread_count=unread_count,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )


async def mark_as_read(
    db: AsyncSession,
    notification_id: uuid.UUID,
    user_id: uuid.UUID,
) -> NotificationResponse:
    """Mark a notification as read."""
    notification = await repository.get_by_id(db, notification_id)
    if not notification:
        raise NotFoundError("Notification not found")
        
    if notification.user_id != user_id:
        raise ForbiddenError("You can only read your own notifications")
        
    updated = await repository.mark_as_read(db, notification)
    return NotificationResponse.model_validate(updated)


async def mark_all_as_read(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> dict[str, Any]:
    """Mark all notifications as read."""
    count = await repository.mark_all_as_read(db, user_id)
    return {"status": "success", "updated_count": count}


async def create_interaction_notification(
    db: AsyncSession,
    actor_id: uuid.UUID,
    owner_id: uuid.UUID,
    interaction_type: str,
    target_type: str,
    target_id: uuid.UUID,
    title: str = "",
) -> None:
    """Helper to create a notification for likes/comments if actor != owner."""
    if actor_id == owner_id:
        return
        
    message = ""
    if interaction_type == "like":
        message = f"Someone liked your {target_type} {title}".strip()
    elif interaction_type == "comment":
        message = f"Someone commented on your {target_type} {title}".strip()
    else:
        message = f"New {interaction_type} on your {target_type} {title}".strip()
        
    await repository.create_notification(
        db=db,
        user_id=owner_id,
        actor_id=actor_id,
        type=f"new_{interaction_type}",
        target_type=target_type,
        target_id=target_id,
        message=message,
    )
