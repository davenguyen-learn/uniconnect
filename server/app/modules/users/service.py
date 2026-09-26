import io
import uuid
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError
from PIL.Image import DecompressionBombError, DecompressionBombWarning
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestError, NotFoundError, PayloadTooLargeError
from app.core.storage import FileStorage, local_storage
from app.modules.users.models import User
from app.modules.users.schemas import UserProfile, UserUpdate


async def get_profile(db: AsyncSession, user_id: str) -> UserProfile:
    """Get a user's profile by ID."""
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError("User not found.")

    return UserProfile.model_validate(user)


async def search_users(
    db: AsyncSession,
    query: str,
    limit: int = 10,
) -> list[UserProfile]:
    """Search active users by username or full name."""
    from sqlalchemy import or_
    pattern = f"%{query}%"
    stmt = (
        select(User)
        .where(
            User.is_active == True,
            or_(
                User.username.ilike(pattern),
                User.full_name.ilike(pattern),
            ),
        )
        .order_by(User.username.asc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    users = res.scalars().all()
    return [UserProfile.model_validate(u) for u in users]



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

    # 2. Trophies count and points
    trophy_query = (
        select(func.count(UserTrophy.id), func.count(UserTrophy.id) * 10)
        .select_from(UserTrophy)
        .where(UserTrophy.user_id == user_id)
    )
    trophy_res = await db.execute(trophy_query)
    try:
        one_row = trophy_res.one()
        total_trophies = int(one_row[0] or 0)
        total_points = int(one_row[1] or 0)
    except Exception:
        total_trophies = int(trophy_res.scalar() or 0)
        total_points = total_trophies * 10

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


def validate_and_process_avatar(file_bytes: bytes, declared_content_type: str | None = None) -> bytes:
    """
    Validate raw uploaded avatar bytes and convert to optimized WebP.
    Enforces size limits, safe pixel bounds, format verification, and transparency preservation.
    """
    if len(file_bytes) > settings.MAX_AVATAR_SIZE_BYTES:
        max_mb = settings.MAX_AVATAR_SIZE_BYTES // (1024 * 1024)
        raise PayloadTooLargeError(f"Avatar file size exceeds {max_mb}MB limit.")

    allowed_mimes = {"image/jpeg", "image/png", "image/webp"}
    if declared_content_type and declared_content_type.lower() not in allowed_mimes:
        raise BadRequestError("Unsupported file type. Only JPEG, PNG, and WebP images are allowed.")

    # Guard against decompression bombs by capping total decodable pixels
    Image.MAX_IMAGE_PIXELS = 16_000_000

    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("error", category=DecompressionBombWarning)

            # Phase 1: Inspect format, dimensions, and header integrity
            stream = io.BytesIO(file_bytes)
            img = Image.open(stream)
            detected_format = (img.format or "").upper()
            if detected_format not in ("JPEG", "JPG", "PNG", "WEBP"):
                raise BadRequestError("Invalid image format. Only JPEG, PNG, and WebP are supported.")

            if img.width > settings.MAX_AVATAR_DIMENSION or img.height > settings.MAX_AVATAR_DIMENSION:
                raise BadRequestError(
                    f"Image dimensions ({img.width}x{img.height}) exceed maximum allowed {settings.MAX_AVATAR_DIMENSION}px."
                )
            img.verify()

            # Phase 2: Fresh stream reopen to safely decode pixel data and convert
            stream.seek(0)
            img = Image.open(stream)
            img.load()

            # Preserve transparency if present
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")

            try:
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass

            output = io.BytesIO()
            img.save(output, format="WEBP", quality=85, optimize=True)
            return output.getvalue()

    except (DecompressionBombError, DecompressionBombWarning) as exc:
        raise BadRequestError("Image exceeds safe pixel density limits.") from exc
    except (UnidentifiedImageError, ValueError, OSError) as exc:
        raise BadRequestError("Uploaded file is not a valid or readable image.") from exc


async def update_avatar(
    db: AsyncSession,
    user_id: uuid.UUID,
    file_bytes: bytes,
    content_type: str | None = None,
    storage: FileStorage = local_storage,
) -> UserProfile:
    """
    Update user's avatar with transaction safety and orphan file cleanup.
    Flow: Validate -> Save new file -> Update DB -> Commit -> Delete old file.
    On DB commit failure, new file is deleted to prevent orphan file accumulation.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User not found.")

    webp_bytes = validate_and_process_avatar(file_bytes, content_type)
    unique_filename = f"{user_id}_{uuid.uuid4().hex}.webp"
    relative_path = f"{settings.AVATAR_UPLOAD_DIR}/{unique_filename}"

    new_avatar_url = await storage.save_file(webp_bytes, relative_path)
    old_avatar_url = user.avatar_url
    user.avatar_url = new_avatar_url

    try:
        await db.commit()
        await db.refresh(user)
    except Exception:
        await db.rollback()
        # Clean up newly created file if DB transaction failed
        await storage.delete_file(new_avatar_url)
        raise

    # DB committed successfully: clean up old avatar file if present
    if old_avatar_url and old_avatar_url.startswith("/uploads/"):
        await storage.delete_file(old_avatar_url)

    return UserProfile.model_validate(user)


async def delete_avatar(
    db: AsyncSession,
    user_id: uuid.UUID,
    storage: FileStorage = local_storage,
) -> UserProfile:
    """
    Delete user's avatar with safe ordering:
    Update DB avatar_url = None -> Commit DB -> Delete file from storage.
    If commit fails, old file remains intact.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User not found.")

    old_avatar_url = user.avatar_url
    if not old_avatar_url:
        return UserProfile.model_validate(user)

    user.avatar_url = None
    await db.commit()
    await db.refresh(user)

    # After DB commit is finalized, delete file from storage
    if old_avatar_url.startswith("/uploads/"):
        await storage.delete_file(old_avatar_url)

    return UserProfile.model_validate(user)



