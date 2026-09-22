"""Participation business logic."""

import uuid
import math
import hmac
import hashlib
import time
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.core.exceptions import (
    CapacityFullError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.modules.activities import repository as activity_repo
from app.modules.participation import repository as participation_repo
from app.modules.participation.models import JoinRequest, RequestStatus
from app.modules.participation.schemas import JoinRequestCreate, JoinRequestResponse, UserInfo


def _to_response(jr: JoinRequest) -> JoinRequestResponse:
    user_info = None
    if jr.user:
        user_info = UserInfo(username=jr.user.username, full_name=jr.user.full_name)
    return JoinRequestResponse(
        id=jr.id,
        activity_id=jr.activity_id,
        user_id=jr.user_id,
        status=jr.status.value if hasattr(jr.status, 'value') else jr.status,
        message=jr.message,
        form_responses=jr.form_responses,
        attendance_confirmed=jr.attendance_confirmed,
        responded_at=jr.responded_at,
        created_at=jr.created_at,
        user=user_info,
    )


async def request_to_join(
    db: AsyncSession,
    activity_id: uuid.UUID,
    user_id: str,
    data: JoinRequestCreate,
    confirm_swap: bool = False,
) -> JoinRequestResponse:
    """Submit a join request for an activity with schedule conflict detection and smart swap."""
    uid = uuid.UUID(user_id)

    # Verify activity exists and is active
    activity = await activity_repo.get_by_id(db, activity_id)
    if not activity:
        raise NotFoundError("Activity not found.")

    # Host cannot join their own activity
    if str(activity.host_id) == user_id:
        raise ValidationError("You cannot join your own activity.")

    # Check capacity
    if activity.current_participants >= activity.max_participants:
        raise CapacityFullError()

    # Check for duplicate active request
    existing = await participation_repo.get_active_request(db, activity_id, uid)
    if existing:
        raise ConflictError("You already have an active request for this activity.")

    # Check Schedule Conflicts (Hard & Soft)
    from app.modules.calendar.service import get_detector_for_user
    detector = await get_detector_for_user(db, uid)
    conflict = detector.check_conflict(activity.start_time, activity.end_time)

    if conflict.has_conflict:
        if conflict.level == "hard_conflict":
            raise ConflictError(f"Không thể tham gia: {conflict.warning_message}")
        elif conflict.level == "soft_conflict" and conflict.swap_candidate:
            if not confirm_swap:
                swap_title = conflict.swap_candidate.get("title", "hoạt động khác")
                raise ConflictError(
                    f"Bạn đang có một yêu cầu tham gia cùng khung giờ tại '{swap_title}'. "
                    f"Vui lòng xác nhận đổi sang hoạt động này (confirm_swap=true)."
                )
            else:
                # Perform Smart Swap: cancel old pending request
                old_req_id = uuid.UUID(conflict.swap_candidate["join_request_id"])
                old_req = await participation_repo.get_by_id(db, old_req_id)
                if old_req and old_req.status == RequestStatus.pending:
                    await participation_repo.update_status(db, old_req, RequestStatus.cancelled)

    join_request = JoinRequest(
        activity_id=activity_id,
        user_id=uid,
        message=data.message,
        form_responses=data.form_responses,
        status=RequestStatus.approved if not activity.require_approval else RequestStatus.pending,
    )
    
    if not activity.require_approval:
        # Lock activity row and check capacity safely
        locked_activity = await participation_repo.lock_and_increment_participants(db, activity_id)
        if locked_activity.current_participants > locked_activity.max_participants:
            raise CapacityFullError()
            
    join_request = await participation_repo.create(db, join_request)
    return _to_response(join_request)


async def approve_request(
    db: AsyncSession, request_id: uuid.UUID, user_id: str
) -> JoinRequestResponse:
    """Approve a join request (host only). Uses row locking and verifies no overlap with another approved event."""
    jr = await participation_repo.get_by_id(db, request_id)
    if not jr:
        raise NotFoundError("Join request not found.")

    if str(jr.activity.host_id) != user_id:
        raise ForbiddenError("Only the host can approve requests.")

    if jr.status != RequestStatus.pending:
        raise ValidationError(f"Cannot approve a request with status '{jr.status.value}'.")

    # Double check if user has another approved/hosted activity at that time
    from app.modules.calendar.service import get_detector_for_user
    detector = await get_detector_for_user(db, jr.user_id)
    conflict = detector.check_conflict(jr.activity.start_time, jr.activity.end_time, exclude_activity_id=jr.activity_id)
    if conflict.has_conflict and conflict.level == "hard_conflict" and conflict.conflicting_with:
        if conflict.conflicting_with.type in ("approved_activity", "hosted_activity"):
            raise ValidationError(
                f"Thành viên này đã được duyệt tham gia hoạt động '{conflict.conflicting_with.title}' trong cùng khung giờ."
            )

    # Lock activity row and check capacity
    activity = await participation_repo.lock_and_increment_participants(db, jr.activity_id)
    if activity.current_participants > activity.max_participants:
        # Rollback the increment — this will be rolled back by the session
        raise CapacityFullError()

    jr = await participation_repo.update_status(db, jr, RequestStatus.approved)
    return _to_response(jr)


async def decline_request(
    db: AsyncSession, request_id: uuid.UUID, user_id: str
) -> JoinRequestResponse:
    """Decline a join request (host only)."""
    jr = await participation_repo.get_by_id(db, request_id)
    if not jr:
        raise NotFoundError("Join request not found.")

    if str(jr.activity.host_id) != user_id:
        raise ForbiddenError("Only the host can decline requests.")

    if jr.status != RequestStatus.pending:
        raise ValidationError(f"Cannot decline a request with status '{jr.status.value}'.")

    jr = await participation_repo.update_status(db, jr, RequestStatus.declined)
    return _to_response(jr)


async def cancel_request(
    db: AsyncSession, request_id: uuid.UUID, user_id: str
) -> JoinRequestResponse:
    """Cancel own join request (requester only)."""
    jr = await participation_repo.get_by_id(db, request_id)
    if not jr:
        raise NotFoundError("Join request not found.")

    if str(jr.user_id) != user_id:
        raise ForbiddenError("Only the requester can cancel the request.")

    if jr.status != RequestStatus.pending:
        raise ValidationError(f"Cannot cancel a request with status '{jr.status.value}'.")

    jr = await participation_repo.update_status(db, jr, RequestStatus.cancelled)
    return _to_response(jr)


async def leave_activity(
    db: AsyncSession, activity_id: uuid.UUID, user_id: str
) -> None:
    """Leave an approved activity."""
    uid = uuid.UUID(user_id)
    jr = await participation_repo.get_active_request(db, activity_id, uid)
    if not jr or jr.status != RequestStatus.approved:
        raise ValidationError("You have not joined this activity.")

    # Lock activity to safely decrement
    act = await activity_repo.get_by_id(db, activity_id)
    if not act:
        raise NotFoundError("Activity not found.")

    # Decrement participant count safely
    await participation_repo.decrement_participants(db, activity_id)
    
    jr = await participation_repo.update_status(db, jr, RequestStatus.cancelled)
    
    return None


async def list_requests(
    db: AsyncSession, activity_id: uuid.UUID, user_id: str
) -> list[JoinRequestResponse]:
    """List join requests. Host sees all, others see only their own."""
    activity = await activity_repo.get_by_id(db, activity_id)
    if not activity:
        raise NotFoundError("Activity not found.")

    is_host = str(activity.host_id) == user_id
    if is_host:
        requests = await participation_repo.list_by_activity(db, activity_id)
    else:
        requests = await participation_repo.list_by_user(db, activity_id, uuid.UUID(user_id))

    return [_to_response(jr) for jr in requests]


async def _award_trophy_if_eligible(db: AsyncSession, activity, user_id: uuid.UUID) -> bool:
    """Award trophy to user if activity has a trophy attached and not yet awarded."""
    from app.modules.trophies.models import UserTrophy, Trophy
    from sqlalchemy import select

    trophy = await db.scalar(select(Trophy).where(Trophy.activity_id == activity.id))
    if not trophy:
        return False

    existing = await db.scalar(
        select(UserTrophy).where(
            UserTrophy.user_id == user_id,
            UserTrophy.trophy_id == trophy.id,
            UserTrophy.activity_id == activity.id,
        )
    )
    if existing:
        return False

    user_trophy = UserTrophy(
        user_id=user_id,
        trophy_id=trophy.id,
        activity_id=activity.id,
    )
    db.add(user_trophy)

    trophy_name = trophy.name if trophy else "Danh hiệu mới"

    # Send in-app notification
    try:
        from app.modules.notifications.repository import create_notification
        await create_notification(
            db=db,
            user_id=user_id,
            actor_id=activity.host_id,
            type="trophy_awarded",
            activity_id=activity.id,
            action_url="/profile",
            message=f"Chúc mừng! Bạn đã nhận được danh hiệu '{trophy_name}' từ hoạt động '{activity.title}'.",
        )
    except Exception as e:
        logger.warning(f"Failed to send trophy notification to {user_id}: {e}")

    return True


def calculate_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on the Earth (Haversine formula)."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def generate_rotating_token(secret: str, activity_id: uuid.UUID, time_offset_steps: int = 0) -> str:
    """Generate 6-character dynamic OTP token for QR code rotation every 30s."""
    step = int(time.time() // 30) + time_offset_steps
    msg = f"{activity_id}:{step}".encode()
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()[:6].upper()


def get_valid_tokens(secret: str, activity_id: uuid.UUID) -> list[str]:
    """Get valid tokens (current step and previous step to tolerate clock drift/network delay)."""
    return [
        generate_rotating_token(secret, activity_id, 0),
        generate_rotating_token(secret, activity_id, -1),
    ]


async def get_check_in_code(db: AsyncSession, activity_id: uuid.UUID, user_id: str) -> dict:
    """Get check-in code and dynamic rotating token for Host or Accepted Co-Hosts."""
    activity = await activity_repo.get_by_id(db, activity_id)
    if not activity:
        raise NotFoundError("Activity not found.")

    from app.modules.groups.permissions import can_open_checkin
    has_permission = await can_open_checkin(db, uuid.UUID(user_id), activity_id)
    if not has_permission:
        raise ForbiddenError("Only the host or accepted co-hosts can access the check-in code.")


    if not activity.check_in_code:
        import secrets
        activity.check_in_code = secrets.token_hex(4).upper()
        await db.commit()
        await db.refresh(activity)

    secret = activity.check_in_code
    rotating_token = generate_rotating_token(secret, activity.id, 0)
    now = time.time()
    expires_in = int(30 - (now % 30))

    return {
        "check_in_code": activity.check_in_code,
        "rotating_token": rotating_token,
        "expires_in_seconds": expires_in,
        "check_in_radius": activity.check_in_radius,
    }


async def check_in_participant(
    db: AsyncSession,
    activity_id: uuid.UUID,
    user_id: str,
    code: str,
    lat: float | None = None,
    lng: float | None = None,
    accuracy: float | None = None,
) -> dict:
    """Participant check-in with untrusted client GPS evidence & server-side proximity validation."""
    activity = await activity_repo.get_by_id(db, activity_id)
    if not activity:
        raise NotFoundError("Activity not found.")

    uid = uuid.UUID(user_id)
    jr = await participation_repo.get_active_request(db, activity_id, uid)
    if not jr or jr.status != RequestStatus.approved:
        raise ForbiddenError("Bạn chưa được duyệt tham gia hoạt động này.")

    # 1. Idempotency Check (pre-check before expensive operations)
    if jr.attendance_confirmed:
        return {
            "message": "Bạn đã được điểm danh trước đó.",
            "attendance_confirmed": True,
            "trophy_awarded": False,
            "already_confirmed": True,
        }

    # 2. Session Window Guard
    now = datetime.now(timezone.utc)
    if activity.start_time:
        start_tz = activity.start_time if activity.start_time.tzinfo else activity.start_time.replace(tzinfo=timezone.utc)
        earliest_allowed = start_tz - timedelta(minutes=30)
        if now < earliest_allowed:
            raise ValidationError("Phiên điểm danh chưa mở. Vui lòng quay lại trước giờ bắt đầu sự kiện 30 phút.")
    if activity.end_time:
        end_tz = activity.end_time if activity.end_time.tzinfo else activity.end_time.replace(tzinfo=timezone.utc)
        latest_allowed = end_tz + timedelta(hours=2)
        if now > latest_allowed:
            raise ValidationError("Phiên điểm danh đã kết thúc.")

    # 3. Validate Code / Rotating OTP
    secret = activity.check_in_code or ""
    clean_code = code.strip().upper()
    valid_codes = [secret.upper()] + get_valid_tokens(secret, activity.id)
    if clean_code not in valid_codes:
        raise ValidationError("Mã điểm danh không hợp lệ hoặc đã hết hạn.")

    # 4. Geofencing & Untrusted GPS Validation
    dist = 0.0
    coords = await activity_repo.get_coordinates_from_db(db, activity_id)
    if coords and coords[0] != 0:
        act_lat, act_lng = coords
        if lat is None or lng is None:
            raise ValidationError("Vui lòng bật định vị GPS trên thiết bị để xác nhận bạn đang có mặt tại sự kiện.")

        # Accuracy enforcement: domain error mapped to gps_accuracy_low
        if accuracy is None:
            raise ValidationError("Thiết bị không cung cấp độ chính xác GPS. Vui lòng bật định vị chính xác cao.")
        if accuracy > 100.0:
            raise ValidationError(
                f"Độ chính xác GPS không đủ tin cậy ({int(accuracy)}m > 100m). Vui lòng di chuyển ra nơi thoáng đãng để cải thiện tín hiệu vệ tinh."
            )

        dist = calculate_distance_meters(lat, lng, act_lat, act_lng)
        if dist > activity.check_in_radius:
            raise ValidationError(
                f"Bạn đang ở cách địa điểm sự kiện khoảng {int(dist)}m (vượt quá bán kính cho phép {activity.check_in_radius}m)."
            )

    # 5. Atomic Attendance Update (Race condition / concurrent request protection)
    stmt = (
        update(JoinRequest)
        .where(
            JoinRequest.id == jr.id,
            JoinRequest.attendance_confirmed == False,
        )
        .values(
            attendance_confirmed=True,
            responded_at=now,
        )
    )
    result = await db.execute(stmt)
    if result.rowcount == 0:
        # Another concurrent request already marked attendance
        return {
            "message": "Bạn đã được điểm danh trước đó.",
            "attendance_confirmed": True,
            "trophy_awarded": False,
            "already_confirmed": True,
        }

    # 6. Idempotent Reward within the same transaction boundary
    trophy_awarded = await _award_trophy_if_eligible(db, activity, uid)

    # 7. Audit Logging
    logger.info(
        f"[AUDIT CHECK-IN] User {uid} checked in to Activity {activity_id}. "
        f"Distance: {dist:.1f}m, Accuracy: {accuracy}m, Timestamp: {now.isoformat()}"
    )

    # 8. Commit single atomic transaction
    await db.commit()

    return {
        "message": "Điểm danh thành công!",
        "attendance_confirmed": True,
        "trophy_awarded": trophy_awarded,
        "already_confirmed": False,
    }


async def update_participant_attendance(
    db: AsyncSession,
    activity_id: uuid.UUID,
    target_user_id: uuid.UUID,
    host_user_id: str,
    attended: bool,
) -> dict:
    """Host manual attendance toggle for a participant."""
    activity = await activity_repo.get_by_id(db, activity_id)
    if not activity:
        raise NotFoundError("Activity not found.")
    if str(activity.host_id) != host_user_id:
        raise ForbiddenError("Chỉ Host mới có quyền cập nhật điểm danh.")

    jr = await participation_repo.get_active_request(db, activity_id, target_user_id)
    if not jr or jr.status != RequestStatus.approved:
        raise NotFoundError("Người dùng chưa được duyệt tham gia hoạt động này.")

    jr.attendance_confirmed = attended
    trophy_awarded = False
    if attended:
        trophy_awarded = await _award_trophy_if_eligible(db, activity, target_user_id)
    else:
        # Revoke trophy if attended set to False
        from app.modules.trophies.models import UserTrophy, Trophy
        from sqlalchemy import delete
        trophy = await db.scalar(select(Trophy).where(Trophy.activity_id == activity.id))
        if trophy:
            await db.execute(
                delete(UserTrophy).where(
                    UserTrophy.user_id == target_user_id,
                    UserTrophy.trophy_id == trophy.id,
                    UserTrophy.activity_id == activity.id,
                )
            )

    await db.commit()
    return {
        "message": "Cập nhật điểm danh thành công.",
        "attendance_confirmed": attended,
        "trophy_awarded": trophy_awarded,
    }


async def list_participants(db: AsyncSession, activity_id: uuid.UUID) -> list[JoinRequestResponse]:
    """List approved participants and auto-mark attended if activity end time passed."""
    from sqlalchemy import select
    from sqlalchemy.orm import joinedload

    activity = await activity_repo.get_by_id(db, activity_id)
    if not activity:
        raise NotFoundError("Activity not found.")

    result = await db.execute(
        select(JoinRequest)
        .options(joinedload(JoinRequest.user))
        .where(
            JoinRequest.activity_id == activity_id,
            JoinRequest.status == RequestStatus.approved
        )
        .order_by(JoinRequest.created_at.asc())
    )
    requests = list(result.unique().scalars().all())

    # Check auto attendance
    if getattr(activity, 'attendance_mode', 'manual') == 'auto':
        now = datetime.now(timezone.utc)
        end = activity.end_time
        if hasattr(end, 'tzinfo') and end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        if now >= end:
            changed = False
            for r in requests:
                if not r.attendance_confirmed:
                    r.attendance_confirmed = True
                    await _award_trophy_if_eligible(db, activity, r.user_id)
                    changed = True
            if changed:
                await db.commit()

    return [_to_response(r) for r in requests]


async def get_certificate_data(
    db: AsyncSession,
    activity_id: uuid.UUID,
    user_id: str,
    target_user_id: uuid.UUID | None = None,
) -> dict:
    """Generate official certificate of participation data for an attended user."""
    from app.modules.users.models import User
    from app.modules.trophies.models import Trophy
    from sqlalchemy import select

    activity = await activity_repo.get_by_id(db, activity_id)
    if not activity:
        raise NotFoundError("Activity not found.")

    effective_user_id = uuid.UUID(user_id)
    if target_user_id and target_user_id != effective_user_id:
        if str(activity.host_id) != user_id:
            raise ForbiddenError("Only the host can view certificates of other participants.")
        effective_user_id = target_user_id

    jr = await participation_repo.get_active_request(db, activity_id, effective_user_id)
    if not jr or not jr.attendance_confirmed:
        raise ValidationError("Chỉ người tham gia đã được xác nhận điểm danh mới có thể nhận Giấy chứng nhận.")

    participant = await db.scalar(select(User).where(User.id == effective_user_id))
    if not participant:
        raise NotFoundError("Participant not found.")

    host = await db.scalar(select(User).where(User.id == activity.host_id))
    host_name = (host.full_name or host.username) if host else "Ban Tổ Chức"
    host_university = host.university if host else None

    # Trophy info
    trophy_name = None
    trophy_icon = None
    trophy_points = None
    trophy = await db.scalar(select(Trophy).where(Trophy.activity_id == activity.id))
    if trophy:
        trophy_name = trophy.name
        trophy_icon = trophy.icon
        trophy_points = trophy.points

    act_part = str(activity.id).replace('-', '')[:6].upper()
    user_part = str(effective_user_id).replace('-', '')[:6].upper()
    cert_code = f"UC-{act_part}-{user_part}"

    start_str = activity.start_time.strftime("%d/%m/%Y") if hasattr(activity.start_time, 'strftime') else str(activity.start_time)[:10]

    return {
        "certificate_code": cert_code,
        "activity_id": activity.id,
        "user_id": effective_user_id,
        "participant_name": participant.full_name or participant.username,
        "participant_username": participant.username,
        "participant_university": participant.university,
        "activity_title": activity.title,
        "activity_date": start_str,
        "meeting_location": getattr(activity, "meeting_location", None) or getattr(activity, "location_name", None),
        "location_name": getattr(activity, "meeting_location", None) or getattr(activity, "location_name", None),
        "host_name": host_name,
        "host_university": host_university,
        "social_work_days": activity.social_work_days,
        "trophy_name": trophy_name,
        "trophy_icon": trophy_icon,
        "trophy_points": trophy_points,
        "issued_at": datetime.now(timezone.utc),
        "verification_url": f"/verify-certificate?code={cert_code}",
    }


async def verify_certificate_code(db: AsyncSession, code: str) -> dict:
    """Public verification lookup for certificate code."""
    from sqlalchemy import select, cast, String

    clean_code = code.strip().upper()
    parts = clean_code.split('-')
    if len(parts) != 3 or parts[0] != "UC":
        raise NotFoundError("Mã giấy chứng nhận không đúng định dạng.")

    act_prefix = parts[1].lower()
    user_prefix = parts[2].lower()

    result = await db.execute(
        select(JoinRequest)
        .where(
            JoinRequest.attendance_confirmed.is_(True),
            cast(JoinRequest.activity_id, String).like(f"{act_prefix}%"),
            cast(JoinRequest.user_id, String).like(f"{user_prefix}%"),
        )
    )
    jr = result.scalars().first()
    if not jr:
        raise NotFoundError("Không tìm thấy giấy chứng nhận hợp lệ với mã này.")

    return await get_certificate_data(db, jr.activity_id, str(jr.user_id))
