"""Group API endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.groups import service as group_service
from app.modules.groups.schemas import GroupCreate, GroupDetailResponse, GroupResponse, GroupUpdate

router = APIRouter(prefix="/groups", tags=["groups"])


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    data: GroupCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new group."""
    return await group_service.create_group(db, uuid.UUID(current_user["sub"]), data)


@router.patch("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: uuid.UUID,
    data: GroupUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update group settings (owner only)."""
    return await group_service.update_group(db, group_id, uuid.UUID(current_user["sub"]), data)


@router.get("/my", response_model=list[GroupResponse])
async def get_my_groups(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List groups the current user belongs to."""
    return await group_service.get_my_groups(db, uuid.UUID(current_user["sub"]))


@router.get("/discover", response_model=list[GroupResponse])
async def discover_groups(
    search: str | None = Query(default=None, description="Search term for name or description"),
    sort_by: str = Query(default="newest", pattern="^(newest|oldest|most_members)$"),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get groups the current user can join."""
    return await group_service.discover_groups(
        db, 
        uuid.UUID(current_user["sub"]),
        search=search,
        sort_by=sort_by,
        limit=limit
    )


@router.get("/{group_id}", response_model=GroupDetailResponse)
async def get_group(
    group_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get details of a specific group."""
    return await group_service.get_group(db, group_id)


@router.post("/{group_id}/join", status_code=status.HTTP_204_NO_CONTENT)
async def join_group(
    group_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Join a group."""
    await group_service.join_group(db, group_id, uuid.UUID(current_user["sub"]))


@router.post("/{group_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_group(
    group_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Leave a group."""
    await group_service.leave_group(db, group_id, uuid.UUID(current_user["sub"]))


@router.get("/{group_id}/activities")
async def get_group_activities(
    group_id: uuid.UUID,
    category: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List activities belonging to a specific group (members only)."""
    from app.modules.groups.repository import get_group_by_id, is_member
    from app.modules.activities.service import list_activities

    user_id = uuid.UUID(current_user["sub"])

    group = await get_group_by_id(db, group_id)
    if not group:
        raise NotFoundError("Group not found.")

    if not await is_member(db, group_id, user_id):
        raise ForbiddenError("You must be a member of this group to view its activities.")

    return await list_activities(
        db, user_id=current_user["sub"], category=category, group_id=group_id,
        limit=limit, offset=offset,
    )


@router.get("/{group_id}/documents")
async def get_group_documents(
    group_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List documents belonging to a specific group (members only)."""
    from app.modules.groups.repository import get_group_by_id, is_member
    from app.modules.documents.service import list_documents

    user_id = uuid.UUID(current_user["sub"])

    group = await get_group_by_id(db, group_id)
    if not group:
        raise NotFoundError("Group not found.")

    if not await is_member(db, group_id, user_id):
        raise ForbiddenError("You must be a member of this group to view its documents.")

    return await list_documents(
        db, user_id=user_id, group_id=group_id,
        limit=limit, offset=offset,
    )
