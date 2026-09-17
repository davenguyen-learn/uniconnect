"""Participation API endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.participation import service
from app.modules.participation.schemas import (
    AttendanceUpdateRequest,
    CertificateResponse,
    CheckInCodeResponse,
    CheckInRequest,
    CheckInResponse,
    JoinRequestCreate,
    JoinRequestResponse,
)

router = APIRouter(tags=["participation"])


@router.post(
    "/activities/{activity_id}/join",
    response_model=JoinRequestResponse,
    status_code=201,
)
async def request_to_join(
    activity_id: uuid.UUID,
    data: JoinRequestCreate | None = None,
    confirm_swap: bool = Query(default=False),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a join request for an activity. Supports smart swap if confirm_swap is true."""
    return await service.request_to_join(
        db, activity_id, current_user["sub"], data or JoinRequestCreate(), confirm_swap=confirm_swap
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
    """List approved participants for an activity (auto-checks attendance if mode=auto)."""
    return await service.list_participants(db, activity_id)


@router.get(
    "/activities/{activity_id}/check-in-code",
    response_model=CheckInCodeResponse,
)
async def get_check_in_code(
    activity_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get check-in code and dynamic rotating token (host only)."""
    return await service.get_check_in_code(db, activity_id, current_user["sub"])


@router.post(
    "/activities/{activity_id}/check-in",
    response_model=CheckInResponse,
)
async def check_in_participant(
    activity_id: uuid.UUID,
    data: CheckInRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check-in to activity using QR or code with Geofencing verification."""
    return await service.check_in_participant(
        db, activity_id, current_user["sub"], data.code, data.latitude, data.longitude, data.accuracy
    )


@router.patch(
    "/activities/{activity_id}/participants/{user_id}/attendance",
)
async def update_participant_attendance(
    activity_id: uuid.UUID,
    user_id: uuid.UUID,
    data: AttendanceUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle or update participant attendance status (host only)."""
    return await service.update_participant_attendance(
        db, activity_id, user_id, current_user["sub"], data.attended
    )


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


@router.get(
    "/activities/{activity_id}/certificate",
    response_model=CertificateResponse,
)
async def get_certificate(
    activity_id: uuid.UUID,
    user_id: uuid.UUID | None = Query(default=None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get participation certificate data (requires attendance confirmed)."""
    return await service.get_certificate_data(
        db, activity_id, current_user["sub"], target_user_id=user_id
    )


@router.get(
    "/certificates/verify/{certificate_code}",
    response_model=CertificateResponse,
)
async def verify_certificate(
    certificate_code: str,
    db: AsyncSession = Depends(get_db),
):
    """Public verification of a certificate by its code."""
    return await service.verify_certificate_code(db, certificate_code)
