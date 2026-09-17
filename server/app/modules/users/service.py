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


async def get_user_stats(db: AsyncSession, user_id: uuid.UUID, is_self: bool = False) -> dict:
    """Aggregate server-derived stats for user recognition, CTXH progress, and trophies."""
    from app.modules.participation.models import JoinRequest
    from app.modules.activities.models import Activity
    from app.modules.trophies.models import UserTrophy, Trophy
    from app.modules.users.policy import CTXH_TARGET_DAYS, resolve_rank_title
    from sqlalchemy import func

    # Check user exists
    user = await db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise NotFoundError("User not found.")

    # 1. CTXH days and attended activities count (Single aggregate query)
    ctxh_query = (
        select(
            func.coalesce(func.sum(Activity.social_work_days), 0.0),
            func.count(JoinRequest.id),
        )
        .select_from(JoinRequest)
        .join(Activity, JoinRequest.activity_id == Activity.id)
        .where(
            JoinRequest.user_id == user_id,
            JoinRequest.attendance_confirmed == True,
        )
    )
    ctxh_res = await db.execute(ctxh_query)
    total_ctxh_raw, total_attended_raw = ctxh_res.one()
    total_ctxh = float(total_ctxh_raw)
    total_attended = int(total_attended_raw)

    # 2. Trophies count and points (Single aggregate query)
    trophy_query = (
        select(
            func.count(UserTrophy.id),
            func.coalesce(func.sum(Trophy.points), 0),
        )
        .select_from(UserTrophy)
        .join(Trophy, UserTrophy.trophy_id == Trophy.id)
        .where(UserTrophy.user_id == user_id)
    )
    trophy_res = await db.execute(trophy_query)
    total_trophies_raw, total_points_raw = trophy_res.one()
    total_trophies = int(total_trophies_raw)
    total_points = int(total_points_raw)

    rank_title = resolve_rank_title(total_points)

    if not is_self:
        return {
            "user_id": str(user_id),
            "total_ctxh_days": total_ctxh,
            "total_attended_activities": total_attended,
            "total_trophies_count": total_trophies,
            "total_trophy_points": total_points,
            "rank_title": rank_title,
        }

    # Self / Private detailed calculations
    completion_percent = min(round((total_ctxh / CTXH_TARGET_DAYS) * 100, 1), 100.0)
    remaining_days = max(0.0, round(CTXH_TARGET_DAYS - total_ctxh, 1))
    is_target_reached = total_ctxh >= CTXH_TARGET_DAYS

    return {
        "user_id": str(user_id),
        "total_ctxh_days": total_ctxh,
        "target_ctxh_days": CTXH_TARGET_DAYS,
        "ctxh_completion_percent": completion_percent,
        "remaining_ctxh_days": remaining_days,
        "is_target_reached": is_target_reached,
        "total_attended_activities": total_attended,
        "total_trophies_count": total_trophies,
        "total_trophy_points": total_points,
        "rank_title": rank_title,
    }


