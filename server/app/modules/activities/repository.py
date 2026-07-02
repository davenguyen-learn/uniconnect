"""Activity repository — encapsulates PostGIS spatial queries."""

import uuid
from datetime import datetime, timezone

from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_MakePoint, ST_SetSRID, ST_X, ST_Y
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.activities.models import Activity


async def create(db: AsyncSession, activity: Activity) -> Activity:
    """Insert a new activity and return it with host populated."""
    db.add(activity)
    await db.flush()

    # Re-fetch with host relationship
    result = await db.execute(
        select(Activity)
        .options(joinedload(Activity.host))
        .where(Activity.id == activity.id)
    )
    return result.scalar_one()


async def get_by_id(db: AsyncSession, activity_id: uuid.UUID) -> Activity | None:
    """Fetch an activity by ID with host relationship."""
    result = await db.execute(
        select(Activity)
        .options(joinedload(Activity.host))
        .where(and_(Activity.id == activity_id, Activity.is_deleted == False))  # noqa: E712
    )
    return result.scalar_one_or_none()


async def update(db: AsyncSession, activity: Activity, data: dict) -> Activity:
    """Update activity fields from a dict of changes."""
    for field, value in data.items():
        if field in ("latitude", "longitude"):
            continue  # Handle location separately
        setattr(activity, field, value)

    # Handle location update if lat/lng provided
    if "latitude" in data and "longitude" in data:
        lat, lng = data["latitude"], data["longitude"]
        activity.location = f"SRID=4326;POINT({lng} {lat})"
    elif "latitude" in data or "longitude" in data:
        # Need both for a valid point — get existing values
        pass  # Handled by service layer validation

    await db.flush()
    return activity


async def soft_delete(db: AsyncSession, activity: Activity) -> None:
    """Mark an activity as deleted."""
    activity.is_deleted = True
    activity.deleted_at = datetime.now(timezone.utc)
    await db.flush()


async def list_active(
    db: AsyncSession,
    user_id: uuid.UUID,
    category: str | None = None,
    host_id: uuid.UUID | None = None,
    group_id: uuid.UUID | None = None,
    limit: int = 20,
    offset: int = 0,
    followed_user_ids: list[uuid.UUID] | None = None,
) -> tuple[list[Activity], int]:
    """List active (non-deleted, future) activities with pagination and access control."""
    from app.modules.groups.models import GroupMember

    now = datetime.now(timezone.utc)

    # Base access filter: Public activity OR user is in the group
    access_filter = or_(
        Activity.group_id.is_(None),
        Activity.group_id.in_(
            select(GroupMember.group_id).where(GroupMember.user_id == user_id)
        )
    )

    base_filter = and_(
        Activity.is_deleted == False,  # noqa: E712
        Activity.end_time > now,
        access_filter,
    )

    if category:
        base_filter = and_(base_filter, Activity.category == category)
    if host_id:
        base_filter = and_(base_filter, Activity.host_id == host_id)
    if group_id:
        base_filter = and_(base_filter, Activity.group_id == group_id)

    # Count
    count_q = select(func.count()).select_from(Activity).where(base_filter)
    total = (await db.execute(count_q)).scalar() or 0

    # Fetch
    order_clauses = []
    if followed_user_ids:
        # PostgreSQL specific: True sorts after False by default if using ASC, 
        # so using DESC puts followed users first.
        order_clauses.append(Activity.host_id.in_(followed_user_ids).desc())
    order_clauses.append(Activity.start_time.asc())

    query = (
        select(Activity)
        .options(joinedload(Activity.host))
        .where(base_filter)
        .order_by(*order_clauses)
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    activities = list(result.unique().scalars().all())

    return activities, total


async def find_within_radius(
    db: AsyncSession,
    user_id: uuid.UUID,
    lat: float,
    lng: float,
    radius_meters: int,
    category: str | None = None,
    search: str | None = None,
    free_to_join: bool | None = None,
    limit: int = 20,
    offset: int = 0,
    followed_user_ids: list[uuid.UUID] | None = None,
) -> tuple[list[tuple[Activity, float]], int]:
    """Find activities within a radius using PostGIS ST_DWithin and access control.

    Returns a list of (Activity, distance_meters) tuples and total count.
    """
    from app.modules.groups.models import GroupMember

    now = datetime.now(timezone.utc)
    point = ST_SetSRID(ST_MakePoint(lng, lat), 4326)

    # Base access filter: Public activity OR user is in the group
    access_filter = or_(
        Activity.group_id.is_(None),
        Activity.group_id.in_(
            select(GroupMember.group_id).where(GroupMember.user_id == user_id)
        )
    )

    base_filter = and_(
        Activity.is_deleted == False,  # noqa: E712
        Activity.end_time > now,
        Activity.location.isnot(None),
        ST_DWithin(Activity.location, point, radius_meters),
        access_filter,
    )

    if category:
        base_filter = and_(base_filter, Activity.category == category)
    if search:
        base_filter = and_(base_filter, or_(Activity.title.ilike(f"%{search}%"), Activity.description.ilike(f"%{search}%")))
    if free_to_join is True:
        base_filter = and_(base_filter, Activity.require_approval == False)

    # Count
    count_q = select(func.count()).select_from(Activity).where(base_filter)
    total = (await db.execute(count_q)).scalar() or 0

    # Fetch with distance
    distance_col = ST_Distance(Activity.location, point).label("distance_meters")
    
    order_clauses = []
    if followed_user_ids:
        order_clauses.append(Activity.host_id.in_(followed_user_ids).desc())
    order_clauses.append(distance_col.asc())

    query = (
        select(Activity, distance_col)
        .options(joinedload(Activity.host))
        .where(base_filter)
        .order_by(*order_clauses)
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    rows = result.unique().all()
    activities_with_distance = [(row[0], row[1]) for row in rows]

    return activities_with_distance, total


async def get_coordinates(activity: Activity) -> tuple[float, float] | None:
    """Extract lat/lng from a PostGIS geography point.

    Since we store as WKB, we need to use ST_X/ST_Y to extract.
    Returns None if location is not set.
    """
    if activity.location is None:
        return None

    # For activities loaded from DB, location is a WKBElement
    # We'll extract coordinates in the service layer using a query
    return None


async def get_coordinates_from_db(db: AsyncSession, activity_id: uuid.UUID) -> tuple[float, float] | None:
    """Query the DB to extract lat/lng from a PostGIS geography point."""
    from geoalchemy2.types import Geometry
    from sqlalchemy import cast
    result = await db.execute(
        select(
            ST_Y(cast(Activity.location, Geometry)).label("lat"),
            ST_X(cast(Activity.location, Geometry)).label("lng"),
        ).where(Activity.id == activity_id)
    )
    row = result.one_or_none()
    if row and row.lat is not None:
        return (row.lat, row.lng)
    return None

async def list_joined_activities(
    db: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Activity], int]:
    """List activities the user has joined (pending or approved)."""
    from app.modules.participation.models import JoinRequest, RequestStatus

    now = datetime.now(timezone.utc)

    # Base join filter: activity is not deleted, is in future, and user has an active request
    base_filter = and_(
        Activity.is_deleted == False,
        Activity.end_time > now,
        JoinRequest.user_id == user_id,
        JoinRequest.status.in_([RequestStatus.pending, RequestStatus.approved]),
    )

    # Count
    count_q = select(func.count()).select_from(Activity).join(JoinRequest).where(base_filter)
    total = (await db.execute(count_q)).scalar() or 0

    # Fetch
    query = (
        select(Activity)
        .join(JoinRequest)
        .options(joinedload(Activity.host))
        .where(base_filter)
        .order_by(Activity.start_time.asc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    activities = list(result.unique().scalars().all())

    return activities, total
