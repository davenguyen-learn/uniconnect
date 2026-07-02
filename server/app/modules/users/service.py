"""User profile business logic — uses session directly."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.users.models import User
from app.modules.users.schemas import UserProfile, UserUpdate


async def get_profile(db: AsyncSession, user_id: str) -> UserProfile:
    """Get a user's profile by ID."""
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError("User not found.")

    return UserProfile.model_validate(user)


async def update_profile(db: AsyncSession, user_id: str, data: UserUpdate) -> UserProfile:
    """Update the current user's profile with provided fields."""
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError("User not found.")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.flush()
    return UserProfile.model_validate(user)


async def follow_user(db: AsyncSession, follower_id: uuid.UUID, following_id: uuid.UUID) -> dict:
    if follower_id == following_id:
        from app.core.exceptions import ValidationError
        raise ValidationError("You cannot follow yourself.")

    from app.modules.users.models import UserFollow
    from sqlalchemy.exc import IntegrityError
    
    # Verify user exists
    target_user = await db.scalar(select(User).where(User.id == following_id))
    if not target_user:
        raise NotFoundError("User not found.")

    try:
        follow = UserFollow(follower_id=follower_id, following_id=following_id)
        db.add(follow)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        # Already following, ignore

    return {"status": "success"}


async def unfollow_user(db: AsyncSession, follower_id: uuid.UUID, following_id: uuid.UUID) -> dict:
    from sqlalchemy import delete
    from app.modules.users.models import UserFollow
    
    await db.execute(
        delete(UserFollow)
        .where(UserFollow.follower_id == follower_id, UserFollow.following_id == following_id)
    )
    await db.commit()
    return {"status": "success"}


async def get_follow_status(db: AsyncSession, user_id: uuid.UUID, target_id: uuid.UUID) -> dict:
    from app.modules.users.models import UserFollow
    from sqlalchemy import func

    is_following = await db.scalar(
        select(UserFollow).where(UserFollow.follower_id == user_id, UserFollow.following_id == target_id)
    )

    followers_count = await db.scalar(
        select(func.count()).select_from(UserFollow).where(UserFollow.following_id == target_id)
    )

    following_count = await db.scalar(
        select(func.count()).select_from(UserFollow).where(UserFollow.follower_id == target_id)
    )

    return {
        "is_following": is_following is not None,
        "followers_count": followers_count or 0,
        "following_count": following_count or 0,
    }


async def list_followers(db: AsyncSession, user_id: uuid.UUID, limit: int = 20, offset: int = 0):
    from app.modules.users.models import UserFollow
    from app.modules.users.schemas import UserFollowResponse
    from sqlalchemy import func

    count_q = select(func.count()).select_from(UserFollow).where(UserFollow.following_id == user_id)
    total = (await db.execute(count_q)).scalar() or 0

    q = (
        select(User).join(UserFollow, User.id == UserFollow.follower_id)
        .where(UserFollow.following_id == user_id)
        .limit(limit).offset(offset)
    )
    users = (await db.execute(q)).scalars().all()

    return UserFollowResponse(
        items=[UserProfile.model_validate(u) for u in users],
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total
    )


async def list_following(db: AsyncSession, user_id: uuid.UUID, limit: int = 20, offset: int = 0):
    from app.modules.users.models import UserFollow
    from app.modules.users.schemas import UserFollowResponse
    from sqlalchemy import func

    count_q = select(func.count()).select_from(UserFollow).where(UserFollow.follower_id == user_id)
    total = (await db.execute(count_q)).scalar() or 0

    q = (
        select(User).join(UserFollow, User.id == UserFollow.following_id)
        .where(UserFollow.follower_id == user_id)
        .limit(limit).offset(offset)
    )
    users = (await db.execute(q)).scalars().all()

    return UserFollowResponse(
        items=[UserProfile.model_validate(u) for u in users],
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total
    )

