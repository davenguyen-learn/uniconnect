"""Participation API endpoints."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.participation import service
from app.modules.participation.schemas import JoinRequestCreate, JoinRequestResponse

router = APIRouter(tags=["participation"])


@router.post(
    "/activities/{activity_id}/join",
    response_model=JoinRequestResponse,
    status_code=201,
)
async def request_to_join(
    activity_id: uuid.UUID,
    data: JoinRequestCreate | None = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a join request for an activity."""
    return await service.request_to_join(
        db, activity_id, current_user["sub"], data or JoinRequestCreate()
    )


@router.get(
    "/activities/{activity_id}/requests",
    response_model=list[JoinRequestResponse],
)
async def list_requests(
    activity_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List join requests for an activity."""
    return await service.list_requests(db, activity_id, current_user["sub"])


@router.get(
    "/activities/{activity_id}/participants",
    response_model=list[JoinRequestResponse],
)
async def list_participants(
    activity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List approved participants for an activity."""
    from sqlalchemy import select
    from sqlalchemy.orm import joinedload
    from app.modules.participation.models import JoinRequest, RequestStatus
    
    result = await db.execute(
        select(JoinRequest)
        .options(joinedload(JoinRequest.user))
        .where(
            JoinRequest.activity_id == activity_id,
            JoinRequest.status == RequestStatus.approved
        )
        .order_by(JoinRequest.created_at.asc())
    )
    requests = result.scalars().all()
    # Convert to response
    from app.modules.participation.service import _to_response
    return [_to_response(r) for r in requests]


@router.patch(
    "/join-requests/{request_id}/approve",
    response_model=JoinRequestResponse,
)
async def approve_request(
    request_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve a join request (host only)."""
    return await service.approve_request(db, request_id, current_user["sub"])


@router.patch(
    "/join-requests/{request_id}/decline",
    response_model=JoinRequestResponse,
)
async def decline_request(
    request_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Decline a join request (host only)."""
    return await service.decline_request(db, request_id, current_user["sub"])


@router.patch(
    "/join-requests/{request_id}/cancel",
    response_model=JoinRequestResponse,
)
async def cancel_request(
    request_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel own join request (requester only)."""
    return await service.cancel_request(db, request_id, current_user["sub"])


@router.post(
    "/activities/{activity_id}/leave",
    status_code=204,
)
async def leave_activity(
    activity_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Leave an approved activity."""
    await service.leave_activity(db, activity_id, current_user["sub"])
