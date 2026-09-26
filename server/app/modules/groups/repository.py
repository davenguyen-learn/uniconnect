from datetime import datetime, timezone
import uuid

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.modules.groups.models import (
    Group,
    GroupMember,
    GroupJoinRequest,
    GroupPrivacy,
    ActivityCoHost,
    ActivityCoHostInvitation,
)
from app.modules.activities.models import Activity
from app.modules.participation.models import JoinRequest


async def create_group(db: AsyncSession, group: Group) -> Group:
    db.add(group)
    await db.flush()
    return group


async def add_member(db: AsyncSession, member: GroupMember) -> GroupMember:
    db.add(member)
    await db.flush()
    return member


async def remove_member(db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID) -> None:
    result = await db.execute(
        select(GroupMember)
        .where(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
    )
    member = result.scalar_one_or_none()
    if member:
        await db.delete(member)
        await db.flush()


async def get_group_by_id(db: AsyncSession, group_id: uuid.UUID) -> Group | None:
    result = await db.execute(
        select(Group)
        .where(Group.id == group_id, Group.is_deleted == False)  # noqa: E712
    )
    return result.unique().scalar_one_or_none()


async def get_group_with_members(db: AsyncSession, group_id: uuid.UUID) -> Group | None:
    result = await db.execute(
        select(Group)
        .options(joinedload(Group.members).joinedload(GroupMember.user))
        .where(Group.id == group_id, Group.is_deleted == False)  # noqa: E712
    )
    return result.unique().scalar_one_or_none()


async def is_member(db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    result = await db.execute(
        select(GroupMember)
        .where(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
    )
    return result.scalar_one_or_none() is not None


from sqlalchemy.orm import selectinload

async def get_my_groups(db: AsyncSession, user_id: uuid.UUID) -> list[Group]:
    result = await db.execute(
        select(Group)
        .options(selectinload(Group.members))
        .join(GroupMember)
        .where(GroupMember.user_id == user_id, Group.is_deleted == False)  # noqa: E712
        .order_by(Group.name)
    )
    return list(result.unique().scalars().all())


async def discover_groups(
    db: AsyncSession, 
    user_id: uuid.UUID, 
    search: str | None = None,
    sort_by: str = "newest",
    limit: int = 50
) -> list[Group]:
    # Groups the user is NOT a member of
    subq = select(GroupMember.group_id).where(GroupMember.user_id == user_id)
    
    stmt = select(Group).options(selectinload(Group.members)).where(Group.is_deleted == False, Group.id.notin_(subq))
    
    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.where(
            (Group.name.ilike(search_pattern)) | 
            (Group.description.ilike(search_pattern))
        )
        
    if sort_by == "oldest":
        stmt = stmt.order_by(Group.created_at.asc())
    elif sort_by == "most_members":
        # We don't have member count readily queryable without subquery, 
        # so for now sort by created_at. We will do member count sort in python side or skip it.
        # But to be safe, just fallback to newest
        stmt = stmt.order_by(Group.created_at.desc())
    else: # newest
        stmt = stmt.order_by(Group.created_at.desc())
        
    stmt = stmt.limit(limit)
    
    result = await db.execute(stmt)
    return list(result.unique().scalars().all())


async def search_cohost_candidates(
    db: AsyncSession,
    activity_id: uuid.UUID,
    user_id: uuid.UUID,
    search: str | None = None,
    limit: int = 20,
) -> list[Group]:
    """
    Search candidate groups to invite as co-hosts for an activity:
    - Activity lead group is excluded
    - Already accepted co-hosts are excluded
    - Public groups: can be invited by anyone
    - Private groups: can only be invited if current user is a member/admin/owner of that group
    """
    # 1. Fetch activity to determine lead group
    act_res = await db.execute(
        select(Activity.group_id).where(Activity.id == activity_id, Activity.is_deleted.is_(False))
    )
    act_row = act_res.first()
    if act_row is None:
        return []

    excluded_group_ids: set[uuid.UUID] = set()
    lead_group_id = act_row[0]
    if lead_group_id:
        excluded_group_ids.add(lead_group_id)

    # 2. Exclude groups that are already accepted co-hosts
    cohost_res = await db.execute(
        select(ActivityCoHost.group_id).where(ActivityCoHost.activity_id == activity_id)
    )
    for gid in cohost_res.scalars().all():
        excluded_group_ids.add(gid)

    # 3. Exclude groups with pending invitations
    pending_res = await db.execute(
        select(ActivityCoHostInvitation.invited_group_id).where(
            ActivityCoHostInvitation.activity_id == activity_id,
            ActivityCoHostInvitation.status == "pending",
        )
    )
    for gid in pending_res.scalars().all():
        excluded_group_ids.add(gid)

    # 4. User's memberships
    user_memberships_subq = select(GroupMember.group_id).where(GroupMember.user_id == user_id)

    # 5. Privacy eligibility rule:
    # Any public group can be invited; private groups require current user membership
    privacy_cond = or_(
        Group.privacy == GroupPrivacy.public,
        and_(
            Group.privacy == GroupPrivacy.private,
            Group.id.in_(user_memberships_subq),
        ),
    )

    stmt = (
        select(Group)
        .options(selectinload(Group.members))
        .where(
            Group.is_deleted.is_(False),
            Group.status == "active",
            privacy_cond,
        )
    )

    if excluded_group_ids:
        stmt = stmt.where(Group.id.notin_(list(excluded_group_ids)))

    if search and search.strip():
        search_pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Group.name.ilike(search_pattern),
                Group.description.ilike(search_pattern),
                Group.public_description.ilike(search_pattern),
            )
        )

    stmt = stmt.order_by(Group.name.asc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.unique().scalars().all())


async def get_group_stats(db: AsyncSession, group_id: uuid.UUID) -> tuple[int, int, float]:
    """
    Server-derived group stats:
    1. member_count = COUNT(GroupMember WHERE group_id == :id)
    2. total_activities_count = COUNT(DISTINCT eligible activities where group is Lead Host or Accepted Co-Host, end_time < now)
    3. total_ctxh_contributed = SUM(distinct Activity.social_work_days) for eligible activities with confirmed attendance.
    """
    now = datetime.now(timezone.utc)

    # 1. Member count (Active confirmed members)
    mem_stmt = select(func.count(GroupMember.id)).where(GroupMember.group_id == group_id)
    mem_res = await db.execute(mem_stmt)
    member_count = mem_res.scalar() or 0

    # 2. Subquery for distinct completed activities where group is Lead Host or Accepted Co-Host
    lead_acts = select(Activity.id).where(
        Activity.group_id == group_id,
        Activity.is_deleted.is_(False),
        Activity.end_time < now,
    )
    cohost_acts = (
        select(ActivityCoHost.activity_id)
        .join(Activity, Activity.id == ActivityCoHost.activity_id)
        .where(
            ActivityCoHost.group_id == group_id,
            Activity.is_deleted.is_(False),
            Activity.end_time < now,
        )
    )
    eligible_act_ids_subq = lead_acts.union(cohost_acts).subquery()

    # Total activities count
    act_count_stmt = select(func.count()).select_from(eligible_act_ids_subq)
    act_count_res = await db.execute(act_count_stmt)
    total_activities_count = act_count_res.scalar() or 0

    # 3. Total CTXH contributed: Each eligible activity is counted at most once if it has confirmed attendance
    confirmed_acts_subq = (
        select(Activity.id, Activity.social_work_days)
        .join(JoinRequest, JoinRequest.activity_id == Activity.id)
        .where(
            Activity.id.in_(select(eligible_act_ids_subq.c.id)),
            JoinRequest.attendance_confirmed.is_(True),
            Activity.social_work_days.is_not(None),
        )
        .distinct()
        .subquery()
    )
    ctxh_stmt = select(func.coalesce(func.sum(confirmed_acts_subq.c.social_work_days), 0.0))
    ctxh_res = await db.execute(ctxh_stmt)
    total_ctxh_contributed = float(ctxh_res.scalar() or 0.0)

    return member_count, total_activities_count, total_ctxh_contributed


async def get_group_members_paginated(
    db: AsyncSession, group_id: uuid.UUID, limit: int = 20, offset: int = 0
) -> tuple[list[GroupMember], int]:
    count_stmt = select(func.count(GroupMember.id)).where(GroupMember.group_id == group_id)
    count_res = await db.execute(count_stmt)
    total = count_res.scalar() or 0

    stmt = (
        select(GroupMember)
        .options(joinedload(GroupMember.user))
        .where(GroupMember.group_id == group_id)
        .order_by(GroupMember.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    res = await db.execute(stmt)
    return list(res.unique().scalars().all()), total


async def get_group_join_requests(
    db: AsyncSession, group_id: uuid.UUID, status: str = "pending", limit: int = 20, offset: int = 0
) -> tuple[list[GroupJoinRequest], int]:
    count_stmt = select(func.count(GroupJoinRequest.id)).where(
        GroupJoinRequest.group_id == group_id, GroupJoinRequest.status == status
    )
    count_res = await db.execute(count_stmt)
    total = count_res.scalar() or 0

    stmt = (
        select(GroupJoinRequest)
        .options(joinedload(GroupJoinRequest.user))
        .where(GroupJoinRequest.group_id == group_id, GroupJoinRequest.status == status)
        .order_by(GroupJoinRequest.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    res = await db.execute(stmt)
    return list(res.unique().scalars().all()), total


async def get_cohost_invitations_for_group(
    db: AsyncSession, group_id: uuid.UUID, status: str | None = None, limit: int = 20, offset: int = 0
) -> tuple[list[ActivityCoHostInvitation], int]:
    stmt = (
        select(ActivityCoHostInvitation)
        .options(
            joinedload(ActivityCoHostInvitation.activity),
            joinedload(ActivityCoHostInvitation.host_group),
            joinedload(ActivityCoHostInvitation.invited_group),
        )
        .where(ActivityCoHostInvitation.invited_group_id == group_id)
    )
    if status:
        stmt = stmt.where(ActivityCoHostInvitation.status == status)

    count_stmt = select(func.count(ActivityCoHostInvitation.id)).where(
        ActivityCoHostInvitation.invited_group_id == group_id
    )
    if status:
        count_stmt = count_stmt.where(ActivityCoHostInvitation.status == status)

    count_res = await db.execute(count_stmt)
    total = count_res.scalar() or 0

    stmt = stmt.order_by(ActivityCoHostInvitation.created_at.desc()).limit(limit).offset(offset)
    res = await db.execute(stmt)
    return list(res.unique().scalars().all()), total


async def count_accepted_cohosts(db: AsyncSession, activity_id: uuid.UUID) -> int:
    stmt = select(func.count(ActivityCoHost.id)).where(ActivityCoHost.activity_id == activity_id)
    res = await db.execute(stmt)
    return res.scalar() or 0


