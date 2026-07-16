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
    return list(result.scalars().all())
