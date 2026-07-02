"""Participation business logic."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    CapacityFullError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.modules.activities import repository as activity_repo
from app.modules.participation import repository as participation_repo
from app.modules.participation.models import JoinRequest, RequestStatus
from app.modules.participation.schemas import JoinRequestCreate, JoinRequestResponse, UserInfo


def _to_response(jr: JoinRequest) -> JoinRequestResponse:
    user_info = None
    if jr.user:
        user_info = UserInfo(username=jr.user.username, full_name=jr.user.full_name)
    return JoinRequestResponse(
        id=jr.id,
        activity_id=jr.activity_id,
        user_id=jr.user_id,
        status=jr.status.value if hasattr(jr.status, 'value') else jr.status,
        message=jr.message,
        responded_at=jr.responded_at,
        created_at=jr.created_at,
        user=user_info,
    )


async def request_to_join(
    db: AsyncSession, activity_id: uuid.UUID, user_id: str, data: JoinRequestCreate
) -> JoinRequestResponse:
    """Submit a join request for an activity."""
    uid = uuid.UUID(user_id)

    # Verify activity exists and is active
    activity = await activity_repo.get_by_id(db, activity_id)
    if not activity:
        raise NotFoundError("Activity not found.")

    # Host cannot join their own activity
    if str(activity.host_id) == user_id:
        raise ValidationError("You cannot join your own activity.")

    # Check capacity
    if activity.current_participants >= activity.max_participants:
        raise CapacityFullError()

    # Check for duplicate active request
    existing = await participation_repo.get_active_request(db, activity_id, uid)
    if existing:
        raise ConflictError("You already have an active request for this activity.")

    join_request = JoinRequest(
        activity_id=activity_id,
        user_id=uid,
        message=data.message if data else None,
        status=RequestStatus.pending if activity.require_approval else RequestStatus.approved,
    )
    
    if not activity.require_approval:
        # Lock activity row and check capacity safely
        locked_activity = await participation_repo.lock_and_increment_participants(db, activity_id)
        if locked_activity.current_participants > locked_activity.max_participants:
            raise CapacityFullError()
            
    join_request = await participation_repo.create(db, join_request)
    return _to_response(join_request)


async def approve_request(
    db: AsyncSession, request_id: uuid.UUID, user_id: str
) -> JoinRequestResponse:
    """Approve a join request (host only). Uses row locking for concurrency safety."""
    jr = await participation_repo.get_by_id(db, request_id)
    if not jr:
        raise NotFoundError("Join request not found.")

    if str(jr.activity.host_id) != user_id:
        raise ForbiddenError("Only the host can approve requests.")

    if jr.status != RequestStatus.pending:
        raise ValidationError(f"Cannot approve a request with status '{jr.status.value}'.")

    # Lock activity row and check capacity
    activity = await participation_repo.lock_and_increment_participants(db, jr.activity_id)
    if activity.current_participants > activity.max_participants:
        # Rollback the increment — this will be rolled back by the session
        raise CapacityFullError()

    jr = await participation_repo.update_status(db, jr, RequestStatus.approved)
    return _to_response(jr)


async def decline_request(
    db: AsyncSession, request_id: uuid.UUID, user_id: str
) -> JoinRequestResponse:
    """Decline a join request (host only)."""
    jr = await participation_repo.get_by_id(db, request_id)
    if not jr:
        raise NotFoundError("Join request not found.")

    if str(jr.activity.host_id) != user_id:
        raise ForbiddenError("Only the host can decline requests.")

    if jr.status != RequestStatus.pending:
        raise ValidationError(f"Cannot decline a request with status '{jr.status.value}'.")

    jr = await participation_repo.update_status(db, jr, RequestStatus.declined)
    return _to_response(jr)


async def cancel_request(
    db: AsyncSession, request_id: uuid.UUID, user_id: str
) -> JoinRequestResponse:
    """Cancel own join request (requester only)."""
    jr = await participation_repo.get_by_id(db, request_id)
    if not jr:
        raise NotFoundError("Join request not found.")

    if str(jr.user_id) != user_id:
        raise ForbiddenError("Only the requester can cancel the request.")

    if jr.status != RequestStatus.pending:
        raise ValidationError(f"Cannot cancel a request with status '{jr.status.value}'.")

    jr = await participation_repo.update_status(db, jr, RequestStatus.cancelled)
    return _to_response(jr)


async def leave_activity(
    db: AsyncSession, activity_id: uuid.UUID, user_id: str
) -> None:
    """Leave an approved activity."""
    uid = uuid.UUID(user_id)
    jr = await participation_repo.get_active_request(db, activity_id, uid)
    if not jr or jr.status != RequestStatus.approved:
        raise ValidationError("You have not joined this activity.")

    # Lock activity to safely decrement
    act = await activity_repo.get_by_id(db, activity_id)
    if not act:
        raise NotFoundError("Activity not found.")

    # Decrement participant count safely
    await participation_repo.decrement_participants(db, activity_id)
    
    jr = await participation_repo.update_status(db, jr, RequestStatus.cancelled)
    
    return None


async def list_requests(
    db: AsyncSession, activity_id: uuid.UUID, user_id: str
) -> list[JoinRequestResponse]:
    """List join requests. Host sees all, others see only their own."""
    activity = await activity_repo.get_by_id(db, activity_id)
    if not activity:
        raise NotFoundError("Activity not found.")

    is_host = str(activity.host_id) == user_id
    if is_host:
        requests = await participation_repo.list_by_activity(db, activity_id)
    else:
        requests = await participation_repo.list_by_user(db, activity_id, uuid.UUID(user_id))

    return [_to_response(jr) for jr in requests]
