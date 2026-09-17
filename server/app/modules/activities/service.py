"""Activity business logic."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.modules.activities import repository
from app.modules.activities.constants import TEMPORAL_LOCK_MINUTES
from app.modules.activities.models import Activity
from app.modules.activities.schemas import (
    ActivityCreate,
    ActivityListResponse,
    ActivityResponse,
    ActivityUpdate,
    HostInfo,
    NearbyQuery,
)
from app.modules.activities.spatial import obfuscate_coordinates


def _activity_to_response(
    activity: Activity,
    lat: float,
    lng: float,
    distance: float | None = None,
    private_description: str | None = None,
    conflict_info: Any | None = None,
) -> ActivityResponse:
    """Convert an Activity model to a response schema."""
    host_info = None
    if activity.host:
        host_info = HostInfo(
            username=activity.host.username,
            full_name=activity.host.full_name,
        )

    group_info = None
    if getattr(activity, 'group', None):
        from app.modules.activities.schemas import GroupInfo
        group_info = GroupInfo(
            id=activity.group.id,
            name=activity.group.name,
        )

    custom_form_info = None
    if getattr(activity, 'custom_form', None):
        # We need to construct CustomFormResponse from Activity.custom_form
        custom_form_info = activity.custom_form
        # Due to from_attributes=True, pydantic handles the parsing automatically

    trophy_info = None
    if getattr(activity, 'trophy', None):
        trophy_info = activity.trophy

    return ActivityResponse(
        id=activity.id,
        host_id=activity.host_id,
        group_id=getattr(activity, 'group_id', None),
        title=activity.title,
        description=activity.description,
        private_description=private_description,
        category=activity.category,
        latitude=lat,
        longitude=lng,
        location_name=activity.location_name,
        start_time=activity.start_time,
        end_time=activity.end_time,
        max_participants=activity.max_participants,
        current_participants=activity.current_participants,
        privacy=activity.privacy.value if hasattr(activity.privacy, 'value') else activity.privacy,
        require_approval=activity.require_approval,
        social_work_days=activity.social_work_days,
        created_at=activity.created_at,
        host=host_info,
        group=group_info,
        distance_meters=distance,
        custom_form=custom_form_info,
        trophy=trophy_info,
        conflict_info=conflict_info,
        attendance_mode=getattr(activity, 'attendance_mode', 'manual') or 'manual',
        check_in_radius=getattr(activity, 'check_in_radius', 300) or 300,
    )


async def create_activity(
    db: AsyncSession, user_id: str, data: ActivityCreate
) -> ActivityResponse:
    """Create a new activity."""
    now = datetime.now(timezone.utc)

    if data.start_time.tzinfo is None:
        data.start_time = data.start_time.replace(tzinfo=timezone.utc)
    if data.end_time.tzinfo is None:
        data.end_time = data.end_time.replace(tzinfo=timezone.utc)

    if data.start_time <= now:
        raise ValidationError("Start time must be in the future.")

    # Check host conflict
    from app.modules.calendar.service import get_detector_for_user
    detector = await get_detector_for_user(db, uuid.UUID(user_id))
    host_conflict = detector.check_conflict(data.start_time, data.end_time)
    if host_conflict.has_conflict and host_conflict.conflicting_with and host_conflict.conflicting_with.type == "hosted_activity":
        raise ConflictError(f"Bạn đang là Host của hoạt động '{host_conflict.conflicting_with.title}' trong cùng khung giờ.")
        
    if data.group_id:
        from app.modules.groups.repository import get_group_by_id
        group = await get_group_by_id(db, data.group_id)
        if group and group.owner_id != uuid.UUID(user_id) and not group.allow_member_activities:
            raise ForbiddenError("Group members are not allowed to post activities.")

    embedding_text = f"{data.title}\n{data.description or ''}"
    from app.modules.chat.embeddings import generate_embedding
    
    from app.modules.users.models import User, UserRole
    from sqlalchemy import select
    user_result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user_obj = user_result.scalar_one_or_none()
    
    if not user_obj or user_obj.role not in [UserRole.admin, UserRole.edu_org]:
        data.social_work_days = None

    if data.trophy_id:
        if not user_obj or (user_obj.role not in [UserRole.admin, UserRole.edu_org] and not user_obj.is_verified):
            raise ForbiddenError("Chỉ các tổ chức hoặc tài khoản đã xác minh mới có thể gắn Trophy cho hoạt động.")

    import secrets
    check_in_code = secrets.token_hex(4).upper()

    activity = Activity(
        host_id=uuid.UUID(user_id),
        title=data.title,
        description=data.description,
        private_description=data.private_description,
        category=data.category,
        location=f"SRID=4326;POINT({data.longitude} {data.latitude})",
        location_name=data.location_name,
        start_time=data.start_time,
        end_time=data.end_time,
        max_participants=data.max_participants,
        privacy=data.privacy,
        require_approval=data.require_approval,
        social_work_days=data.social_work_days,
        group_id=data.group_id,
        trophy_id=data.trophy_id,
        attendance_mode=data.attendance_mode or "manual",
        check_in_radius=data.check_in_radius or 300,
        check_in_code=check_in_code,
        current_participants=1,  # Host is counted
        embedding=generate_embedding(embedding_text),
    )
    
    if data.custom_form:
        from app.modules.forms.models import CustomForm, FormField, FieldType
        form_fields = []
        for f in data.custom_form.fields:
            form_fields.append(FormField(
                label=f.label,
                field_type=f.field_type,
                is_required=f.is_required,
                order=f.order,
                meta_data=f.meta_data,
            ))
        activity.custom_form = CustomForm(
            title=data.custom_form.title,
            description=data.custom_form.description,
            fields=form_fields,
        )

    activity = await repository.create(db, activity)
    return _activity_to_response(activity, data.latitude, data.longitude, private_description=data.private_description)


async def get_activity(
    db: AsyncSession, activity_id: uuid.UUID, user_id: str | None = None
) -> ActivityResponse:
    """Get a single activity. Obfuscates coordinates for non-participants."""
    activity = await repository.get_by_id(db, activity_id)
    if not activity:
        raise NotFoundError("Activity not found.")

    if activity.group_id and user_id:
        from app.modules.groups.repository import is_member
        member = await is_member(db, activity.group_id, uuid.UUID(user_id))
        if not member and not (str(activity.host_id) == user_id):
            raise ForbiddenError("This activity is restricted to group members.")

    coords = await repository.get_coordinates_from_db(db, activity_id)
    if not coords:
        lat, lng = 0.0, 0.0
    else:
        lat, lng = coords

    # Obfuscate for non-host users
    is_host = user_id and str(activity.host_id) == user_id
    if not is_host:
        lat, lng = obfuscate_coordinates(lat, lng)

    # Only reveal private_description to host or approved participants
    revealed_private_desc = None
    if is_host:
        revealed_private_desc = activity.private_description
    elif user_id:
        from app.modules.participation.models import JoinRequest, RequestStatus
        from sqlalchemy import select, and_
        result = await db.execute(
            select(JoinRequest).where(and_(
                JoinRequest.activity_id == activity_id,
                JoinRequest.user_id == uuid.UUID(user_id),
                JoinRequest.status == RequestStatus.approved,
            ))
        )
        if result.unique().scalar_one_or_none():
            revealed_private_desc = activity.private_description

    return _activity_to_response(activity, lat, lng, private_description=revealed_private_desc)


async def update_activity(
    db: AsyncSession, activity_id: uuid.UUID, user_id: str, data: ActivityUpdate
) -> ActivityResponse:
    """Update an activity. Host-only, subject to temporal lock."""
    activity = await repository.get_by_id(db, activity_id)
    if not activity:
        raise NotFoundError("Activity not found.")

    if str(activity.host_id) != user_id:
        raise ForbiddenError("Only the host can edit this activity.")

    # Temporal lock: cannot modify within 30 min of start
    now = datetime.now(timezone.utc)
    lock_threshold = activity.start_time - timedelta(minutes=TEMPORAL_LOCK_MINUTES)
    if hasattr(lock_threshold, 'tzinfo') and lock_threshold.tzinfo is None:
        lock_threshold = lock_threshold.replace(tzinfo=timezone.utc)
    if now >= lock_threshold:
        raise ValidationError(
            f"Cannot modify activity within {TEMPORAL_LOCK_MINUTES} minutes of start time."
        )

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise ValidationError("No fields to update.")

    if "social_work_days" in update_data:
        from app.modules.users.models import User, UserRole
        from sqlalchemy import select
        user_result = await db.execute(select(User.role).where(User.id == uuid.UUID(user_id)))
        user_role = user_result.scalar_one_or_none()
        if user_role not in [UserRole.admin, UserRole.edu_org]:
            update_data.pop("social_work_days")

    if "trophy_id" in update_data and update_data["trophy_id"]:
        from app.modules.users.models import User, UserRole
        from sqlalchemy import select
        user_result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user_obj = user_result.scalar_one_or_none()
        if not user_obj or (user_obj.role not in [UserRole.admin, UserRole.edu_org] and not user_obj.is_verified):
            raise ForbiddenError("Chỉ các tổ chức hoặc tài khoản đã xác minh mới có thể gắn Trophy cho hoạt động.")

    if not activity.check_in_code:
        import secrets
        activity.check_in_code = secrets.token_hex(4).upper()

    # Handle location update
    if "latitude" in update_data or "longitude" in update_data:
        coords = await repository.get_coordinates_from_db(db, activity_id)
        current_lat, current_lng = coords if coords else (0, 0)
        new_lat = update_data.pop("latitude", current_lat)
        new_lng = update_data.pop("longitude", current_lng)
        activity.location = f"SRID=4326;POINT({new_lng} {new_lat})"

    if "title" in update_data or "description" in update_data:
        new_title = update_data.get("title", activity.title)
        new_desc = update_data.get("description", activity.description)
        embedding_text = f"{new_title}\n{new_desc or ''}"
        from app.modules.chat.embeddings import generate_embedding
        update_data["embedding"] = generate_embedding(embedding_text)

    activity = await repository.update(db, activity, update_data)

    coords = await repository.get_coordinates_from_db(db, activity_id)
    lat, lng = coords if coords else (0, 0)
    return _activity_to_response(activity, lat, lng)


async def delete_activity(
    db: AsyncSession, activity_id: uuid.UUID, user_id: str
) -> None:
    """Soft delete an activity. Host-only."""
    activity = await repository.get_by_id(db, activity_id)
    if not activity:
        raise NotFoundError("Activity not found.")

    if str(activity.host_id) != user_id:
        raise ForbiddenError("Only the host can delete this activity.")

    await repository.soft_delete(db, activity)


async def list_activities(
    db: AsyncSession,
    user_id: str,
    category: str | None = None,
    group_id: uuid.UUID | None = None,
    limit: int = 20,
    offset: int = 0,
    include_conflicts: bool = False,
) -> ActivityListResponse:
    from app.modules.users.models import UserFollow
    from sqlalchemy import select
    from app.modules.calendar.service import get_detector_for_user

    # Fetch followed user IDs to prioritize their activities
    followed_user_ids_result = await db.execute(
        select(UserFollow.following_id).where(UserFollow.follower_id == uuid.UUID(user_id))
    )
    followed_user_ids = list(followed_user_ids_result.scalars().all())

    activities, total = await repository.list_active(
        db, user_id=uuid.UUID(user_id), category=category, group_id=group_id,
        limit=limit, offset=offset, followed_user_ids=followed_user_ids
    )

    detector = None
    if user_id:
        try:
            detector = await get_detector_for_user(db, uuid.UUID(user_id))
        except Exception:
            detector = None

    items = []
    for activity in activities:
        conflict = detector.check_conflict(activity.start_time, activity.end_time) if detector else None
        if not include_conflicts and conflict and conflict.has_conflict and conflict.level == "hard_conflict":
            continue

        coords = await repository.get_coordinates_from_db(db, activity.id)
        lat, lng = coords if coords else (0, 0)
        lat, lng = obfuscate_coordinates(lat, lng)  # Always obfuscate in listings
        items.append(_activity_to_response(activity, lat, lng, conflict_info=conflict))

    return ActivityListResponse(
        items=items, total=total, limit=limit, offset=offset, has_more=(offset + limit < total)
    )


async def get_my_activities(
    db: AsyncSession, user_id: str, limit: int = 50, offset: int = 0
) -> ActivityListResponse:
    """List activities hosted by the current user (all past & upcoming)."""
    activities, total = await repository.list_hosted_activities(
        db, user_id=uuid.UUID(user_id), limit=limit, offset=offset
    )

    items = []
    for activity in activities:
        coords = await repository.get_coordinates_from_db(db, activity.id)
        lat, lng = coords if coords else (0, 0)
        items.append(_activity_to_response(activity, lat, lng))

    return ActivityListResponse(
        items=items, total=total, limit=limit, offset=offset, has_more=(offset + limit < total)
    )


async def discover_nearby(
    db: AsyncSession, query: NearbyQuery, user_id: str | None = None, include_conflicts: bool = False
) -> ActivityListResponse:
    """Find activities within radius using PostGIS spatial query."""
    # Ensure user_id is provided, otherwise we can't filter group visibility
    if not user_id:
        raise ValidationError("user_id is required for discover_nearby")

    from app.modules.users.models import UserFollow
    from sqlalchemy import select
    from app.modules.calendar.service import get_detector_for_user

    # Fetch followed user IDs to prioritize their activities
    followed_user_ids_result = await db.execute(
        select(UserFollow.following_id).where(UserFollow.follower_id == uuid.UUID(user_id))
    )
    followed_user_ids = list(followed_user_ids_result.scalars().all())

    results, total = await repository.find_within_radius(
        db,
        user_id=uuid.UUID(user_id),
        lat=query.lat,
        lng=query.lng,
        radius_meters=query.radius,
        category=query.category,
        search=query.search,
        free_to_join=query.free_to_join,
        days_ahead=query.days_ahead,
        limit=query.limit,
        offset=query.offset,
        followed_user_ids=followed_user_ids,
    )

    detector = None
    if user_id:
        try:
            detector = await get_detector_for_user(db, uuid.UUID(user_id))
        except Exception:
            detector = None

    items = []
    for activity, distance in results:
        conflict = detector.check_conflict(activity.start_time, activity.end_time) if detector else None
        if not include_conflicts and conflict and conflict.has_conflict and conflict.level == "hard_conflict":
            continue

        coords = await repository.get_coordinates_from_db(db, activity.id)
        lat, lng = coords if coords else (0, 0)

        # Obfuscate coordinates for non-hosts
        is_host = user_id and str(activity.host_id) == user_id
        if not is_host:
            lat, lng = obfuscate_coordinates(lat, lng)

        items.append(_activity_to_response(activity, lat, lng, distance=distance, conflict_info=conflict))

    return ActivityListResponse(
        items=items, total=total, limit=query.limit, offset=query.offset,
        has_more=(query.offset + query.limit < total),
    )


async def preview_reschedule(
    db: AsyncSession,
    activity_id: uuid.UUID,
    user_id: str,
    new_start_time: datetime,
    new_end_time: datetime,
):
    """Host previews how rescheduling will impact existing approved participants."""
    activity = await repository.get_by_id(db, activity_id)
    if not activity:
        raise NotFoundError("Activity not found.")
    if str(activity.host_id) != user_id:
        raise ForbiddenError("Only the host can preview rescheduling impact.")
    from app.modules.calendar.service import preview_reschedule_impact
    return await preview_reschedule_impact(db, activity_id, new_start_time, new_end_time)


async def get_joined_activities(
    db: AsyncSession, user_id: str, limit: int = 20, offset: int = 0
) -> ActivityListResponse:
    """List activities joined by the current user."""
    activities, total = await repository.list_joined_activities(
        db, user_id=uuid.UUID(user_id), limit=limit, offset=offset
    )

    items = []
    for activity in activities:
        coords = await repository.get_coordinates_from_db(db, activity.id)
        lat, lng = coords if coords else (0, 0)
        items.append(_activity_to_response(activity, lat, lng))

    return ActivityListResponse(
        items=items, total=total, limit=limit, offset=offset, has_more=(offset + limit < total)
    )
