import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.groups.models import Group, GroupMember


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
    return result.scalar_one_or_none()


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
    return list(result.scalars().all())


async def discover_groups(db: AsyncSession, user_id: uuid.UUID, limit: int = 50) -> list[Group]:
    # Groups the user is NOT a member of
    subq = select(GroupMember.group_id).where(GroupMember.user_id == user_id)
    
    result = await db.execute(
        select(Group)
        .options(selectinload(Group.members))
        .where(Group.is_deleted == False, Group.id.notin_(subq))  # noqa: E712
        .order_by(Group.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
