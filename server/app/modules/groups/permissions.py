import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.groups.models import Group, GroupMember, GroupRole, ActivityCoHost, ActivityCoHostInvitation
from app.modules.activities.models import Activity


async def is_group_admin_or_owner(db: AsyncSession, user_id: uuid.UUID, group_id: uuid.UUID) -> bool:
    """Helper to check if user is the group owner or has admin role in the group."""
    # Check if user is owner
    grp_stmt = select(Group.id).where(Group.id == group_id, Group.owner_id == user_id)
    grp_res = await db.execute(grp_stmt)
    if grp_res.scalar_one_or_none():
        return True

    # Check if user has admin membership
    mem_stmt = select(GroupMember.id).where(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id,
        GroupMember.role == GroupRole.admin,
    )
    mem_res = await db.execute(mem_stmt)
    return mem_res.scalar_one_or_none() is not None


async def can_manage_group(db: AsyncSession, user_id: uuid.UUID, group_id: uuid.UUID) -> bool:
    """Only group owner can manage core group settings or disband group."""
    stmt = select(Group.id).where(Group.id == group_id, Group.owner_id == user_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none() is not None


async def can_approve_join_request(db: AsyncSession, user_id: uuid.UUID, group_id: uuid.UUID) -> bool:
    """Owner or admin of the group can review/approve/reject join requests."""
    return await is_group_admin_or_owner(db, user_id, group_id)


async def can_invite_cohost(db: AsyncSession, user_id: uuid.UUID, activity_id: uuid.UUID) -> bool:
    """Only direct activity host or owner/admin of the activity's lead group can invite co-hosts."""
    act_stmt = select(Activity).where(Activity.id == activity_id, Activity.is_deleted.is_(False))
    act_res = await db.execute(act_stmt)
    act = act_res.scalar_one_or_none()
    if not act:
        return False

    if act.host_id == user_id:
        return True

    if act.group_id:
        return await is_group_admin_or_owner(db, user_id, act.group_id)

    return False


async def can_respond_cohost_invitation(db: AsyncSession, user_id: uuid.UUID, invitation_id: uuid.UUID) -> bool:
    """Only owner or admin of the invited group can accept or decline a co-host invitation."""
    inv_stmt = select(ActivityCoHostInvitation.invited_group_id).where(ActivityCoHostInvitation.id == invitation_id)
    inv_res = await db.execute(inv_stmt)
    invited_group_id = inv_res.scalar_one_or_none()
    if not invited_group_id:
        return False

    return await is_group_admin_or_owner(db, user_id, invited_group_id)


async def can_open_checkin(db: AsyncSession, user_id: uuid.UUID, activity_id: uuid.UUID) -> bool:
    """
    Check-in authority resolution:
    Allowed for:
    1. Direct activity host user.
    2. Owner or admin of the activity's lead host group.
    3. Owner or admin of ANY accepted co-host group for this activity.
    """
    act_stmt = select(Activity).where(Activity.id == activity_id, Activity.is_deleted.is_(False))
    act_res = await db.execute(act_stmt)
    act = act_res.scalar_one_or_none()
    if not act:
        return False

    # 1. Direct host
    if act.host_id == user_id:
        return True

    # 2. Lead host group admin/owner
    if act.group_id and await is_group_admin_or_owner(db, user_id, act.group_id):
        return True

    # 3. Accepted co-host group admin/owner
    cohost_stmt = select(ActivityCoHost.group_id).where(ActivityCoHost.activity_id == activity_id)
    cohost_res = await db.execute(cohost_stmt)
    cohost_group_ids = list(cohost_res.scalars().all())

    for gid in cohost_group_ids:
        if await is_group_admin_or_owner(db, user_id, gid):
            return True

    return False


async def can_manage_activity(db: AsyncSession, user_id: uuid.UUID, activity_id: uuid.UUID) -> bool:
    """
    Activity management authority (editing, deleting, canceling):
    Allowed ONLY for direct host or lead group owner/admin.
    Accepted co-hosts DO NOT have management authority over the activity!
    """
    act_stmt = select(Activity).where(Activity.id == activity_id, Activity.is_deleted.is_(False))
    act_res = await db.execute(act_stmt)
    act = act_res.scalar_one_or_none()
    if not act:
        return False

    if act.host_id == user_id:
        return True

    if act.group_id:
        return await is_group_admin_or_owner(db, user_id, act.group_id)

    return False
