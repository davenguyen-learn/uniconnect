"""Activity business logic."""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
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

    return ActivityResponse(
        id=activity.id,
        host_id=activity.host_id,
        group_id=getattr(activity, 'group_id', None),
        title=activity.title,
        description=activity.description,
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
        created_at=activity.created_at,
        host=host_info,
        group=group_info,
        distance_meters=distance,
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
        
    if data.group_id:
        from app.modules.groups.repository import get_group_by_id
        group = await get_group_by_id(db, data.group_id)
        if group and group.owner_id != uuid.UUID(user_id) and not group.allow_member_activities:
            raise ForbiddenError("Group members are not allowed to post activities.")

    activity = Activity(
        host_id=uuid.UUID(user_id),
        title=data.title,
        description=data.description,
        category=data.category,
        location=f"SRID=4326;POINT({data.longitude} {data.latitude})",
        location_name=data.location_name,
        start_time=data.start_time,
        end_time=data.end_time,
        max_participants=data.max_participants,
        privacy=data.privacy,
        require_approval=data.require_approval,
        group_id=data.group_id,
        current_participants=1,  # Host is counted
    )

    activity = await repository.create(db, activity)
    return _activity_to_response(activity, data.latitude, data.longitude)


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

    return _activity_to_response(activity, lat, lng)


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

    # Handle location update
    if "latitude" in update_data or "longitude" in update_data:
        coords = await repository.get_coordinates_from_db(db, activity_id)
        current_lat, current_lng = coords if coords else (0, 0)
        new_lat = update_data.pop("latitude", current_lat)
        new_lng = update_data.pop("longitude", current_lng)
        activity.location = f"SRID=4326;POINT({new_lng} {new_lat})"

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
) -> ActivityListResponse:
    from app.modules.users.models import UserFollow
    from sqlalchemy import select

    # Fetch followed user IDs to prioritize their activities
    followed_user_ids_result = await db.execute(
        select(UserFollow.following_id).where(UserFollow.follower_id == uuid.UUID(user_id))
    )
    followed_user_ids = list(followed_user_ids_result.scalars().all())

    activities, total = await repository.list_active(
        db, user_id=uuid.UUID(user_id), category=category, group_id=group_id,
        limit=limit, offset=offset, followed_user_ids=followed_user_ids
    )

    items = []
    for activity in activities:
        coords = await repository.get_coordinates_from_db(db, activity.id)
        lat, lng = coords if coords else (0, 0)
        lat, lng = obfuscate_coordinates(lat, lng)  # Always obfuscate in listings
        items.append(_activity_to_response(activity, lat, lng))

    return ActivityListResponse(
        items=items, total=total, limit=limit, offset=offset, has_more=(offset + limit < total)
    )


async def get_my_activities(
    db: AsyncSession, user_id: str, limit: int = 20, offset: int = 0
) -> ActivityListResponse:
    """List activities hosted by the current user."""
    activities, total = await repository.list_active(
        db, user_id=uuid.UUID(user_id), host_id=uuid.UUID(user_id), limit=limit, offset=offset
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
    db: AsyncSession, query: NearbyQuery, user_id: str | None = None
) -> ActivityListResponse:
    """Find activities within radius using PostGIS spatial query."""
    # Ensure user_id is provided, otherwise we can't filter group visibility
    if not user_id:
        raise ValidationError("user_id is required for discover_nearby")

    from app.modules.users.models import UserFollow
    from sqlalchemy import select

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
        limit=query.limit,
        offset=query.offset,
        followed_user_ids=followed_user_ids,
    )

    items = []
    for activity, distance in results:
        coords = await repository.get_coordinates_from_db(db, activity.id)
        lat, lng = coords if coords else (0, 0)

        # Obfuscate coordinates for non-hosts
        is_host = user_id and str(activity.host_id) == user_id
        if not is_host:
            lat, lng = obfuscate_coordinates(lat, lng)

        items.append(_activity_to_response(activity, lat, lng, distance=distance))

    return ActivityListResponse(
        items=items, total=total, limit=query.limit, offset=query.offset,
        has_more=(query.offset + query.limit < total),
    )


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
