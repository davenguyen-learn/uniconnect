"""Domain Service Adapters for LLM Tool Execution.

Adheres strictly to Phase 9 Architectural Locks:
- LOCK 1: Calls Domain Services / Repositories; never raw unauthorized SQL.
- LOCK 2: Returns Structured Typed Results (ActivitySearchToolResult, UserScheduleToolResult, GroupSearchToolResult).
- LOCK 3: Reuses Phase 7 calendar.service (ConflictDetector, intervals_overlap).
- LOCK 4: Independent calculation of conflict_status, registration_status, and eligibility_status.
- LOCK 5: GPS is untrusted; backend computes distance_meters and distance_status.
- LOCK 6: Calendar privacy DTO: exposes ONLY busy slots and safe reason codes, NEVER private titles.
- LOCK 7: Group search enforces group privacy and visibility rules.
"""

import uuid
from datetime import datetime, timezone, date, timedelta
from typing import Any

from sqlalchemy import and_, or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_SetSRID, ST_Distance

from app.modules.activities.models import Activity
from app.modules.groups.models import Group, GroupMember, GroupPrivacy
from app.modules.participation.models import JoinRequest, RequestStatus
from app.modules.chat.schemas import (
    ActivitySearchToolItem,
    ActivitySearchToolResult,
    BusySlotItem,
    UserScheduleToolResult,
    GroupSearchToolItem,
    GroupSearchToolResult,
)


async def search_activities_tool(
    db: AsyncSession,
    user_id: uuid.UUID | None,
    category: str | None = None,
    keyword: str | None = None,
    semantic_query: str | None = None,
    is_social_work: bool | None = None,
    exclude_user_busy_times: bool = True,
    lat: float | None = None,
    lng: float | None = None,
    radius_meters: int = 25000,
    limit: int = 5,
) -> ActivitySearchToolResult:
    """Search for activities using domain query filters and enrich with eligibility, conflict, and distance."""
    now = datetime.now(timezone.utc)

    # Base access filter: Public activity OR user is in the group
    if user_id:
        access_filter = or_(
            Activity.group_id.is_(None),
            Activity.group_id.in_(
                select(GroupMember.group_id).where(GroupMember.user_id == user_id)
            ),
        )
    else:
        access_filter = Activity.group_id.is_(None)

    base_filter = and_(
        Activity.is_deleted.is_(False),
        Activity.end_time > now,
        access_filter,
    )

    if is_social_work:
        base_filter = and_(
            base_filter,
            Activity.social_work_days.is_not(None),
            Activity.social_work_days > 0,
        )

    if category:
        base_filter = and_(base_filter, Activity.category.ilike(f"%{category}%"))

    if keyword:
        base_filter = and_(
            base_filter,
            or_(
                Activity.title.ilike(f"%{keyword}%"),
                Activity.description.ilike(f"%{keyword}%"),
                Activity.category.ilike(f"%{keyword}%"),
            ),
        )

    distance_col = None
    if lat is not None and lng is not None:
        point = ST_SetSRID(ST_MakePoint(lng, lat), 4326)
        base_filter = and_(
            base_filter,
            Activity.location.is_not(None),
            ST_DWithin(Activity.location, point, radius_meters),
        )
        distance_col = ST_Distance(Activity.location, point).label("distance_meters")

    query = select(Activity)

    similarity_col = None
    if semantic_query:
        try:
            from app.modules.chat.embeddings import generate_embedding
            query_embedding = generate_embedding(semantic_query)
            if query_embedding:
                similarity_col = Activity.embedding.cosine_distance(query_embedding).label("similarity_distance")
                query = query.add_columns(similarity_col).order_by(Activity.embedding.cosine_distance(query_embedding).asc())
        except Exception:
            pass

    if distance_col is not None:
        query = query.add_columns(distance_col)
        if similarity_col is None:
            query = query.order_by(distance_col.asc())
    elif similarity_col is None:
        query = query.order_by(Activity.start_time.asc())

    fetch_limit = limit * 3 if (exclude_user_busy_times and user_id) else limit
    query = query.options(joinedload(Activity.host)).where(base_filter).limit(fetch_limit)

    result = await db.execute(query)
    rows = result.unique().all()

    # Reuse Phase 7 Conflict Detector
    detector = None
    if user_id:
        try:
            from app.modules.calendar.service import get_detector_for_user
            detector = await get_detector_for_user(db, user_id)
        except Exception:
            detector = None

    items: list[ActivitySearchToolItem] = []
    for row in rows:
        activity: Activity = row[0]

        # 1. Compute conflict_status (LOCK 4)
        conflict_status = "none"
        if detector and activity.start_time and activity.end_time:
            c_info = detector.check_conflict(activity.start_time, activity.end_time)
            if c_info.has_conflict:
                conflict_status = c_info.level  # "hard_conflict" or "soft_conflict"
                if exclude_user_busy_times and conflict_status == "hard_conflict":
                    continue

        # 2. Compute registration_status (LOCK 4)
        registration_status = "available"
        if user_id:
            reg_stmt = select(JoinRequest).where(
                JoinRequest.activity_id == activity.id,
                JoinRequest.user_id == user_id,
            )
            reg_res = await db.execute(reg_stmt)
            existing_reg = reg_res.scalar_one_or_none()
            if existing_reg and existing_reg.status in (RequestStatus.approved, RequestStatus.pending):
                registration_status = "registered"

        if registration_status != "registered":
            if activity.start_time and activity.start_time < now:
                registration_status = "deadline_passed"
            elif activity.max_participants is not None and getattr(activity, "current_participants", 0) >= activity.max_participants:
                registration_status = "capacity_full"

        # 3. Compute eligibility_status (LOCK 4)
        eligibility_status = "eligible"
        if activity.group_id and user_id:
            mem_stmt = select(GroupMember).where(
                GroupMember.group_id == activity.group_id,
                GroupMember.user_id == user_id,
            )
            mem_res = await db.execute(mem_stmt)
            if not mem_res.scalar_one_or_none():
                eligibility_status = "not_eligible"

        # 4. Compute distance & status (LOCK 5)
        dist_m = None
        dist_status = "unknown"
        if len(row) > 1 and distance_col is not None:
            dist_idx = 2 if (similarity_col is not None and len(row) > 2) else 1
            if len(row) > dist_idx and row[dist_idx] is not None:
                dist_m = round(float(row[dist_idx]), 1)
                if dist_m <= 2000:
                    dist_status = "nearby"
                elif dist_m <= 10000:
                    dist_status = "moderate"
                else:
                    dist_status = "far"

        items.append(
            ActivitySearchToolItem(
                activity_id=str(activity.id),
                title=activity.title,
                start_time=activity.start_time.isoformat() if activity.start_time else "",
                end_time=activity.end_time.isoformat() if activity.end_time else "",
                location_name=activity.location_name or "Khuôn viên trường",
                social_work_days=activity.social_work_days,
                distance_meters=dist_m,
                distance_status=dist_status,
                conflict_status=conflict_status,
                registration_status=registration_status,
                eligibility_status=eligibility_status,
            )
        )

        if len(items) >= limit:
            break

    return ActivitySearchToolResult(items=items, total=len(items))


async def get_user_schedule_tool(
    db: AsyncSession,
    user_id: uuid.UUID,
    days_ahead: int = 7,
) -> UserScheduleToolResult:
    """
    Get user's busy slots for upcoming days.
    LOCK 6 PRIVACY: ONLY exposes time windows and reason_code, NEVER private titles!
    """
    from app.modules.calendar.service import get_user_calendar_events

    today = date.today()
    end_date = today + timedelta(days=days_ahead)
    events = await get_user_calendar_events(db, user_id, today, end_date)

    busy_slots: list[BusySlotItem] = []
    for e in events:
        # Determine privacy safe reason_code
        if e.event_type == "busy_slot":
            code = "personal_busy"
        else:
            code = "university_activity"

        busy_slots.append(
            BusySlotItem(
                start_time=e.start_time.isoformat(),
                end_time=e.end_time.isoformat(),
                reason_code=code,
            )
        )

    return UserScheduleToolResult(busy_slots=busy_slots, total_busy_slots=len(busy_slots))


async def search_groups_tool(
    db: AsyncSession,
    user_id: uuid.UUID | None,
    keyword: str | None = None,
    limit: int = 5,
) -> GroupSearchToolResult:
    """
    Search for campus clubs/groups respecting visibility (LOCK 7).
    Public groups or groups where user is a member are returned.
    """
    now = datetime.now(timezone.utc)

    # Base visibility filter
    if user_id:
        visibility_filter = or_(
            Group.privacy == GroupPrivacy.public,
            Group.id.in_(
                select(GroupMember.group_id).where(GroupMember.user_id == user_id)
            ),
        )
    else:
        visibility_filter = Group.privacy == GroupPrivacy.public

    stmt = select(Group).options(joinedload(Group.members)).where(
        Group.is_deleted.is_(False),
        visibility_filter,
    )

    if keyword:
        search_pattern = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                Group.name.ilike(search_pattern),
                Group.description.ilike(search_pattern),
            )
        )

    stmt = stmt.order_by(Group.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    groups = res.unique().scalars().all()

    items = [
        GroupSearchToolItem(
            group_id=str(g.id),
            name=g.name,
            description=g.description,
            privacy=g.privacy.value if hasattr(g.privacy, "value") else str(g.privacy),
            member_count=len(g.members),
        )
        for g in groups
    ]

    return GroupSearchToolResult(items=items, total=len(items))
