import uuid
from typing import Sequence

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.notifications.models import Notification


async def create_notification(
    db: AsyncSession,
    user_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    type: str,
    target_type: str,
    target_id: uuid.UUID,
    message: str,
) -> Notification:
    """Create a new notification."""
    notification = Notification(
        user_id=user_id,
        actor_id=actor_id,
        type=type,
        target_type=target_type,
        target_id=target_id,
        message=message,
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification


async def list_notifications(
    db: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0,
) -> tuple[Sequence[Notification], int, int]:
    """Get notifications for a user, along with total count and unread count."""
    
    # Get total count
    total_stmt = select(func.count()).select_from(Notification).where(Notification.user_id == user_id)
    total_result = await db.execute(total_stmt)
    total = total_result.scalar() or 0
    
    # Get unread count
    unread_stmt = select(func.count()).select_from(Notification).where(
        Notification.user_id == user_id, 
        Notification.is_read == False
    )
    unread_result = await db.execute(unread_stmt)
    unread_count = unread_result.scalar() or 0
    
    # Get items
    stmt = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .offset(offset)
        .options(selectinload(Notification.actor))
    )
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    return items, total, unread_count


async def get_by_id(db: AsyncSession, notification_id: uuid.UUID) -> Notification | None:
    """Get a notification by ID."""
    stmt = select(Notification).where(Notification.id == notification_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def mark_as_read(db: AsyncSession, notification: Notification) -> Notification:
    """Mark a notification as read."""
    notification.is_read = True
    await db.commit()
    await db.refresh(notification)
    return notification


async def mark_all_as_read(db: AsyncSession, user_id: uuid.UUID) -> int:
    """Mark all notifications for a user as read."""
    stmt = (
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == False)
        .values(is_read=True)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount
