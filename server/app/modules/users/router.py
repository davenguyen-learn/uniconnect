"""User profile API endpoints."""

from fastapi import APIRouter, Depends
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.users import service
from app.modules.users.schemas import UserProfile, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfile)
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the authenticated user's profile."""
    return await service.get_profile(db, current_user["sub"])


@router.patch("/me", response_model=UserProfile)
async def update_my_profile(
    data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the authenticated user's profile."""
    return await service.update_profile(db, current_user["sub"], data)


@router.post("/me/verify")
async def verify_account(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Request account verification (auto-approves for now for demo purposes)."""
    # In a real app, this would submit a request to admin panel.
    from sqlalchemy import update
    from app.modules.users.models import User
    await db.execute(update(User).where(User.id == uuid.UUID(current_user["sub"])).values(is_verified=True))
    await db.commit()
    return {"status": "success", "message": "Account verified."}


import uuid
from fastapi import Query
from app.modules.users.schemas import UserFollowResponse, FollowStatusResponse

@router.get("/{user_id}", response_model=UserProfile)
async def get_user_profile(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a user's profile."""
    return await service.get_profile(db, str(user_id))


@router.post("/{user_id}/follow")
async def follow_user(
    user_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Follow a user."""
    return await service.follow_user(db, uuid.UUID(current_user["sub"]), user_id)


@router.delete("/{user_id}/follow")
async def unfollow_user(
    user_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unfollow a user."""
    return await service.unfollow_user(db, uuid.UUID(current_user["sub"]), user_id)


@router.get("/{user_id}/follow-status", response_model=FollowStatusResponse)
async def get_follow_status(
    user_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get follow status between current user and target user."""
    return await service.get_follow_status(db, uuid.UUID(current_user["sub"]), user_id)


@router.get("/{user_id}/followers", response_model=UserFollowResponse)
async def list_followers(
    user_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List a user's followers."""
    return await service.list_followers(db, user_id, limit, offset)


@router.get("/{user_id}/following", response_model=UserFollowResponse)
async def list_following(
    user_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List users that a user is following."""
    return await service.list_following(db, user_id, limit, offset)
