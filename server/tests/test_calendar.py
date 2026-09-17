import uuid
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
import pytest

from app.modules.calendar.models import UserBusySlot, BusySlotException, UserVacationPeriod, RecurrenceType
from app.modules.calendar.service import ConflictDetector, LOCAL_TZ
from app.modules.activities.models import Activity
from app.modules.participation.models import JoinRequest, RequestStatus


def test_one_off_busy_slot_overlap():
    user_id = uuid.uuid4()
    # User is busy from 14:00 to 16:00 on 2026-09-20
    busy_start = datetime(2026, 9, 20, 14, 0, tzinfo=timezone.utc)
    busy_end = datetime(2026, 9, 20, 16, 0, tzinfo=timezone.utc)
    
    slot = UserBusySlot(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Lịch học thêm Toán",
        recurrence="none",
        start_datetime=busy_start,
        end_datetime=busy_end,
    )
    detector = ConflictDetector(
        busy_slots=[slot],
        vacations=[],
        approved_activities=[],
        hosted_activities=[],
        pending_requests=[],
    )

    # Overlapping activity: 15:00 - 17:00
    act_start = datetime(2026, 9, 20, 15, 0, tzinfo=timezone.utc)
    act_end = datetime(2026, 9, 20, 17, 0, tzinfo=timezone.utc)
    conflict = detector.check_conflict(act_start, act_end)
    assert conflict.has_conflict is True
    assert conflict.level == "hard_conflict"
    assert conflict.can_join is False
    assert "Toán" in conflict.warning_message

    # Non-overlapping activity: 16:30 - 18:00
    free_start = datetime(2026, 9, 20, 16, 30, tzinfo=timezone.utc)
    free_end = datetime(2026, 9, 20, 18, 0, tzinfo=timezone.utc)
    no_conflict = detector.check_conflict(free_start, free_end)
    assert no_conflict.has_conflict is False
    assert no_conflict.level == "none"


def test_weekly_recurrence_and_boundary():
    user_id = uuid.uuid4()
    # Weekly on Tuesday (weekday = 1), 08:00 - 11:30 VN time
    # Valid from 2026-09-01 to 2026-09-22 (ends on Tuesday 22nd)
    slot = UserBusySlot(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Thể dục sáng Thứ 3",
        recurrence="weekly",
        day_of_week=1, # Tuesday
        start_time_of_day=time(8, 0),
        end_time_of_day=time(11, 30),
        valid_from=date(2026, 9, 1),
        valid_until=date(2026, 9, 22),
    )
    # Add an exception for 2026-09-15 (Holiday/Skip day)
    exc = BusySlotException(
        id=uuid.uuid4(),
        busy_slot_id=slot.id,
        skip_date=date(2026, 9, 15),
    )
    slot.exceptions = [exc]

    detector = ConflictDetector(
        busy_slots=[slot],
        vacations=[],
        approved_activities=[],
        hosted_activities=[],
        pending_requests=[],
    )

    # 1. Tuesday 2026-09-08 at 09:00 - 10:30 VN time -> Should conflict!
    tue_1_start = datetime(2026, 9, 8, 9, 0, tzinfo=LOCAL_TZ).astimezone(timezone.utc)
    tue_1_end = datetime(2026, 9, 8, 10, 30, tzinfo=LOCAL_TZ).astimezone(timezone.utc)
    c1 = detector.check_conflict(tue_1_start, tue_1_end)
    assert c1.has_conflict is True
    assert c1.level == "hard_conflict"

    # 2. Tuesday 2026-09-15 (Skipped exception) -> Should NOT conflict!
    tue_skip_start = datetime(2026, 9, 15, 9, 0, tzinfo=LOCAL_TZ).astimezone(timezone.utc)
    tue_skip_end = datetime(2026, 9, 15, 10, 30, tzinfo=LOCAL_TZ).astimezone(timezone.utc)
    c_skip = detector.check_conflict(tue_skip_start, tue_skip_end)
    assert c_skip.has_conflict is False

    # 3. Tuesday 2026-09-29 (After valid_until) -> Course finished, should NOT conflict!
    tue_future_start = datetime(2026, 9, 29, 9, 0, tzinfo=LOCAL_TZ).astimezone(timezone.utc)
    tue_future_end = datetime(2026, 9, 29, 10, 30, tzinfo=LOCAL_TZ).astimezone(timezone.utc)
    c_future = detector.check_conflict(tue_future_start, tue_future_end)
    assert c_future.has_conflict is False


def test_soft_conflict_pending_request_and_smart_swap():
    user_id = uuid.uuid4()
    act_id = uuid.uuid4()
    p_act = Activity(
        id=act_id,
        title="Chiến dịch Tiếp Sức Mùa Thi",
        start_time=datetime(2026, 9, 20, 8, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc),
        current_participants=5,
        max_participants=20,
    )
    jr = JoinRequest(
        id=uuid.uuid4(),
        activity_id=act_id,
        user_id=user_id,
        status=RequestStatus.pending,
        activity=p_act,
    )

    detector = ConflictDetector(
        busy_slots=[],
        vacations=[],
        approved_activities=[],
        hosted_activities=[],
        pending_requests=[jr],
    )

    # Check another activity at the same time: 09:00 - 11:00
    new_act_start = datetime(2026, 9, 20, 9, 0, tzinfo=timezone.utc)
    new_act_end = datetime(2026, 9, 20, 11, 0, tzinfo=timezone.utc)
    conflict = detector.check_conflict(new_act_start, new_act_end)
    
    assert conflict.has_conflict is True
    assert conflict.level == "soft_conflict"
    assert conflict.can_join is True
    assert conflict.swap_candidate is not None
    assert conflict.swap_candidate["join_request_id"] == str(jr.id)
    assert "Tiếp Sức Mùa Thi" in conflict.warning_message


def test_adjacent_time_boundary_no_conflict():
    """Half-open interval [start, end) ensures adjacent slots do NOT conflict."""
    user_id = uuid.uuid4()
    # Slot 1: 10:00 - 11:00 UTC
    slot1_start = datetime(2026, 9, 20, 10, 0, tzinfo=timezone.utc)
    slot1_end = datetime(2026, 9, 20, 11, 0, tzinfo=timezone.utc)

    slot = UserBusySlot(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Lịch họp lab 10h-11h",
        recurrence="none",
        start_datetime=slot1_start,
        end_datetime=slot1_end,
    )
    detector = ConflictDetector(
        busy_slots=[slot],
        vacations=[],
        approved_activities=[],
        hosted_activities=[],
        pending_requests=[],
    )

    # Activity starts exactly when slot ends: 11:00 - 12:00 UTC -> NO conflict
    act_start = datetime(2026, 9, 20, 11, 0, tzinfo=timezone.utc)
    act_end = datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc)
    c1 = detector.check_conflict(act_start, act_end)
    assert c1.has_conflict is False
    assert c1.level == "none"

    # Activity ends exactly when slot starts: 09:00 - 10:00 UTC -> NO conflict
    act_before_start = datetime(2026, 9, 20, 9, 0, tzinfo=timezone.utc)
    act_before_end = datetime(2026, 9, 20, 10, 0, tzinfo=timezone.utc)
    c2 = detector.check_conflict(act_before_start, act_before_end)
    assert c2.has_conflict is False
    assert c2.level == "none"


def test_weekly_valid_from_and_valid_until_boundaries():
    """Verify recurrence does not trigger before valid_from or after valid_until."""
    user_id = uuid.uuid4()
    # Weekly on Tuesday (day_of_week = 1), 08:00 - 11:30 VN time
    # Valid strictly from 2026-09-08 (Tuesday) to 2026-09-22 (Tuesday)
    slot = UserBusySlot(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Thực hành Mạng máy tính",
        recurrence="weekly",
        day_of_week=1,
        start_time_of_day=time(8, 0),
        end_time_of_day=time(11, 30),
        valid_from=date(2026, 9, 8),
        valid_until=date(2026, 9, 22),
    )
    detector = ConflictDetector(
        busy_slots=[slot],
        vacations=[],
        approved_activities=[],
        hosted_activities=[],
        pending_requests=[],
    )

    # 1. Tuesday 2026-09-01 (Before valid_from) -> MUST NOT conflict
    tue_before = datetime(2026, 9, 1, 9, 0, tzinfo=LOCAL_TZ).astimezone(timezone.utc)
    tue_before_end = datetime(2026, 9, 1, 10, 30, tzinfo=LOCAL_TZ).astimezone(timezone.utc)
    c_before = detector.check_conflict(tue_before, tue_before_end)
    assert c_before.has_conflict is False

    # 2. Tuesday 2026-09-08 (Exactly valid_from) -> MUST conflict
    tue_start = datetime(2026, 9, 8, 9, 0, tzinfo=LOCAL_TZ).astimezone(timezone.utc)
    tue_start_end = datetime(2026, 9, 8, 10, 30, tzinfo=LOCAL_TZ).astimezone(timezone.utc)
    c_start = detector.check_conflict(tue_start, tue_start_end)
    assert c_start.has_conflict is True
    assert c_start.level == "hard_conflict"

    # 3. Tuesday 2026-09-22 (Exactly valid_until) -> MUST conflict
    tue_until = datetime(2026, 9, 22, 9, 0, tzinfo=LOCAL_TZ).astimezone(timezone.utc)
    tue_until_end = datetime(2026, 9, 22, 10, 30, tzinfo=LOCAL_TZ).astimezone(timezone.utc)
    c_until = detector.check_conflict(tue_until, tue_until_end)
    assert c_until.has_conflict is True
    assert c_until.level == "hard_conflict"

    # 4. Tuesday 2026-09-29 (After valid_until) -> MUST NOT conflict
    tue_after = datetime(2026, 9, 29, 9, 0, tzinfo=LOCAL_TZ).astimezone(timezone.utc)
    tue_after_end = datetime(2026, 9, 29, 10, 30, tzinfo=LOCAL_TZ).astimezone(timezone.utc)
    c_after = detector.check_conflict(tue_after, tue_after_end)
    assert c_after.has_conflict is False


def test_vacation_suppresses_weekly_recurrence():
    """User on vacation period has all weekly recurring commitments automatically suspended."""
    user_id = uuid.uuid4()
    slot = UserBusySlot(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Lịch sinh hoạt CLB thứ 5",
        recurrence="weekly",
        day_of_week=3,  # Thursday
        start_time_of_day=time(18, 0),
        end_time_of_day=time(20, 0),
    )
    # Vacation period from 2026-09-15 to 2026-09-20 (covers Thursday 2026-09-17)
    vacation = UserVacationPeriod(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Nghỉ lễ Trung thu",
        start_date=date(2026, 9, 15),
        end_date=date(2026, 9, 20),
    )

    detector = ConflictDetector(
        busy_slots=[slot],
        vacations=[vacation],
        approved_activities=[],
        hosted_activities=[],
        pending_requests=[],
    )

    # Thursday 2026-09-17 (Inside vacation) -> Conflict suspended
    thu_vacation_start = datetime(2026, 9, 17, 18, 30, tzinfo=LOCAL_TZ).astimezone(timezone.utc)
    thu_vacation_end = datetime(2026, 9, 17, 19, 30, tzinfo=LOCAL_TZ).astimezone(timezone.utc)
    c_vacation = detector.check_conflict(thu_vacation_start, thu_vacation_end)
    assert c_vacation.has_conflict is False

    # Thursday 2026-09-24 (After vacation) -> Conflict re-engages
    thu_after_start = datetime(2026, 9, 24, 18, 30, tzinfo=LOCAL_TZ).astimezone(timezone.utc)
    thu_after_end = datetime(2026, 9, 24, 19, 30, tzinfo=LOCAL_TZ).astimezone(timezone.utc)
    c_after = detector.check_conflict(thu_after_start, thu_after_end)
    assert c_after.has_conflict is True
    assert c_after.level == "hard_conflict"


def test_hosted_activity_hard_conflict():
    """Being host of an activity locks that time slot as a non-joinable hard conflict."""
    user_id = uuid.uuid4()
    hosted_act = Activity(
        id=uuid.uuid4(),
        title="Tọa đàm AI Trong Y Tế",
        host_id=user_id,
        start_time=datetime(2026, 9, 25, 14, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 9, 25, 17, 0, tzinfo=timezone.utc),
    )

    detector = ConflictDetector(
        busy_slots=[],
        vacations=[],
        approved_activities=[],
        hosted_activities=[hosted_act],
        pending_requests=[],
    )

    # Check joining another activity: 15:00 - 16:30
    check_start = datetime(2026, 9, 25, 15, 0, tzinfo=timezone.utc)
    check_end = datetime(2026, 9, 25, 16, 30, tzinfo=timezone.utc)
    conflict = detector.check_conflict(check_start, check_end)
    assert conflict.has_conflict is True
    assert conflict.level == "hard_conflict"
    assert conflict.can_join is False
    assert "Host" in conflict.warning_message
    assert conflict.conflicting_with.type == "hosted_activity"


def test_intervals_overlap_primitive():
    from app.modules.calendar.service import intervals_overlap, time_intervals_overlap

    t1 = datetime(2026, 9, 20, 10, 0)
    t2 = datetime(2026, 9, 20, 11, 0)
    t3 = datetime(2026, 9, 20, 12, 0)

    # Adjacent: [t1, t2) and [t2, t3) -> False
    assert intervals_overlap(t1, t2, t2, t3) is False
    assert intervals_overlap(t2, t3, t1, t2) is False

    # Overlapping: [t1, t3) and [t2, t3) -> True
    assert intervals_overlap(t1, t3, t2, t3) is True

    # Time of day adjacent: 08:00-10:00 vs 10:00-12:00 -> False
    assert time_intervals_overlap(time(8, 0), time(10, 0), time(10, 0), time(12, 0)) is False
    # Time of day overlap: 08:00-11:00 vs 10:00-12:00 -> True
    assert time_intervals_overlap(time(8, 0), time(11, 0), time(10, 0), time(12, 0)) is True


def test_reschedule_preview_response_model():
    from app.modules.calendar.schemas import ReschedulePreviewResponse, ConflictedMemberInfo

    # 1. Zero participants case
    zero_resp = ReschedulePreviewResponse(
        total_participants=0,
        conflicted_count=0,
        safe_to_reschedule=True,
        free_percentage=100,
        conflicted_members=[],
    )
    assert zero_resp.safe_to_reschedule is True
    assert zero_resp.free_percentage == 100

    # 2. Conflicted member with privacy DTO
    info = ConflictedMemberInfo(
        user_id="user-123",
        full_name="Nguyễn Văn A",
        reason_code="personal_busy",
        reason_label="Trùng lịch bận cá nhân",
    )
    assert info.reason_code == "personal_busy"
    assert info.reason_label == "Trùng lịch bận cá nhân"
    # Ensure raw title is NOT present in schema
    assert not hasattr(info, "raw_title")
    assert not hasattr(info, "event_title")


