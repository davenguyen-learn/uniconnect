"""Activity business logic."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.modules.activities import repository
from app.modules.activities.constants import TEMPORAL_LOCK_MINUTES
from app.modules.activities.models import Activity, ActivityPrivacy
from app.modules.activities.schemas import (
    ActivityCreate,
    ActivityListResponse,
    ActivityResponse,
    ActivityUpdate,
    HostInfo,
    NearbyQuery,
)
from app.modules.activities.spatial import obfuscate_coordinates


def _activity_to_response(
    activity: Activity,
    lat: float,
    lng: float,
    distance: float | None = None,
    private_description: str | None = None,
    conflict_info: Any | None = None,
    attendance_confirmed: bool | None = None,
    joined_at: datetime | None = None,
    co_hosts: list[Any] | None = None,
) -> ActivityResponse:
    """Convert an Activity model to a response schema."""
    host_info = None
    if activity.host:
        host_info = HostInfo(
            username=activity.host.username,
            full_name=activity.host.full_name,
            avatar_url=getattr(activity.host, "avatar_url", None),
        )

    group_info = None
    if getattr(activity, 'group', None):
        from app.modules.activities.schemas import GroupInfo
        group_info = GroupInfo(
            id=activity.group.id,
            name=activity.group.name,
            avatar_url=getattr(activity.group, "avatar_url", None),
        )

    custom_form_info = None
    if getattr(activity, 'custom_form', None):
        # We need to construct CustomFormResponse from Activity.custom_form
        custom_form_info = activity.custom_form
        # Due to from_attributes=True, pydantic handles the parsing automatically

    trophy_info = None
    if getattr(activity, 'trophy', None):
        trophy_info = activity.trophy

    return ActivityResponse(
        id=activity.id,
        host_id=activity.host_id,
        group_id=getattr(activity, 'group_id', None),
        title=activity.title,
        description=activity.description,
        private_description=private_description,
        category=activity.category,
        latitude=lat,
        longitude=lng,
        meeting_location=getattr(activity, 'meeting_location', None) or getattr(activity, 'location_name', None),
        location_name=getattr(activity, 'meeting_location', None) or getattr(activity, 'location_name', None),
        start_time=activity.start_time,
        end_time=activity.end_time,
        max_participants=activity.max_participants,
        current_participants=activity.current_participants,
        privacy=activity.privacy.value if hasattr(activity.privacy, 'value') else activity.privacy,
        require_approval=activity.require_approval,
        social_work_days=activity.social_work_days,
        created_at=activity.created_at,
        host=host_info,
        group=group_info,
        co_hosts=co_hosts or [],
        distance_meters=distance,
        custom_form=custom_form_info,
        trophy=trophy_info,
        conflict_info=conflict_info,
        attendance_mode=getattr(activity, 'attendance_mode', 'manual') or 'manual',
        check_in_radius=getattr(activity, 'check_in_radius', 300) or 300,
        attendance_confirmed=attendance_confirmed,
        joined_at=joined_at,
    )


async def create_activity(
    db: AsyncSession, user_id: str, data: ActivityCreate
) -> ActivityResponse:
    """Create a new activity."""
    now = datetime.now(timezone.utc) - timedelta(minutes=3)
    if data.start_time.tzinfo is None:
        data.start_time = data.start_time.replace(tzinfo=timezone.utc)
    if data.end_time.tzinfo is None:
        data.end_time = data.end_time.replace(tzinfo=timezone.utc)

    if data.start_time <= now:
        raise ValidationError("Thời gian bắt đầu phải ở trong tương lai (sau thời điểm hiện tại).")

    # Check host conflict
    from app.modules.calendar.service import get_detector_for_user
    detector = await get_detector_for_user(db, uuid.UUID(user_id))
    host_conflict = detector.check_conflict(data.start_time, data.end_time)
    if host_conflict.has_conflict and host_conflict.conflicting_with and host_conflict.conflicting_with.type == "hosted_activity":
        raise ConflictError(f"Bạn đang là Host của hoạt động '{host_conflict.conflicting_with.title}' trong cùng khung giờ.")
        
    if data.group_id:
        from app.modules.groups.repository import get_group_by_id
        group = await get_group_by_id(db, data.group_id)
        if group:
            if getattr(group, "status", "active") == "inactive":
                raise ValidationError("Nhóm này đã dừng hoạt động, không thể tạo hoạt động mới.")
            if group.owner_id != uuid.UUID(user_id) and not group.allow_member_activities:
                raise ForbiddenError("Group members are not allowed to post activities.")

    embedding_text = f"{data.title}\n{data.description or ''}"
    from app.modules.chat.embeddings import generate_embedding
    
    from app.modules.users.models import User, UserRole
    from sqlalchemy import select
    user_result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user_obj = user_result.scalar_one_or_none()
    
    if not user_obj or user_obj.role not in [UserRole.admin, UserRole.edu_org]:
        data.social_work_days = None

    if data.trophy_id:
        user_role = user_obj.role.value if hasattr(user_obj.role, "value") else str(user_obj.role)
        if not user_obj or user_role not in [UserRole.admin.value, UserRole.edu_org.value]:
            raise ForbiddenError("Chỉ Ban Quản trị hoặc Tổ chức Giáo dục mới có thể gắn Trophy vào hoạt động.")

    import secrets
    check_in_code = secrets.token_hex(4).upper()

    meeting_loc = data.meeting_location or data.location_name
    activity = Activity(
        host_id=uuid.UUID(user_id),
        title=data.title,
        description=data.description,
        private_description=data.private_description,
        category=data.category,
        marker_location=f"SRID=4326;POINT({data.longitude} {data.latitude})",
        meeting_location=meeting_loc,
        start_time=data.start_time,
        end_time=data.end_time,
        max_participants=data.max_participants,
        privacy=data.privacy,
        require_approval=data.require_approval,
        social_work_days=data.social_work_days,
        group_id=data.group_id,
        attendance_mode=data.attendance_mode or "manual",
        check_in_radius=data.check_in_radius or 300,
        check_in_code=check_in_code,
        current_participants=1,  # Host is counted
        embedding=generate_embedding(embedding_text),
    )

    if data.trophy_id:
        from app.modules.trophies.models import Trophy
        from sqlalchemy import select
        trophy = await db.scalar(select(Trophy).where(Trophy.id == data.trophy_id))
        if trophy:
            trophy.activity_id = activity.id
    
    if data.custom_form:
        from app.modules.forms.models import CustomForm, FormField, FieldType
        form_fields = []
        for f in data.custom_form.fields:
            form_fields.append(FormField(
                label=f.label,
                field_type=f.field_type,
                is_required=f.is_required,
                order=f.order,
                meta_data=f.meta_data,
            ))
        activity.custom_form = CustomForm(
            title=data.custom_form.title,
            description=data.custom_form.description,
            fields=form_fields,
        )

    activity = await repository.create(db, activity)
    return _activity_to_response(activity, data.latitude, data.longitude, private_description=data.private_description)


async def get_activity(
    db: AsyncSession, activity_id: uuid.UUID, user_id: str | None = None
) -> ActivityResponse:
    """Get a single activity. Obfuscates coordinates for non-participants."""
    activity = await repository.get_by_id(db, activity_id)
    if not activity:
        raise NotFoundError("Activity not found.")

    # Check access control for private activities
    is_private = (
        activity.privacy == ActivityPrivacy.private
        or str(activity.privacy).lower() in ("activityprivacy.private", "private")
    )

    if is_private:
        if not user_id:
            raise ForbiddenError("This activity is restricted to group members.")

        is_host = str(activity.host_id) == user_id
        if not is_host:
            is_authorized = False
            user_uuid = uuid.UUID(user_id)

            # Check if user is member of host group
            if activity.group_id:
                from app.modules.groups.repository import is_member
                if await is_member(db, activity.group_id, user_uuid):
                    is_authorized = True

            # Check if user is member of any accepted co-host group
            if not is_authorized:
                from app.modules.groups.models import ActivityCoHost, GroupMember
                from sqlalchemy import select, and_
                cohost_res = await db.execute(
                    select(GroupMember.id).join(
                        ActivityCoHost, ActivityCoHost.group_id == GroupMember.group_id
                    ).where(
                        and_(
                            ActivityCoHost.activity_id == activity_id,
                            GroupMember.user_id == user_uuid,
                        )
                    )
                )
                if cohost_res.first():
                    is_authorized = True

            # Check if user has an approved join request
            if not is_authorized:
                from app.modules.participation.models import JoinRequest, RequestStatus
                from sqlalchemy import select, and_
                part_res = await db.execute(
                    select(JoinRequest.id).where(
                        and_(
                            JoinRequest.activity_id == activity_id,
                            JoinRequest.user_id == user_uuid,
                            JoinRequest.status == RequestStatus.approved,
                        )
                    )
                )
                if part_res.first():
                    is_authorized = True

            if not is_authorized:
                raise ForbiddenError("This activity is restricted to group members.")

    coords = await repository.get_coordinates_from_db(db, activity_id)
    if not coords:
        lat, lng = 0.0, 0.0
    else:
        lat, lng = coords

    # Obfuscate for non-host users
    is_host = user_id and str(activity.host_id) == user_id
    if not is_host:
        lat, lng = obfuscate_coordinates(lat, lng)

    # Only reveal private_description to host or approved participants
    revealed_private_desc = None
    if is_host:
        revealed_private_desc = activity.private_description
    elif user_id:
        from app.modules.participation.models import JoinRequest, RequestStatus
        from sqlalchemy import select, and_
        result = await db.execute(
            select(JoinRequest).where(and_(
                JoinRequest.activity_id == activity_id,
                JoinRequest.user_id == uuid.UUID(user_id),
                JoinRequest.status == RequestStatus.approved,
            ))
        )
        if result.unique().scalar_one_or_none():
            revealed_private_desc = activity.private_description

    # Fetch co-hosts
    from app.modules.groups.models import ActivityCoHost, Group
    from app.modules.activities.schemas import GroupInfo
    cohost_res = await db.execute(
        select(Group)
        .join(ActivityCoHost, ActivityCoHost.group_id == Group.id)
        .where(ActivityCoHost.activity_id == activity_id)
    )
    co_hosts_list = [
        GroupInfo(id=g.id, name=g.name, avatar_url=getattr(g, "avatar_url", None))
        for g in cohost_res.unique().scalars().all()
    ]

    return _activity_to_response(activity, lat, lng, private_description=revealed_private_desc, co_hosts=co_hosts_list)


async def update_activity(
    db: AsyncSession, activity_id: uuid.UUID, user_id: str, data: ActivityUpdate
) -> ActivityResponse:
    """Update an activity. Host-only, subject to temporal lock."""
    activity = await repository.get_by_id(db, activity_id)
    if not activity:
        raise NotFoundError("Activity not found.")

    if str(activity.host_id) != user_id:
        raise ForbiddenError("Only the host can edit this activity.")

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise ValidationError("No fields to update.")

    # Invariant: Sau khi attendance_finalized_at != NULL, không được thay đổi trophy_id hoặc chỉnh sửa hoạt động
    if getattr(activity, "attendance_finalized_at", None) is not None:
        if "trophy_id" in update_data:
            raise ConflictError("Hoạt động đã chốt điểm danh, không thể thay đổi Trophy.")
        raise ConflictError("Hoạt động đã chốt điểm danh, không thể chỉnh sửa.")

    # Temporal lock: cannot modify within 30 min of start
    now = datetime.now(timezone.utc)
    lock_threshold = activity.start_time - timedelta(minutes=TEMPORAL_LOCK_MINUTES)
    if hasattr(lock_threshold, 'tzinfo') and lock_threshold.tzinfo is None:
        lock_threshold = lock_threshold.replace(tzinfo=timezone.utc)
    if now >= lock_threshold:
        raise ValidationError(
            f"Cannot modify activity within {TEMPORAL_LOCK_MINUTES} minutes of start time."
        )

    if "group_id" in update_data and update_data["group_id"]:
        from app.modules.groups.repository import get_group_by_id
        target_group = await get_group_by_id(db, update_data["group_id"])
        if target_group and getattr(target_group, "status", "active") == "inactive":
            raise ValidationError("Nhóm này đã dừng hoạt động, không thể gắn hoạt động vào nhóm.")

    if "social_work_days" in update_data:
        from app.modules.users.models import User, UserRole
        from sqlalchemy import select
        user_result = await db.execute(select(User.role).where(User.id == uuid.UUID(user_id)))
        user_role = user_result.scalar_one_or_none()
        if user_role not in [UserRole.admin, UserRole.edu_org]:
            update_data.pop("social_work_days")

    if "trophy_id" in update_data:
        new_trophy_id = update_data.pop("trophy_id")
        if new_trophy_id:
            from app.modules.users.models import User, UserRole
            from app.modules.trophies.models import Trophy
            from sqlalchemy import select
            user_result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
            user_obj = user_result.scalar_one_or_none()
            user_role = user_obj.role.value if hasattr(user_obj.role, "value") else str(user_obj.role)
            if not user_obj or user_role not in [UserRole.admin.value, UserRole.edu_org.value]:
                raise ForbiddenError("Chỉ Ban Quản trị hoặc Tổ chức Giáo dục mới có thể gắn Trophy vào hoạt động.")
            trophy = await db.scalar(select(Trophy).where(Trophy.id == new_trophy_id))
            if trophy:
                trophy.activity_id = activity.id

    if not activity.check_in_code:
        import secrets
        activity.check_in_code = secrets.token_hex(4).upper()

    if "custom_form" in update_data:
        custom_form_data = update_data.pop("custom_form")
        from app.modules.forms.models import CustomForm, FormField, FieldType
        from sqlalchemy import select, delete, and_

        if custom_form_data:
            fields_data = custom_form_data.get("fields", [])
            for f in fields_data:
                f_type = f.get("field_type") if isinstance(f, dict) else getattr(f, "field_type", "text")
                if f_type == "boolean":
                    if isinstance(f, dict):
                        f["field_type"] = "checkbox"
                    else:
                        setattr(f, "field_type", "checkbox")

            has_required = any(
                f.get("is_required", True) if isinstance(f, dict) else getattr(f, "is_required", True)
                for f in fields_data
            )

            if activity.custom_form:
                activity.custom_form.title = custom_form_data.get("title")
                activity.custom_form.description = custom_form_data.get("description")
                await db.execute(
                    delete(FormField).where(FormField.form_id == activity.custom_form.id)
                )
                form_obj = activity.custom_form
            else:
                form_obj = CustomForm(
                    title=custom_form_data.get("title"),
                    description=custom_form_data.get("description"),
                )
                db.add(form_obj)
                await db.flush()
                activity.custom_form_id = form_obj.id
                activity.custom_form = form_obj

            for f_data in fields_data:
                label = f_data.get("label") if isinstance(f_data, dict) else f_data.label
                f_type_str = f_data.get("field_type") if isinstance(f_data, dict) else f_data.field_type
                f_type_val = FieldType(f_type_str.value if hasattr(f_type_str, "value") else str(f_type_str))
                is_req = f_data.get("is_required", True) if isinstance(f_data, dict) else f_data.is_required
                order = f_data.get("order", 0) if isinstance(f_data, dict) else f_data.order
                meta = f_data.get("meta_data") if isinstance(f_data, dict) else f_data.meta_data
                new_ff = FormField(
                    form_id=form_obj.id,
                    label=label,
                    field_type=f_type_val,
                    is_required=is_req,
                    order=order,
                    meta_data=meta,
                )
                db.add(new_ff)
            await db.flush()

            # Rule: If activity requires approval AND the updated form has required field(s),
            # cancel approved join requests (excluding host) so participants must re-submit form and request join again!
            new_require_approval = update_data.get("require_approval", activity.require_approval)
            if new_require_approval and has_required:
                from app.modules.participation.models import JoinRequest, RequestStatus
                from app.modules.notifications.repository import create_notification

                jr_stmt = select(JoinRequest).where(
                    and_(
                        JoinRequest.activity_id == activity.id,
                        JoinRequest.status.in_([RequestStatus.approved, RequestStatus.pending]),
                        JoinRequest.user_id != activity.host_id,
                    )
                )
                jr_result = await db.execute(jr_stmt)
                affected_requests = list(jr_result.scalars().all())

                approved_count = 0
                for req in affected_requests:
                    if req.status == RequestStatus.approved:
                        approved_count += 1
                    req.status = RequestStatus.cancelled

                    await create_notification(
                        db,
                        user_id=req.user_id,
                        actor_id=uuid.UUID(user_id),
                        type="activity_form_updated",
                        message=f"Hoạt động '{activity.title}' đã có sửa đổi về biểu mẫu (thêm trường bắt buộc). Phê duyệt tham gia của bạn đã được hủy, vui lòng điền lại biểu mẫu và gửi lại yêu cầu tham gia.",
                        activity_id=activity.id,
                        target_type="activity",
                        target_id=activity.id,
                        action_url=f"/activities/{activity.id}",
                    )

                if approved_count > 0:
                    activity.current_participants = max(1, activity.current_participants - approved_count)
        else:
            if activity.custom_form:
                await db.delete(activity.custom_form)
                activity.custom_form = None
                activity.custom_form_id = None

    # Handle location update
    if "location_name" in update_data and "meeting_location" not in update_data:
        update_data["meeting_location"] = update_data.pop("location_name")

    if "latitude" in update_data or "longitude" in update_data:
        coords = await repository.get_coordinates_from_db(db, activity_id)
        current_lat, current_lng = coords if coords else (0, 0)
        new_lat = update_data.pop("latitude", current_lat)
        new_lng = update_data.pop("longitude", current_lng)
        activity.marker_location = f"SRID=4326;POINT({new_lng} {new_lat})"

    if "title" in update_data or "description" in update_data:
        new_title = update_data.get("title", activity.title)
        new_desc = update_data.get("description", activity.description)
        embedding_text = f"{new_title}\n{new_desc or ''}"
        from app.modules.chat.embeddings import generate_embedding
        update_data["embedding"] = generate_embedding(embedding_text)

    activity = await repository.update(db, activity, update_data)

    coords = await repository.get_coordinates_from_db(db, activity_id)
    lat, lng = coords if coords else (0, 0)
    return _activity_to_response(activity, lat, lng)


async def delete_activity(
    db: AsyncSession, activity_id: uuid.UUID, user_id: str, user_role: str = "student"
) -> None:
    """Soft delete an activity. Host or admin."""
    activity = await repository.get_by_id(db, activity_id)
    if not activity:
        raise NotFoundError("Activity not found.")

    is_host = str(activity.host_id) == user_id
    is_admin = user_role in ("admin", "edu_org")

    if not is_host and not is_admin:
        raise ForbiddenError("Only the host or admin can delete this activity.")

    await repository.soft_delete(db, activity)


async def list_activities(
    db: AsyncSession,
    user_id: str,
    category: str | None = None,
    search: str | None = None,
    group_id: uuid.UUID | None = None,
    limit: int = 20,
    offset: int = 0,
    include_conflicts: bool = False,
    include_past: bool = False,
) -> ActivityListResponse:
    from app.modules.users.models import UserFollow
    from sqlalchemy import select
    from app.modules.calendar.service import get_detector_for_user

    # Fetch followed user IDs to prioritize their activities
    followed_user_ids_result = await db.execute(
        select(UserFollow.following_id).where(UserFollow.follower_id == uuid.UUID(user_id))
    )
    followed_user_ids = list(followed_user_ids_result.scalars().all())

    activities, total = await repository.list_active(
        db, user_id=uuid.UUID(user_id), category=category, search=search, group_id=group_id,
        limit=limit, offset=offset, followed_user_ids=followed_user_ids, include_past=include_past
    )

    # Batch load co-hosts for returned activities
    co_hosts_map: dict[uuid.UUID, list[GroupInfo]] = {}
    if activities:
        from app.modules.groups.models import ActivityCoHost, Group
        from app.modules.activities.schemas import GroupInfo
        act_ids = [a.id for a in activities]
        cohost_stmt = (
            select(ActivityCoHost.activity_id, Group)
            .join(Group, Group.id == ActivityCoHost.group_id)
            .where(ActivityCoHost.activity_id.in_(act_ids))
        )
        cohost_res = await db.execute(cohost_stmt)
        for aid, g in cohost_res.unique().all():
            if aid not in co_hosts_map:
                co_hosts_map[aid] = []
            co_hosts_map[aid].append(
                GroupInfo(id=g.id, name=g.name, avatar_url=getattr(g, "avatar_url", None))
            )

    detector = None
    if user_id:
        try:
            detector = await get_detector_for_user(db, uuid.UUID(user_id))
        except Exception:
            detector = None

    items = []
    for activity in activities:
        conflict = detector.check_conflict(activity.start_time, activity.end_time, exclude_activity_id=activity.id) if detector else None
        if not include_conflicts and conflict and conflict.has_conflict and conflict.level == "hard_conflict":
            continue

        coords = await repository.get_coordinates_from_db(db, activity.id)
        lat, lng = coords if coords else (0, 0)
        lat, lng = obfuscate_coordinates(lat, lng)  # Always obfuscate in listings
        items.append(_activity_to_response(activity, lat, lng, conflict_info=conflict, co_hosts=co_hosts_map.get(activity.id, [])))

    return ActivityListResponse(
        items=items, total=total, limit=limit, offset=offset, has_more=(offset + limit < total)
    )


async def get_my_activities(
    db: AsyncSession, user_id: str, status_filter: str | None = None, limit: int = 50, offset: int = 0
) -> ActivityListResponse:
    """List activities hosted by the current user (all past & upcoming)."""
    activities, total = await repository.list_hosted_activities(
        db, user_id=uuid.UUID(user_id), status_filter=status_filter, limit=limit, offset=offset
    )

    items = []
    for activity in activities:
        coords = await repository.get_coordinates_from_db(db, activity.id)
        lat, lng = coords if coords else (0, 0)
        items.append(_activity_to_response(activity, lat, lng))

    return ActivityListResponse(
        items=items, total=total, limit=limit, offset=offset, has_more=(offset + limit < total)
    )


async def discover_nearby(
    db: AsyncSession, query: NearbyQuery, user_id: str | None = None, include_conflicts: bool = False
) -> ActivityListResponse:
    """Find activities within radius using PostGIS spatial query."""
    # Ensure user_id is provided, otherwise we can't filter group visibility
    if not user_id:
        raise ValidationError("user_id is required for discover_nearby")

    from app.modules.users.models import UserFollow
    from sqlalchemy import select
    from app.modules.calendar.service import get_detector_for_user

    # Fetch followed user IDs to prioritize their activities
    followed_user_ids_result = await db.execute(
        select(UserFollow.following_id).where(UserFollow.follower_id == uuid.UUID(user_id))
    )
    followed_user_ids = list(followed_user_ids_result.scalars().all())

    results, total = await repository.find_within_radius(
        db,
        user_id=uuid.UUID(user_id),
        lat=query.lat,
        lng=query.lng,
        radius_meters=query.radius,
        category=query.category,
        search=query.search,
        free_to_join=query.free_to_join,
        days_ahead=query.days_ahead,
        is_ctxh=query.is_ctxh,
        has_trophy=query.has_trophy,
        sort_by=query.sort_by,
        exclude_my_activities=query.exclude_my_activities,
        limit=query.limit,
        offset=query.offset,
        followed_user_ids=followed_user_ids,
    )

    detector = None
    if user_id:
        try:
            detector = await get_detector_for_user(db, uuid.UUID(user_id))
        except Exception:
            detector = None

    items = []
    for activity, distance in results:
        conflict = detector.check_conflict(activity.start_time, activity.end_time, exclude_activity_id=activity.id) if detector else None
        if not include_conflicts and conflict and conflict.has_conflict:
            continue

        coords = await repository.get_coordinates_from_db(db, activity.id)
        lat, lng = coords if coords else (0, 0)

        # Obfuscate coordinates for non-hosts
        is_host = user_id and str(activity.host_id) == user_id
        if not is_host:
            lat, lng = obfuscate_coordinates(lat, lng)

        items.append(_activity_to_response(activity, lat, lng, distance=distance, conflict_info=conflict))

    return ActivityListResponse(
        items=items, total=total, limit=query.limit, offset=query.offset,
        has_more=(query.offset + query.limit < total),
    )


async def preview_reschedule(
    db: AsyncSession,
    activity_id: uuid.UUID,
    user_id: str,
    new_start_time: datetime,
    new_end_time: datetime,
):
    """Host previews how rescheduling will impact existing approved participants."""
    activity = await repository.get_by_id(db, activity_id)
    if not activity:
        raise NotFoundError("Activity not found.")
    if str(activity.host_id) != user_id:
        raise ForbiddenError("Only the host can preview rescheduling impact.")
    from app.modules.calendar.service import preview_reschedule_impact
    return await preview_reschedule_impact(db, activity_id, new_start_time, new_end_time)


async def get_joined_activities(
    db: AsyncSession, user_id: str, status_filter: str | None = None, limit: int = 50, offset: int = 0
) -> ActivityListResponse:
    """List activities joined by the current user."""
    activities, total, attendance_map, joined_at_map = await repository.list_joined_activities(
        db, user_id=uuid.UUID(user_id), status_filter=status_filter, limit=limit, offset=offset
    )

    items = []
    for activity in activities:
        coords = await repository.get_coordinates_from_db(db, activity.id)
        lat, lng = coords if coords else (0, 0)
        items.append(_activity_to_response(
            activity, lat, lng,
            attendance_confirmed=attendance_map.get(activity.id, False),
            joined_at=joined_at_map.get(activity.id),
        ))

    return ActivityListResponse(
        items=items, total=total, limit=limit, offset=offset, has_more=(offset + limit < total)
    )
