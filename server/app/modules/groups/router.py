"""Group API endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query, status, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.groups import service as group_service
from app.modules.groups.schemas import (
    GroupCreate,
    GroupDetailResponse,
    GroupResponse,
    GroupUpdate,
    GroupStatsResponse,
    GroupMemberResponse,
    GroupJoinRequestResponse,
    JoinRequestActionRequest,
    CoHostInvitationResponse,
    CoHostActionRequest,
    CoHostInvitationCreate,
)

router = APIRouter(prefix="/groups", tags=["groups"])


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    data: GroupCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new group."""
    return await group_service.create_group(db, uuid.UUID(current_user["sub"]), data)


@router.patch("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: uuid.UUID,
    data: GroupUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update group settings (owner only)."""
    return await group_service.update_group(db, group_id, uuid.UUID(current_user["sub"]), data)


@router.get("/my", response_model=list[GroupResponse])
async def get_my_groups(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List groups the current user belongs to."""
    return await group_service.get_my_groups(db, uuid.UUID(current_user["sub"]))


@router.get("/discover", response_model=list[GroupResponse])
async def discover_groups(
    search: str | None = Query(default=None, description="Search term for name or description"),
    sort_by: str = Query(default="newest", pattern="^(newest|oldest|most_members)$"),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get groups the current user can join."""
    return await group_service.discover_groups(
        db, 
        uuid.UUID(current_user["sub"]),
        search=search,
        sort_by=sort_by,
        limit=limit
    )


@router.get("/{group_id}", response_model=GroupDetailResponse)
async def get_group(
    group_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get details of a specific group."""
    return await group_service.get_group(db, group_id, user_id=uuid.UUID(current_user["sub"]))


@router.post("/{group_id}/join", status_code=status.HTTP_204_NO_CONTENT)
async def join_group(
    group_id: uuid.UUID,
    payload: dict | None = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Join a group."""
    form_responses = payload.get("form_responses") if payload else None
    await group_service.join_group(db, group_id, uuid.UUID(current_user["sub"]), form_responses=form_responses)


@router.post("/{group_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_group(
    group_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Leave a group."""
    await group_service.leave_group(db, group_id, uuid.UUID(current_user["sub"]))


@router.get("/{group_id}/activities")
async def get_group_activities(
    group_id: uuid.UUID,
    category: str | None = Query(default=None),
    include_past: bool = Query(default=True),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List activities belonging to a specific group (lead host or co-host)."""
    from app.modules.groups.repository import get_group_by_id, is_member
    from app.modules.activities.service import list_activities

    user_id = uuid.UUID(current_user["sub"])

    group = await get_group_by_id(db, group_id)
    if not group:
        raise NotFoundError("Group not found.")

    group_privacy_val = group.privacy.value if hasattr(group.privacy, 'value') else group.privacy
    if group_privacy_val == "private" and not await is_member(db, group_id, user_id) and group.owner_id != user_id:
        return {"items": [], "total": 0, "has_more": False}

    return await list_activities(
        db, user_id=current_user["sub"], category=category, group_id=group_id,
        limit=limit, offset=offset, include_past=include_past,
    )


# ── Phase 8 Endpoints ──

@router.get("/{group_id}/stats", response_model=GroupStatsResponse)
async def get_group_stats(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Public stats for Club Showcase: 100% server-derived with deduplicated aggregates."""
    return await group_service.get_group_stats_service(db, group_id)


@router.get("/{group_id}/members", response_model=list[GroupMemberResponse])
async def list_group_members(
    group_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Paginated list of active group members."""
    return await group_service.get_group_members_service(db, group_id, limit=limit, offset=offset)


@router.get("/{group_id}/join-requests", response_model=list[GroupJoinRequestResponse])
async def list_join_requests(
    group_id: uuid.UUID,
    status: str = Query(default="pending", pattern="^(pending|approved|rejected)$"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Management only: List join requests for club owner/admin."""
    return await group_service.list_group_join_requests(
        db, group_id, uuid.UUID(current_user["sub"]), status=status, limit=limit, offset=offset
    )


@router.post("/{group_id}/join-requests/{request_id}/action", response_model=GroupJoinRequestResponse)
async def action_join_request_endpoint(
    group_id: uuid.UUID,
    request_id: uuid.UUID,
    data: JoinRequestActionRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """State machine transition: pending -> approved | rejected (owner/admin only)."""
    return await group_service.action_join_request(
        db, group_id, request_id, uuid.UUID(current_user["sub"]), data.action
    )


@router.get("/{group_id}/co-host-invitations", response_model=list[CoHostInvitationResponse])
async def list_cohost_invitations(
    group_id: uuid.UUID,
    status: str | None = Query(default=None, pattern="^(pending|accepted|declined)$"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Management only: BCN inbox for co-host invitations."""
    return await group_service.list_cohost_invitations(
        db, group_id, uuid.UUID(current_user["sub"]), status=status, limit=limit, offset=offset
    )


@router.post("/co-host-invitations/{invitation_id}/respond", response_model=CoHostInvitationResponse)
async def respond_cohost_invitation_endpoint(
    invitation_id: uuid.UUID,
    data: CoHostActionRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Atomic acceptance or decline with MAX_COHOSTS limit and transactional consistency."""
    return await group_service.respond_cohost_invitation(
        db, invitation_id, uuid.UUID(current_user["sub"]), data.action
    )


@router.post("/{group_id}/avatar", response_model=GroupDetailResponse)
async def upload_group_avatar(
    group_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload and set group avatar (owner or admin only)."""
    file_bytes = await file.read()
    return await group_service.update_group_avatar(
        db=db,
        group_id=group_id,
        user_id=uuid.UUID(current_user["sub"]),
        file_bytes=file_bytes,
        content_type=file.content_type,
    )


@router.delete("/{group_id}/avatar", response_model=GroupDetailResponse)
async def delete_group_avatar(
    group_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete group avatar (owner or admin only)."""
    return await group_service.delete_group_avatar(
        db=db,
        group_id=group_id,
        user_id=uuid.UUID(current_user["sub"]),
    )


