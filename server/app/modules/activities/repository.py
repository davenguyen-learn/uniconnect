"""Activity repository — encapsulates PostGIS spatial queries."""

import uuid
from datetime import datetime, timezone

from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_MakePoint, ST_SetSRID, ST_X, ST_Y
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.activities.models import Activity, ActivityPrivacy


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
    return result.unique().scalar_one()


async def get_by_id(db: AsyncSession, activity_id: uuid.UUID) -> Activity | None:
    """Fetch an activity by ID with host relationship."""
    result = await db.execute(
        select(Activity)
        .options(joinedload(Activity.host))
        .where(and_(Activity.id == activity_id, Activity.is_deleted == False))  # noqa: E712
    )
    return result.unique().scalar_one_or_none()


# Alias for backward-compatibility
get_activity_by_id = get_by_id


async def update(db: AsyncSession, activity: Activity, data: dict) -> Activity:
    """Update activity fields from a dict of changes."""
    for field, value in data.items():
        if field in ("latitude", "longitude"):
            continue  # Handle location separately
        setattr(activity, field, value)

    # Handle location update if lat/lng provided
    if "latitude" in data and "longitude" in data:
        lat, lng = data["latitude"], data["longitude"]
        activity.marker_location = f"SRID=4326;POINT({lng} {lat})"
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
    search: str | None = None,
    host_id: uuid.UUID | None = None,
    group_id: uuid.UUID | None = None,
    limit: int = 20,
    offset: int = 0,
    followed_user_ids: list[uuid.UUID] | None = None,
    include_past: bool = False,
) -> tuple[list[Activity], int]:
    """List active (non-deleted) activities with pagination, access control, and optional past events."""
    from app.modules.groups.models import ActivityCoHost, GroupMember

    now = datetime.now(timezone.utc)

    # Base access filter: Public activity OR activity not in a group OR user is in host group OR user is in co-host group
    if user_id:
        access_filter = or_(
            Activity.privacy == ActivityPrivacy.public,
            Activity.group_id.is_(None),
            Activity.group_id.in_(
                select(GroupMember.group_id).where(GroupMember.user_id == user_id)
            ),
            Activity.id.in_(
                select(ActivityCoHost.activity_id).where(
                    ActivityCoHost.group_id.in_(
                        select(GroupMember.group_id).where(GroupMember.user_id == user_id)
                    )
                )
            ),
        )
    else:
        access_filter = or_(
            Activity.privacy == ActivityPrivacy.public,
            Activity.group_id.is_(None),
        )

    time_filter = Activity.end_time > now if not include_past else True
    base_filter = and_(
        Activity.is_deleted == False,  # noqa: E712
        time_filter,
        access_filter,
    )

    if search:
        search_pattern = f"%{search}%"
        base_filter = and_(
            base_filter,
            or_(
                Activity.title.ilike(search_pattern),
                Activity.description.ilike(search_pattern),
                Activity.location_name.ilike(search_pattern),
                Activity.meeting_location.ilike(search_pattern),
            ),
        )

    if category:
        base_filter = and_(base_filter, Activity.category == category)
    if host_id:
        base_filter = and_(base_filter, Activity.host_id == host_id)
    if group_id:
        base_filter = and_(
            base_filter,
            or_(
                Activity.group_id == group_id,
                Activity.id.in_(
                    select(ActivityCoHost.activity_id).where(
                        ActivityCoHost.group_id == group_id
                    )
                ),
            ),
        )

    # Count
    count_q = select(func.count()).select_from(Activity).where(base_filter)
    total = (await db.execute(count_q)).scalar() or 0

    # Fetch
    order_clauses = []
    if followed_user_ids:
        # PostgreSQL specific: True sorts after False by default if using ASC, 
        # so using DESC puts followed users first.
        order_clauses.append(Activity.host_id.in_(followed_user_ids).desc())
    if include_past:
        order_clauses.append(Activity.start_time.desc())
    else:
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
    days_ahead: int | None = None,
    is_ctxh: bool | None = None,
    has_trophy: bool | None = None,
    sort_by: str | None = "distance",
    exclude_my_activities: bool = True,
    limit: int = 20,
    offset: int = 0,
    followed_user_ids: list[uuid.UUID] | None = None,
) -> tuple[list[tuple[Activity, float]], int]:
    """Find activities within a radius using PostGIS ST_DWithin and access control.

    Returns a list of (Activity, distance_meters) tuples and total count.
    """
    from app.modules.groups.models import ActivityCoHost, GroupMember
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    point = ST_SetSRID(ST_MakePoint(lng, lat), 4326)

    # Base access filter: Public activity OR activity not in a group OR user is in host group OR user is in co-host group
    if user_id:
        access_filter = or_(
            Activity.privacy == ActivityPrivacy.public,
            Activity.group_id.is_(None),
            Activity.group_id.in_(
                select(GroupMember.group_id).where(GroupMember.user_id == user_id)
            ),
            Activity.id.in_(
                select(ActivityCoHost.activity_id).where(
                    ActivityCoHost.group_id.in_(
                        select(GroupMember.group_id).where(GroupMember.user_id == user_id)
                    )
                )
            ),
        )
    else:
        access_filter = or_(
            Activity.privacy == ActivityPrivacy.public,
            Activity.group_id.is_(None),
        )

    base_filter = and_(
        Activity.is_deleted == False,  # noqa: E712
        Activity.end_time > now,
        Activity.marker_location.isnot(None),
        ST_DWithin(Activity.marker_location, point, radius_meters),
        access_filter,
    )

    if exclude_my_activities and user_id:
        base_filter = and_(base_filter, Activity.host_id != user_id)

    if category:
        category_synonyms: dict[str, list[str]] = {
            # Học tập & Workshop (tách thành 2 tag)
            "Study": ["Study", "Học tập", "Học thuật", "Học thuật & Kỹ năng", "Kỹ năng"],
            "Học tập": ["Study", "Học tập", "Học thuật", "Học thuật & Kỹ năng", "Kỹ năng"],
            "Workshop": ["Workshop", "Học thuật & Workshop", "Chuyên đề", "Tọa đàm", "Seminar"],
            # Ăn uống & Cà phê
            "Food": ["Food", "Ăn uống", "Ẩm thực", "Ăn uống & Cà phê"],
            "Ăn uống": ["Food", "Ăn uống", "Ẩm thực", "Ăn uống & Cà phê"],
            "Cafe": ["Cafe", "Cà phê", "Coffee", "Ăn uống & Cà phê"],
            "Cà phê": ["Cafe", "Cà phê", "Coffee", "Ăn uống & Cà phê"],
            # Thể thao & Vận động
            "Sports": ["Sports", "Thể thao", "Thể thao & Giải trí", "Thể thao & Vận động"],
            "Thể thao": ["Sports", "Thể thao", "Thể thao & Giải trí", "Thể thao & Vận động"],
            "Fitness": ["Fitness", "Vận động", "Thể thao & Vận động"],
            "Vận động": ["Fitness", "Vận động", "Thể thao & Vận động"],
            # Tình nguyện & CTXH
            "Volunteer": ["Volunteer", "Tình nguyện", "Tình nguyện & CTXH"],
            "Tình nguyện": ["Volunteer", "Tình nguyện", "Tình nguyện & CTXH"],
            "CTXH": ["CTXH", "Công tác xã hội", "Tình nguyện & CTXH"],
            # CLB & Đội nhóm
            "CLB": ["CLB", "Câu lạc bộ", "CLB & Đội nhóm"],
            "Team": ["Team", "Đội nhóm", "CLB & Đội nhóm"],
            "Đội nhóm": ["Team", "Đội nhóm", "CLB & Đội nhóm"],
            # Hướng nghiệp & Việc làm
            "Career": ["Career", "Hướng nghiệp", "Hướng nghiệp & Việc làm"],
            "Hướng nghiệp": ["Career", "Hướng nghiệp", "Hướng nghiệp & Việc làm"],
            "Job": ["Job", "Việc làm", "Tuyển dụng", "Hướng nghiệp & Việc làm"],
            "Việc làm": ["Job", "Việc làm", "Tuyển dụng", "Hướng nghiệp & Việc làm"],
            # Xem phim & Giải trí
            "Movie": ["Movie", "Xem phim", "Phim ảnh", "Xem phim & Giải trí"],
            "Xem phim": ["Movie", "Xem phim", "Phim ảnh", "Xem phim & Giải trí"],
            "Entertainment": ["Entertainment", "Giải trí", "Xem phim & Giải trí", "Thể thao & Giải trí"],
            "Giải trí": ["Entertainment", "Giải trí", "Xem phim & Giải trí", "Thể thao & Giải trí"],
            # Âm nhạc & Nghệ thuật
            "Music": ["Music", "Âm nhạc", "Nhạc", "Âm nhạc & Nghệ thuật"],
            "Âm nhạc": ["Music", "Âm nhạc", "Nhạc", "Âm nhạc & Nghệ thuật"],
            "Art": ["Art", "Nghệ thuật", "Hội họa", "Âm nhạc & Nghệ thuật"],
            "Nghệ thuật": ["Art", "Nghệ thuật", "Hội họa", "Âm nhạc & Nghệ thuật"],
            # Game & Esports
            "Gaming": ["Gaming", "Game", "Trò chơi điện tử", "Game & Esports"],
            "Game": ["Gaming", "Game", "Trò chơi điện tử", "Game & Esports"],
            "Esports": ["Esports", "Thể thao điện tử", "Game & Esports"],
            # Dã ngoại & Phượt
            "Travel": ["Travel", "Dã ngoại", "Du lịch", "Dã ngoại & Phượt"],
            "Dã ngoại": ["Travel", "Dã ngoại", "Du lịch", "Dã ngoại & Phượt"],
            "Backpacking": ["Backpacking", "Phượt", "Dã ngoại & Phượt"],
            "Phượt": ["Backpacking", "Phượt", "Dã ngoại & Phượt"],
            # Boardgame & Social
            "Boardgame": ["Boardgame", "Board Games", "Trò chơi"],
            "Social": ["Social", "Giao lưu kết bạn", "Giao lưu", "Kết bạn"],
            "Giao lưu kết bạn": ["Social", "Giao lưu kết bạn", "Giao lưu", "Kết bạn"],
        }
        cats = category_synonyms.get(category, [category])
        base_filter = and_(base_filter, Activity.category.in_(cats))
    if search:
        base_filter = and_(base_filter, or_(Activity.title.ilike(f"%{search}%"), Activity.description.ilike(f"%{search}%")))
    if free_to_join is True:
        base_filter = and_(base_filter, Activity.require_approval == False)
    if days_ahead is not None:
        deadline = now + timedelta(days=days_ahead)
        base_filter = and_(base_filter, Activity.start_time >= now, Activity.start_time <= deadline)
    if is_ctxh:
        base_filter = and_(base_filter, Activity.social_work_days.is_not(None), Activity.social_work_days > 0)
    if has_trophy:
        base_filter = and_(base_filter, Activity.trophy_id.is_not(None))

    # Count
    count_q = select(func.count()).select_from(Activity).where(base_filter)
    total = (await db.execute(count_q)).scalar() or 0

    # Fetch with distance
    distance_col = ST_Distance(Activity.marker_location, point).label("distance_meters")
    
    order_clauses = []
    if followed_user_ids:
        order_clauses.append(Activity.host_id.in_(followed_user_ids).desc())

    if sort_by == "time":
        order_clauses.append(Activity.start_time.asc())
        order_clauses.append(distance_col.asc())
    elif sort_by == "created_at":
        order_clauses.append(Activity.created_at.desc())
        order_clauses.append(distance_col.asc())
    else:  # default "distance"
        order_clauses.append(distance_col.asc())
        order_clauses.append(Activity.start_time.asc())

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
    if activity.marker_location is None:
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
            ST_Y(cast(Activity.marker_location, Geometry)).label("lat"),
            ST_X(cast(Activity.marker_location, Geometry)).label("lng"),
        ).where(Activity.id == activity_id)
    )
    row = result.one_or_none()
    if row and row.lat is not None:
        return (row.lat, row.lng)
    return None


async def list_hosted_activities(
    db: AsyncSession,
    user_id: uuid.UUID,
    status_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Activity], int]:
    """List all activities hosted by the user (both past and upcoming), sorted newest first."""
    base_filter = and_(
        Activity.is_deleted == False,
        Activity.host_id == user_id,
    )
    if status_filter == "upcoming":
        base_filter = and_(base_filter, Activity.end_time >= func.now())
        order_clause = Activity.start_time.asc()
    elif status_filter == "past":
        base_filter = and_(base_filter, Activity.end_time < func.now())
        order_clause = Activity.start_time.desc()
    else:
        order_clause = Activity.start_time.desc()

    count_q = select(func.count()).select_from(Activity).where(base_filter)
    total = (await db.execute(count_q)).scalar() or 0

    query = (
        select(Activity)
        .options(joinedload(Activity.host))
        .where(base_filter)
        .order_by(order_clause)
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    activities = list(result.unique().scalars().all())

    return activities, total


async def list_joined_activities(
    db: AsyncSession,
    user_id: uuid.UUID,
    status_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Activity], int]:
    """List all activities the user has joined (both past and upcoming), sorted newest first."""
    from app.modules.participation.models import JoinRequest, RequestStatus

    if status_filter == "upcoming":
        base_filter = and_(
            Activity.is_deleted == False,
            JoinRequest.user_id == user_id,
            JoinRequest.status.in_([RequestStatus.pending, RequestStatus.approved]),
            Activity.end_time >= func.now(),
        )
        order_clause = Activity.start_time.asc()
    elif status_filter == "past":
        base_filter = and_(
            Activity.is_deleted == False,
            JoinRequest.user_id == user_id,
            JoinRequest.status == RequestStatus.approved,
            Activity.end_time < func.now(),
        )
        order_clause = Activity.start_time.desc()
    elif status_filter == "cancelled":
        base_filter = and_(
            JoinRequest.user_id == user_id,
            or_(
                JoinRequest.status.in_([RequestStatus.cancelled, RequestStatus.declined]),
                Activity.is_deleted == True,
            ),
        )
        order_clause = JoinRequest.created_at.desc()
    else:
        base_filter = and_(
            Activity.is_deleted == False,
            JoinRequest.user_id == user_id,
            JoinRequest.status.in_([RequestStatus.pending, RequestStatus.approved]),
        )
        order_clause = JoinRequest.created_at.desc()

    count_q = select(func.count()).select_from(Activity).join(JoinRequest, Activity.id == JoinRequest.activity_id).where(base_filter)
    total = (await db.execute(count_q)).scalar() or 0

    query = (
        select(Activity, JoinRequest.attendance_confirmed, JoinRequest.created_at)
        .join(JoinRequest, Activity.id == JoinRequest.activity_id)
        .options(joinedload(Activity.host))
        .where(base_filter)
        .order_by(order_clause)
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    rows = result.unique().all()
    activities = [r[0] for r in rows]
    attendance_map = {r[0].id: bool(r[1]) for r in rows}
    joined_at_map = {r[0].id: r[2] for r in rows}

    return activities, total, attendance_map, joined_at_map
