"""Participation repository — transactional capacity management with row locking."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, and_, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.activities.models import Activity
from app.modules.participation.models import JoinRequest, RequestStatus


async def create(db: AsyncSession, join_request: JoinRequest) -> JoinRequest:
    """Insert a new join request."""
    db.add(join_request)
    await db.flush()

    result = await db.execute(
        select(JoinRequest)
        .options(joinedload(JoinRequest.user))
        .where(JoinRequest.id == join_request.id)
    )
    return result.scalar_one()


async def get_by_id(db: AsyncSession, request_id: uuid.UUID) -> JoinRequest | None:
    """Fetch a join request by ID with relationships."""
    result = await db.execute(
        select(JoinRequest)
        .options(joinedload(JoinRequest.user), joinedload(JoinRequest.activity))
        .where(JoinRequest.id == request_id)
    )
    return result.scalar_one_or_none()


async def get_active_request(
    db: AsyncSession, activity_id: uuid.UUID, user_id: uuid.UUID
) -> JoinRequest | None:
    """Check if user already has an active (pending/approved) request for this activity."""
    result = await db.execute(
        select(JoinRequest).where(
            and_(
                JoinRequest.activity_id == activity_id,
                JoinRequest.user_id == user_id,
                JoinRequest.status.in_([RequestStatus.pending, RequestStatus.approved]),
            )
        )
    )
    return result.scalar_one_or_none()


async def list_by_activity(
    db: AsyncSession, activity_id: uuid.UUID
) -> list[JoinRequest]:
    """List all join requests for an activity."""
    result = await db.execute(
        select(JoinRequest)
        .options(joinedload(JoinRequest.user))
        .where(JoinRequest.activity_id == activity_id)
        .order_by(JoinRequest.created_at.desc())
    )
    return list(result.unique().scalars().all())


async def list_by_user(
    db: AsyncSession, activity_id: uuid.UUID, user_id: uuid.UUID
) -> list[JoinRequest]:
    """List a specific user's requests for an activity."""
    result = await db.execute(
        select(JoinRequest)
        .options(joinedload(JoinRequest.user))
        .where(
            and_(
                JoinRequest.activity_id == activity_id,
                JoinRequest.user_id == user_id,
            )
        )
        .order_by(JoinRequest.created_at.desc())
    )
    return list(result.unique().scalars().all())


async def update_status(
    db: AsyncSession, join_request: JoinRequest, status: RequestStatus
) -> JoinRequest:
    """Update a join request's status."""
    join_request.status = status
    if status in (RequestStatus.approved, RequestStatus.declined):
        join_request.responded_at = datetime.now(timezone.utc)
    await db.flush()
    return join_request


async def lock_and_increment_participants(
    db: AsyncSession, activity_id: uuid.UUID
) -> Activity:
    """Lock the activity row and increment current_participants.

    Uses SELECT ... FOR UPDATE to prevent race conditions when multiple
    approvals happen concurrently.
    """
    result = await db.execute(
        select(Activity)
        .where(Activity.id == activity_id)
        .with_for_update()
    )
    activity = result.scalar_one()

    activity.current_participants += 1
    await db.flush()
    return activity


async def decrement_participants(
    db: AsyncSession, activity_id: uuid.UUID
) -> None:
    """Decrement participant count (used when cancelling an approved request)."""
    await db.execute(
        update(Activity)
        .where(Activity.id == activity_id)
        .values(current_participants=Activity.current_participants - 1)
    )
    await db.flush()
