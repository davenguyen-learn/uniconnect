import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.groups import repository as group_repo
from app.modules.groups.models import Group, GroupMember, GroupRole
from app.modules.groups.schemas import GroupCreate, GroupDetailResponse, GroupMemberResponse, GroupResponse, GroupUpdate


async def create_group(db: AsyncSession, owner_id: uuid.UUID, data: GroupCreate) -> GroupResponse:
    group = Group(
        name=data.name,
        description=data.description,
        allow_member_activities=data.allow_member_activities,
        allow_member_documents=data.allow_member_documents,
        owner_id=owner_id,
    )
    group = await group_repo.create_group(db, group)

    # Automatically add owner as admin
    member = GroupMember(
        group_id=group.id,
        user_id=owner_id,
        role=GroupRole.admin
    )
    await group_repo.add_member(db, member)
    
    return _build_group_response(group)


async def update_group(db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID, data: GroupUpdate) -> GroupResponse:
    group = await group_repo.get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    if group.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Only the owner can update group settings")
        
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(group, key, value)
        
    await db.flush()
    return _build_group_response(group)


async def get_group(db: AsyncSession, group_id: uuid.UUID) -> GroupDetailResponse:
    group = await group_repo.get_group_with_members(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    members_res = []
    for m in group.members:
        members_res.append(GroupMemberResponse(
            user_id=m.user_id,
            role=m.role,
            joined_at=m.created_at,
            username=m.user.username,
            full_name=m.user.full_name
        ))
        
    return GroupDetailResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        allow_member_activities=group.allow_member_activities,
        allow_member_documents=group.allow_member_documents,
        owner_id=group.owner_id,
        created_at=group.created_at,
        member_count=len(group.members),
        members=members_res
    )


async def join_group(db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID) -> None:
    group = await group_repo.get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    is_member = await group_repo.is_member(db, group_id, user_id)
    if is_member:
        raise HTTPException(status_code=400, detail="Already a member")
        
    member = GroupMember(
        group_id=group_id,
        user_id=user_id,
        role=GroupRole.member
    )
    await group_repo.add_member(db, member)


async def leave_group(db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID) -> None:
    group = await group_repo.get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    if group.owner_id == user_id:
        raise HTTPException(status_code=400, detail="Owner cannot leave the group")
        
    is_member = await group_repo.is_member(db, group_id, user_id)
    if not is_member:
        raise HTTPException(status_code=400, detail="Not a member")
        
    await group_repo.remove_member(db, group_id, user_id)


async def get_my_groups(db: AsyncSession, user_id: uuid.UUID) -> list[GroupResponse]:
    groups = await group_repo.get_my_groups(db, user_id)
    return [_build_group_response(g) for g in groups]


async def discover_groups(
    db: AsyncSession, 
    user_id: uuid.UUID, 
    search: str | None = None,
    sort_by: str = "newest",
    limit: int = 50
) -> list[GroupResponse]:
    groups = await group_repo.discover_groups(db, user_id, search, sort_by, limit)
    
    # If sort_by is most_members, sort in python
    if sort_by == "most_members":
        groups.sort(key=lambda g: len(g.members), reverse=True)
        
    return [
        GroupResponse(
            id=g.id,
            name=g.name,
            description=g.description,
            allow_member_activities=g.allow_member_activities,
            allow_member_documents=g.allow_member_documents,
            owner_id=g.owner_id,
            created_at=g.created_at,
            member_count=len(g.members),
        )
        for g in groups
    ]


from sqlalchemy.orm.attributes import instance_state

def _build_group_response(group: Group) -> GroupResponse:
    state = instance_state(group)
    member_count = 0
    if "members" not in state.unloaded:
        member_count = len(group.members)

    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        allow_member_activities=group.allow_member_activities,
        allow_member_documents=group.allow_member_documents,
        owner_id=group.owner_id,
        created_at=group.created_at,
        member_count=member_count
    )
