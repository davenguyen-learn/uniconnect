"""Activity API endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_optional_current_user
from app.modules.activities import service
from app.modules.activities.schemas import (
    ActivityCreate,
    ActivityListResponse,
    ActivityResponse,
    ActivityUpdate,
    NearbyQuery,
)
from app.modules.calendar.schemas import ReschedulePreviewRequest, ReschedulePreviewResponse

router = APIRouter(prefix="/activities", tags=["activities"])


@router.post("", response_model=ActivityResponse, status_code=201)
async def create_activity(
    data: ActivityCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new activity."""
    return await service.create_activity(db, current_user["sub"], data)


@router.get("/nearby", response_model=ActivityListResponse)
async def discover_nearby(
    lat: float = Query(ge=-90, le=90),
    lng: float = Query(ge=-180, le=180),
    radius: int = Query(default=5000, ge=100, le=50000),
    category: str | None = Query(default=None),
    search: str | None = Query(default=None),
    free_to_join: bool | None = Query(default=None),
    days_ahead: int | None = Query(default=None, ge=1, le=365),
    is_ctxh: bool | None = Query(default=None),
    has_trophy: bool | None = Query(default=None),
    sort_by: str = Query(default="distance"),
    exclude_my_activities: bool = Query(default=True),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    include_conflicts: bool = Query(default=False),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Discover activities within a radius of a geographic point."""
    query = NearbyQuery(
        lat=lat, lng=lng, radius=radius, category=category,
        search=search, free_to_join=free_to_join,
        days_ahead=days_ahead, is_ctxh=is_ctxh, has_trophy=has_trophy,
        sort_by=sort_by,
        exclude_my_activities=exclude_my_activities,
        limit=limit, offset=offset
    )
    return await service.discover_nearby(
        db, query, current_user["sub"], include_conflicts=include_conflicts
    )


@router.get("/joined", response_model=ActivityListResponse)
async def get_joined_activities(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List activities joined by the current user."""
    return await service.get_joined_activities(
        db, current_user["sub"], status_filter=status, limit=limit, offset=offset
    )


@router.get("/mine", response_model=ActivityListResponse)
async def get_my_activities(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List activities hosted by the current user."""
    return await service.get_my_activities(
        db, current_user["sub"], status_filter=status, limit=limit, offset=offset
    )


@router.get("", response_model=ActivityListResponse)
async def list_activities(
    category: str | None = Query(default=None),
    search: str | None = Query(default=None),
    group_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    include_conflicts: bool = Query(default=False),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active activities with optional filtering."""
    return await service.list_activities(
        db, user_id=current_user["sub"], category=category, search=search, group_id=group_id,
        limit=limit, offset=offset, include_conflicts=include_conflicts
    )


@router.post("/{activity_id}/preview-reschedule", response_model=ReschedulePreviewResponse)
async def preview_reschedule(
    activity_id: uuid.UUID,
    data: ReschedulePreviewRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Host preview of participant availability when rescheduling."""
    return await service.preview_reschedule(
        db, activity_id, current_user["sub"], data.new_start_time, data.new_end_time
    )


@router.get("/{activity_id}", response_model=ActivityResponse)
async def get_activity(
    activity_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single activity by ID."""
    return await service.get_activity(db, activity_id, current_user["sub"])


@router.patch("/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: uuid.UUID,
    data: ActivityUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an activity (host only)."""
    return await service.update_activity(db, activity_id, current_user["sub"], data)


@router.delete("/{activity_id}", status_code=204)
async def delete_activity(
    activity_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete an activity (host or admin)."""
    await service.delete_activity(
        db, activity_id, current_user["sub"], current_user.get("role", "student")
    )


@router.get("/{activity_id}/cohost-candidates")
async def get_cohost_candidates_endpoint(
    activity_id: uuid.UUID,
    search: str | None = Query(default=None, description="Search term for name or description"),
    limit: int = Query(default=20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Search candidate groups to invite as co-hosts for this activity:
    - Excludes lead host group and already accepted co-hosts
    - Public groups: can be invited by anyone
    - Private groups: can only be invited if current user is a member/admin
    """
    from app.modules.groups import service as group_service
    return await group_service.search_cohost_candidates(
        db,
        activity_id=activity_id,
        user_id=uuid.UUID(current_user["sub"]),
        search=search,
        limit=limit,
    )


@router.post("/{activity_id}/invite-cohost", status_code=status.HTTP_201_CREATED)
async def invite_cohost_endpoint(
    activity_id: uuid.UUID,
    data: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lead host invites a group to be co-host of this activity."""
    from app.modules.groups import service as group_service
    from app.modules.groups.schemas import CoHostInvitationCreate
    payload = CoHostInvitationCreate(**data)
    return await group_service.invite_cohost(
        db, activity_id, uuid.UUID(current_user["sub"]), payload
    )


@router.post("/{activity_id}/finalize-attendance", status_code=status.HTTP_200_OK)
async def finalize_attendance_endpoint(
    activity_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Finalize attendance for activity and trigger TrophyGrantRequest eligibility if trophy attached."""
    from app.modules.participation import service as part_service
    return await part_service.finalize_activity_attendance(
        db,
        activity_id,
        current_user["sub"],
        current_user.get("role", "student"),
    )


@router.get("/{activity_id}/participants/export")
async def export_activity_participants_endpoint(
    activity_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Stream activity participants and dynamic form responses as UTF-8 BOM CSV.
    Strictly authorized: Lead Host, Lead Group Owner/Admin, System Admin.
    """
    from datetime import datetime
    from fastapi.responses import StreamingResponse
    from app.modules.activities import repository as act_repo
    from app.modules.activities.export_service import stream_activity_participants_csv, format_slug

    act = await act_repo.get_by_id(db, activity_id)
    title_slug = format_slug(act.title) if act and act.title else str(activity_id)[:8]
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"danh_sach_tham_gia_{title_slug}_{date_str}.csv"

    return StreamingResponse(
        stream_activity_participants_csv(
            db=db,
            activity_id=activity_id,
            user_id=uuid.UUID(current_user["sub"]),
            user_role=current_user.get("role", "student"),
        ),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

