import uuid
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.modules.calendar import repository as cal_repo
from app.modules.calendar.models import UserBusySlot, RecurrenceType, UserVacationPeriod
from app.modules.calendar.schemas import (
    BusySlotCreate,
    BusySlotResponse,
    CalendarEventItem,
    ConflictDetail,
    ConflictInfo,
    ConflictedMemberInfo,
    ReschedulePreviewResponse,
)
from app.modules.activities.models import Activity
from app.modules.participation.models import JoinRequest, RequestStatus
from app.modules.users.models import User

try:
    from zoneinfo import ZoneInfo
    LOCAL_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
except Exception:
    LOCAL_TZ = timezone(timedelta(hours=7))


def intervals_overlap(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
    """
    Half-open interval [start, end) overlap predicate: max(start_a, start_b) < min(end_a, end_b).
    Guarantees adjacent intervals (e.g. 10:00-11:00 and 11:00-12:00) do NOT conflict.
    """
    return max(start_a, start_b) < min(end_a, end_b)


def time_intervals_overlap(start_a: time, end_a: time, start_b: time, end_b: time) -> bool:
    """Half-open interval [start, end) overlap predicate for time-of-day."""
    return max(start_a, start_b) < min(end_a, end_b)


class ConflictDetector:
    def __init__(
        self,
        busy_slots: list[UserBusySlot],
        vacations: list[UserVacationPeriod],
        approved_activities: list[Activity],
        hosted_activities: list[Activity],
        pending_requests: list[JoinRequest],
    ):
        self.busy_slots = busy_slots
        self.vacations = vacations
        self.approved_activities = approved_activities
        self.hosted_activities = hosted_activities
        self.pending_requests = pending_requests

    def check_conflict(
        self,
        act_start: datetime,
        act_end: datetime,
        exclude_activity_id: uuid.UUID | None = None,
    ) -> ConflictInfo:
        """
        Check if interval [act_start, act_end] conflicts with user's schedule.
        Returns ConflictInfo with level: 'none' | 'soft_conflict' | 'hard_conflict'.
        """
        # Ensure datetimes are timezone aware (UTC)
        if act_start.tzinfo is None:
            act_start = act_start.replace(tzinfo=timezone.utc)
        if act_end.tzinfo is None:
            act_end = act_end.replace(tzinfo=timezone.utc)

        # 1. Check Hosted Activities (Hard Block)
        for ha in self.hosted_activities:
            if exclude_activity_id and ha.id == exclude_activity_id:
                continue
            ha_start = ha.start_time if ha.start_time.tzinfo else ha.start_time.replace(tzinfo=timezone.utc)
            ha_end = ha.end_time if ha.end_time.tzinfo else ha.end_time.replace(tzinfo=timezone.utc)
            if intervals_overlap(ha_start, ha_end, act_start, act_end):
                return ConflictInfo(
                    has_conflict=True,
                    level="hard_conflict",
                    can_join=False,
                    warning_message=f"Bạn đang là Host của hoạt động '{ha.title}' trong cùng khung giờ.",
                    conflicting_with=ConflictDetail(
                        type="hosted_activity",
                        title=ha.title,
                        time_range=f"{ha_start.strftime('%H:%M %d/%m')} - {ha_end.strftime('%H:%M %d/%m')}",
                        target_id=str(ha.id),
                    ),
                )

        # 2. Check Approved Activities (Hard Conflict)
        for aa in self.approved_activities:
            if exclude_activity_id and aa.id == exclude_activity_id:
                continue
            aa_start = aa.start_time if aa.start_time.tzinfo else aa.start_time.replace(tzinfo=timezone.utc)
            aa_end = aa.end_time if aa.end_time.tzinfo else aa.end_time.replace(tzinfo=timezone.utc)
            if intervals_overlap(aa_start, aa_end, act_start, act_end):
                return ConflictInfo(
                    has_conflict=True,
                    level="hard_conflict",
                    can_join=False,
                    warning_message=f"Bạn đã được duyệt tham gia hoạt động '{aa.title}'.",
                    conflicting_with=ConflictDetail(
                        type="approved_activity",
                        title=aa.title,
                        time_range=f"{aa_start.strftime('%H:%M %d/%m')} - {aa_end.strftime('%H:%M %d/%m')}",
                        target_id=str(aa.id),
                    ),
                )

        # 3. Check One-off Busy Slots (Hard Conflict)
        for slot in self.busy_slots:
            if slot.recurrence != RecurrenceType.weekly.value and slot.start_datetime and slot.end_datetime:
                bs_start = slot.start_datetime if slot.start_datetime.tzinfo else slot.start_datetime.replace(tzinfo=timezone.utc)
                bs_end = slot.end_datetime if slot.end_datetime.tzinfo else slot.end_datetime.replace(tzinfo=timezone.utc)
                if intervals_overlap(bs_start, bs_end, act_start, act_end):
                    return ConflictInfo(
                        has_conflict=True,
                        level="hard_conflict",
                        can_join=False,
                        warning_message=f"Trùng lịch bận cá nhân: {slot.title}.",
                        conflicting_with=ConflictDetail(
                            type="busy_slot",
                            title=slot.title,
                            time_range=f"{bs_start.strftime('%H:%M %d/%m')} - {bs_end.strftime('%H:%M %d/%m')}",
                            target_id=str(slot.id),
                        ),
                    )

        # 4. Check Weekly Recurring Slots (Converted to User Local Time)
        local_start = act_start.astimezone(LOCAL_TZ)
        local_end = act_end.astimezone(LOCAL_TZ)
        act_local_date = local_start.date()
        act_dow = local_start.weekday()  # 0=Monday, 6=Sunday

        # Check vacation period
        is_in_vacation = any(v.start_date <= act_local_date <= v.end_date for v in self.vacations)

        if not is_in_vacation:
            for slot in self.busy_slots:
                if slot.recurrence == RecurrenceType.weekly.value and slot.day_of_week == act_dow:
                    # Check validity dates
                    if slot.valid_from and act_local_date < slot.valid_from:
                        continue
                    if slot.valid_until and act_local_date > slot.valid_until:
                        continue

                    # Check skip exceptions
                    exception_dates = {exc.skip_date for exc in slot.exceptions}
                    if act_local_date in exception_dates:
                        continue

                    # Overlap on time of day
                    if slot.start_time_of_day and slot.end_time_of_day:
                        if time_intervals_overlap(slot.start_time_of_day, slot.end_time_of_day, local_start.time(), local_end.time()):
                            time_str = f"{slot.start_time_of_day.strftime('%H:%M')} - {slot.end_time_of_day.strftime('%H:%M')}"
                            return ConflictInfo(
                                has_conflict=True,
                                level="hard_conflict",
                                can_join=False,
                                warning_message=f"Trùng lịch định kỳ: {slot.title} ({time_str}).",
                                conflicting_with=ConflictDetail(
                                    type="busy_slot",
                                    title=slot.title,
                                    time_range=time_str,
                                    target_id=str(slot.id),
                                ),
                            )

        # 5. Check Pending Join Requests (Soft Conflict - Smart Swap possible)
        for jr in self.pending_requests:
            if exclude_activity_id and jr.activity_id == exclude_activity_id:
                continue
            act = jr.activity
            if not act:
                continue
            p_start = act.start_time if act.start_time.tzinfo else act.start_time.replace(tzinfo=timezone.utc)
            p_end = act.end_time if act.end_time.tzinfo else act.end_time.replace(tzinfo=timezone.utc)
            if intervals_overlap(p_start, p_end, act_start, act_end):
                return ConflictInfo(
                    has_conflict=True,
                    level="soft_conflict",
                    can_join=True,
                    warning_message=f"Trùng thời gian với hoạt động '{act.title}' bạn đang chờ duyệt.",
                    conflicting_with=ConflictDetail(
                        type="pending_request",
                        title=act.title,
                        time_range=f"{p_start.strftime('%H:%M %d/%m')} - {p_end.strftime('%H:%M %d/%m')}",
                        target_id=str(act.id),
                    ),
                    swap_candidate={
                        "join_request_id": str(jr.id),
                        "activity_id": str(act.id),
                        "title": act.title,
                    },
                )

        return ConflictInfo(has_conflict=False, level="none", can_join=True)



async def get_detector_for_user(db: AsyncSession, user_id: uuid.UUID) -> ConflictDetector:
    """Load all relevant schedules for user and instantiate ConflictDetector."""
    busy_slots = await cal_repo.get_user_busy_slots(db, user_id)
    vacations = await cal_repo.get_user_vacations(db, user_id)
    approved_acts = await cal_repo.get_user_approved_activities(db, user_id)
    hosted_acts = await cal_repo.get_user_hosted_activities(db, user_id)
    pending_reqs = await cal_repo.get_user_pending_join_requests(db, user_id)

    return ConflictDetector(
        busy_slots=busy_slots,
        vacations=vacations,
        approved_activities=approved_acts,
        hosted_activities=hosted_acts,
        pending_requests=pending_reqs,
    )


async def get_user_calendar_events(
    db: AsyncSession, user_id: uuid.UUID, start_date: date, end_date: date
) -> list[CalendarEventItem]:
    """
    Aggregate all calendar events for user in the given date window:
    - Expanded weekly recurring busy slots
    - One-off busy slots
    - Approved joined activities
    - Hosted activities
    """
    events: list[CalendarEventItem] = []
    start_dt = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=LOCAL_TZ)
    end_dt = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=LOCAL_TZ)

    # 1. Busy slots
    busy_slots = await cal_repo.get_user_busy_slots(db, user_id)
    for slot in busy_slots:
        if slot.recurrence == RecurrenceType.weekly.value and slot.day_of_week is not None:
            # Expand weekly instances between start_date and end_date
            curr_date = start_date
            exc_dates = {exc.skip_date for exc in slot.exceptions}
            while curr_date <= end_date:
                if curr_date.weekday() == slot.day_of_week:
                    if (not slot.valid_from or curr_date >= slot.valid_from) and (
                        not slot.valid_until or curr_date <= slot.valid_until
                    ):
                        if curr_date not in exc_dates and slot.start_time_of_day and slot.end_time_of_day:
                            inst_start = datetime.combine(curr_date, slot.start_time_of_day).replace(tzinfo=LOCAL_TZ)
                            inst_end = datetime.combine(curr_date, slot.end_time_of_day).replace(tzinfo=LOCAL_TZ)
                            events.append(
                                CalendarEventItem(
                                    id=f"busy_weekly_{slot.id}_{curr_date.isoformat()}",
                                    title=slot.title,
                                    start_time=inst_start,
                                    end_time=inst_end,
                                    event_type="busy_slot",
                                    is_recurring=True,
                                    color_tag="busy",
                                )
                            )
                curr_date += timedelta(days=1)
        elif slot.start_datetime and slot.end_datetime:
            # One-off slot
            if slot.end_datetime >= start_dt and slot.start_datetime <= end_dt:
                events.append(
                    CalendarEventItem(
                        id=f"busy_oneoff_{slot.id}",
                        title=slot.title,
                        start_time=slot.start_datetime,
                        end_time=slot.end_datetime,
                        event_type="busy_slot",
                        is_recurring=False,
                        color_tag="busy",
                    )
                )

    # 2. Approved joined activities
    approved = await cal_repo.get_user_approved_activities(db, user_id, start_time=start_dt, end_time=end_dt)
    for act in approved:
        events.append(
            CalendarEventItem(
                id=f"act_joined_{act.id}",
                title=act.title,
                start_time=act.start_time,
                end_time=act.end_time,
                event_type="activity_joined",
                activity_id=act.id,
                category=act.category,
                meeting_location=getattr(act, 'meeting_location', None) or act.location_name,
                location_name=getattr(act, 'meeting_location', None) or act.location_name,
                is_recurring=False,
                color_tag="joined",
            )
        )

    # 3. Hosted activities
    hosted = await cal_repo.get_user_hosted_activities(db, user_id, start_time=start_dt, end_time=end_dt)
    for act in hosted:
        events.append(
            CalendarEventItem(
                id=f"act_hosted_{act.id}",
                title=f"[Host] {act.title}",
                start_time=act.start_time,
                end_time=act.end_time,
                event_type="activity_hosted",
                activity_id=act.id,
                category=act.category,
                meeting_location=getattr(act, 'meeting_location', None) or act.location_name,
                location_name=getattr(act, 'meeting_location', None) or act.location_name,
                is_recurring=False,
                color_tag="hosted",
            )
        )

    events.sort(key=lambda e: e.start_time)
    return events


async def create_busy_slot(db: AsyncSession, user_id: uuid.UUID, data: BusySlotCreate) -> BusySlotResponse:
    slot = UserBusySlot(
        user_id=user_id,
        title=data.title,
        recurrence=data.recurrence,
        start_datetime=data.start_datetime,
        end_datetime=data.end_datetime,
        day_of_week=data.day_of_week,
        start_time_of_day=data.start_time_of_day,
        end_time_of_day=data.end_time_of_day,
        valid_from=data.valid_from,
        valid_until=data.valid_until,
    )
    saved = await cal_repo.create_busy_slot(db, slot)
    return BusySlotResponse(
        id=saved.id,
        user_id=saved.user_id,
        title=saved.title,
        recurrence=saved.recurrence,
        start_datetime=saved.start_datetime,
        end_datetime=saved.end_datetime,
        day_of_week=saved.day_of_week,
        start_time_of_day=saved.start_time_of_day,
        end_time_of_day=saved.end_time_of_day,
        valid_from=saved.valid_from,
        valid_until=saved.valid_until,
        exception_dates=[e.skip_date for e in saved.exceptions],
    )


async def delete_busy_slot(db: AsyncSession, user_id: uuid.UUID, slot_id: uuid.UUID) -> None:
    slot = await cal_repo.get_busy_slot_by_id(db, slot_id, user_id)
    if slot:
        await cal_repo.delete_busy_slot(db, slot)


async def preview_reschedule_impact(
    db: AsyncSession,
    activity_id: uuid.UUID,
    new_start_time: datetime,
    new_end_time: datetime,
) -> ReschedulePreviewResponse:
    """
    Host impact assessment: scans all approved participants' availability for new time window.
    Protects participant privacy by not revealing private busy slot titles.
    Guarantees:
    - 0 participants returns free_percentage = 100 and safe_to_reschedule = True (no ZeroDivisionError).
    - Unique user deduplication so multiple conflicts per participant count as 1 conflicted member.
    - Standardized privacy DTO (reason_code, reason_label).
    """
    # Get all approved join requests
    stmt = (
        select(JoinRequest)
        .where(
            JoinRequest.activity_id == activity_id,
            JoinRequest.status == RequestStatus.approved,
        )
        .options(selectinload(JoinRequest.user))
    )
    result = await db.execute(stmt)
    approved_reqs = list(result.scalars().all())

    total = len(approved_reqs)
    if total == 0:
        return ReschedulePreviewResponse(
            total_participants=0,
            conflicted_count=0,
            safe_to_reschedule=True,
            free_percentage=100,
            conflicted_members=[],
        )

    conflicted_list: list[ConflictedMemberInfo] = []
    seen_user_ids: set[uuid.UUID] = set()

    for jr in approved_reqs:
        if jr.user_id in seen_user_ids:
            continue

        detector = await get_detector_for_user(db, jr.user_id)
        # Exclude this activity itself so it doesn't self-conflict
        conflict = detector.check_conflict(new_start_time, new_end_time, exclude_activity_id=activity_id)
        if conflict.has_conflict and conflict.level == "hard_conflict":
            seen_user_ids.add(jr.user_id)
            # Sanitize reason for privacy
            reason_code = "personal_busy"
            reason_label = "Trùng lịch bận cá nhân"
            c_type = "busy_slot"

            if conflict.conflicting_with:
                if conflict.conflicting_with.type in ("approved_activity", "hosted_activity"):
                    reason_code = "university_activity"
                    reason_label = "Trùng hoạt động khác trên trường"
                    c_type = "other_activity"
                elif "định kỳ" in (conflict.warning_message or ""):
                    reason_code = "recurring_schedule"
                    reason_label = "Trùng lịch học cố định"
                    c_type = "busy_slot"

            user_name = jr.user.full_name or jr.user.username if jr.user else "Thành viên"
            conflicted_list.append(
                ConflictedMemberInfo(
                    user_id=str(jr.user_id),
                    full_name=user_name,
                    reason_code=reason_code,
                    reason_label=reason_label,
                    conflict_type=c_type,
                    reason=reason_label,
                )
            )

    conflicted_count = len(conflicted_list)
    free_pct = 100 if total == 0 else int(((total - conflicted_count) / total) * 100)

    return ReschedulePreviewResponse(
        total_participants=total,
        conflicted_count=conflicted_count,
        safe_to_reschedule=conflicted_count == 0,
        free_percentage=free_pct,
        conflicted_members=conflicted_list,
    )

