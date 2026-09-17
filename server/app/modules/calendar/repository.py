import uuid
from datetime import date, datetime
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.calendar.models import UserBusySlot, BusySlotException, UserVacationPeriod
from app.modules.activities.models import Activity
from app.modules.participation.models import JoinRequest, RequestStatus


async def create_busy_slot(db: AsyncSession, slot: UserBusySlot) -> UserBusySlot:
    db.add(slot)
    await db.commit()
    await db.refresh(slot)
    return slot


async def get_busy_slot_by_id(db: AsyncSession, slot_id: uuid.UUID, user_id: uuid.UUID) -> UserBusySlot | None:
    stmt = (
        select(UserBusySlot)
        .where(UserBusySlot.id == slot_id, UserBusySlot.user_id == user_id)
        .options(selectinload(UserBusySlot.exceptions))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_busy_slots(db: AsyncSession, user_id: uuid.UUID) -> list[UserBusySlot]:
    stmt = (
        select(UserBusySlot)
        .where(UserBusySlot.user_id == user_id)
        .options(selectinload(UserBusySlot.exceptions))
        .order_by(UserBusySlot.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def delete_busy_slot(db: AsyncSession, slot: UserBusySlot) -> None:
    await db.delete(slot)
    await db.commit()


async def add_slot_exception(db: AsyncSession, slot_id: uuid.UUID, skip_date: date) -> BusySlotException:
    exc = BusySlotException(busy_slot_id=slot_id, skip_date=skip_date)
    db.add(exc)
    await db.commit()
    await db.refresh(exc)
    return exc


async def get_user_vacations(db: AsyncSession, user_id: uuid.UUID) -> list[UserVacationPeriod]:
    stmt = (
        select(UserVacationPeriod)
        .where(UserVacationPeriod.user_id == user_id)
        .order_by(UserVacationPeriod.start_date.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_user_approved_activities(
    db: AsyncSession, user_id: uuid.UUID, start_time: datetime | None = None, end_time: datetime | None = None
) -> list[Activity]:
    """Get all activities user has an approved join request for."""
    stmt = (
        select(Activity)
        .join(JoinRequest, JoinRequest.activity_id == Activity.id)
        .where(
            JoinRequest.user_id == user_id,
            JoinRequest.status == RequestStatus.approved,
            Activity.is_deleted.is_(False),
        )
    )
    if start_time:
        stmt = stmt.where(Activity.end_time >= start_time)
    if end_time:
        stmt = stmt.where(Activity.start_time <= end_time)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_user_hosted_activities(
    db: AsyncSession, user_id: uuid.UUID, start_time: datetime | None = None, end_time: datetime | None = None
) -> list[Activity]:
    """Get all active activities where user is the host."""
    stmt = (
        select(Activity)
        .where(
            Activity.host_id == user_id,
            Activity.is_deleted.is_(False),
        )
    )
    if start_time:
        stmt = stmt.where(Activity.end_time >= start_time)
    if end_time:
        stmt = stmt.where(Activity.start_time <= end_time)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_user_pending_join_requests(db: AsyncSession, user_id: uuid.UUID) -> list[JoinRequest]:
    """Get active pending join requests of user, including activity."""
    stmt = (
        select(JoinRequest)
        .join(Activity, Activity.id == JoinRequest.activity_id)
        .where(
            JoinRequest.user_id == user_id,
            JoinRequest.status == RequestStatus.pending,
            Activity.is_deleted.is_(False),
        )
        .options(selectinload(JoinRequest.activity))
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
