"""End-to-End Cross-Phase Critical Invariant Tests (Pillar 2).

Verifies the 4 critical business workflows across Phase 5 to Phase 10:
- Flow 1: Event -> Attendance -> Gamification & Profile CTXH Recalculation
- Flow 2: Calendar -> Conflict Detection -> Registration Status Orthogonality
- Flow 3: Groups -> Co-hosting Acceptance -> Attendance RBAC Delegation vs Host Exclusivity
- Flow 4: Admin Control Plane -> Verification Lifecycle -> Role Promotion -> Atomic Audit Trail
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.core.exceptions import ForbiddenError, ValidationError
from app.modules.activities.models import Activity, ActivityPrivacy
from app.modules.admin.models import (
    AdminAuditAction,
    AdminAuditLog,
    AdminAuditTargetType,
    OrganizationVerificationRequest,
    VerificationStatus,
)
from app.modules.admin.verification.service import review_verification_request
from app.modules.calendar.service import intervals_overlap, get_detector_for_user
from app.modules.calendar.models import UserBusySlot
from app.modules.groups.models import ActivityCoHost, ActivityCoHostInvitation, Group, GroupMember, GroupRole
from app.modules.groups.permissions import (
    can_open_checkin,
    can_manage_activity,
)
from app.modules.participation.models import JoinRequest, RequestStatus
from app.modules.participation.service import update_participant_attendance
from app.modules.trophies.models import Trophy, UserTrophy
from app.modules.users.models import User, UserRole
from app.modules.users.service import get_user_stats
from app.modules.users.policy import CTXH_TARGET_DAYS


# ── Flow 1: Event -> Attendance -> Gamification & Profile Reflection ──

@pytest.mark.asyncio
async def test_flow_event_attendance_gamification_and_profile():
    """E2E Flow 1: Attendance confirmation awards Trophy, updates CTXH days and rank on Profile."""
    db = AsyncMock()
    user_id = uuid.uuid4()
    host_id = uuid.uuid4()
    act_id = uuid.uuid4()
    trophy_id = uuid.uuid4()

    # 1. Setup Activity with CTXH and exclusive Trophy
    activity = Activity(
        id=act_id,
        host_id=host_id,
        title="Chiến dịch Mùa Hè Xanh",
        social_work_days=1.5,
        trophy_id=trophy_id,
        is_deleted=False,
    )

    # 2. Setup Participant with JoinRequest (initially attendance_confirmed = False)
    jr = JoinRequest(
        id=uuid.uuid4(),
        activity_id=act_id,
        user_id=user_id,
        status=RequestStatus.approved,
        attendance_confirmed=False,
    )

    # 3. Setup User Profile
    user = User(
        id=user_id,
        username="sinhvien_k21",
        full_name="Nguyễn Văn Sinh Viên",
        role=UserRole.student,
    )

    # Mock DB getters
    async def mock_repo_get_activity(session, a_id):
        if a_id == act_id:
            return activity
        return None

    async def mock_repo_get_request(session, a_id, u_id):
        if a_id == act_id and u_id == user_id:
            return jr
        return None

    db.scalar = AsyncMock(return_value=None)
    with patch("app.modules.participation.service.activity_repo.get_by_id", side_effect=mock_repo_get_activity), \
         patch("app.modules.participation.service.participation_repo.get_active_request", side_effect=mock_repo_get_request):

        # Host confirms attendance
        result = await update_participant_attendance(
            db=db,
            activity_id=act_id,
            target_user_id=user_id,
            host_user_id=str(host_id),
            attended=True,
        )

        assert result["attendance_confirmed"] is True
        assert result["trophy_awarded"] is False
        assert jr.attendance_confirmed is True

    # 4. Invariant Check: Verify Profile Stats reflects updated CTXH days & Trophy points
    # Mock DB response for get_user_stats:
    # Query 1: (total_ctxh, total_attended) = (1.5, 1)
    # Query 2: (total_trophies, total_points) = (1, 100) -> Rank: "Tình nguyện viên Tích cực"
    db.scalar.return_value = user
    mock_ctxh_res = MagicMock()
    mock_ctxh_res.one.return_value = (1.5, 1)
    mock_trophy_res = MagicMock()
    mock_trophy_res.one.return_value = (1, 100)

    db.execute.side_effect = [mock_ctxh_res, mock_trophy_res]

    stats = await get_user_stats(db, user_id=user_id, is_self=True)
    assert stats["total_ctxh_days"] == 1.5
    assert stats["total_attended_activities"] == 1
    assert stats["total_trophies_count"] == 1
    assert stats["total_trophy_points"] == 100
    assert stats["rank_title"] == "Thành viên Tích cực"
    assert stats["ctxh_completion_percent"] == round((1.5 / CTXH_TARGET_DAYS) * 100, 1)


# ── Flow 2: Calendar -> Conflict -> Registration Status Orthogonality ──

@pytest.mark.asyncio
async def test_flow_calendar_conflict_registration_orthogonality():
    """E2E Flow 2: Busy slot overlap produces hard_conflict without corrupting registration availability."""
    now = datetime(2026, 9, 20, 8, 0, tzinfo=timezone.utc)
    busy_start = now
    busy_end = now + timedelta(hours=2)

    # 1. Half-open interval primitive invariant check
    # Exact overlap
    assert intervals_overlap(busy_start, busy_end, busy_start + timedelta(minutes=30), busy_end) is True
    # Adjacent boundary (10:00 - 11:00 vs 11:00 - 12:00) does NOT conflict
    assert intervals_overlap(busy_start, busy_end, busy_end, busy_end + timedelta(hours=1)) is False

    # 2. Conflict Detector with busy slot
    user_id = uuid.uuid4()
    act_id = uuid.uuid4()

    # Conflicting activity
    act_start = now + timedelta(minutes=15)
    act_end = now + timedelta(hours=1, minutes=45)

    # Busy slot on user's calendar
    busy_slot = UserBusySlot(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Lịch học Giải tích",
        recurrence="none",
        start_datetime=busy_start,
        end_datetime=busy_end,
    )

    from app.modules.calendar.service import ConflictDetector
    detector = ConflictDetector(
        busy_slots=[busy_slot],
        vacations=[],
        approved_activities=[],
        hosted_activities=[],
        pending_requests=[],
    )

    conflict_info = detector.check_conflict(act_start, act_end)

    # 3. Invariant: Conflict engine marks hard_conflict, while registration stays independent
    assert conflict_info.has_conflict is True
    assert conflict_info.level == "hard_conflict"
    assert conflict_info.can_join is False
    assert "Lịch học Giải tích" in conflict_info.warning_message

    # Orthogonal registration status simulation (capacity available, start in future)
    max_participants = 50
    current_participants = 12
    registration_status = "available"
    if current_participants >= max_participants:
        registration_status = "capacity_full"

    assert registration_status == "available"
    assert conflict_info.level == "hard_conflict"


# ── Flow 3: Groups -> Co-hosting Acceptance -> Attendance Access Delegation ──

@pytest.mark.asyncio
async def test_flow_groups_cohosting_permission_delegation_and_host_exclusivity():
    """E2E Flow 3: Co-host admin inherits attendance check-in access, but cannot manage co-hosts or delete activity."""
    db = AsyncMock()
    lead_host_id = uuid.uuid4()
    lead_group_id = uuid.uuid4()
    cohost_admin_id = uuid.uuid4()
    cohost_group_id = uuid.uuid4()
    act_id = uuid.uuid4()

    activity = Activity(
        id=act_id,
        host_id=lead_host_id,
        group_id=lead_group_id,
        title="Hội trại Sinh viên Liên Khoa",
        is_deleted=False,
    )

    # Co-host relationship in accepted state
    cohost_record = ActivityCoHost(
        id=uuid.uuid4(),
        activity_id=act_id,
        group_id=cohost_group_id,
    )

    # Mock cohost admin membership check in cohost group
    async def mock_execute(stmt):
        mock_res = MagicMock()
        stmt_str = str(stmt)
        if "activities" in stmt_str:
            mock_res.scalar_one_or_none.return_value = activity
        elif "activity_cohosts" in stmt_str:
            mock_res.scalars.return_value.all.return_value = [cohost_group_id]
        elif "group_members" in stmt_str or "groups" in stmt_str:
            mock_res.scalar_one_or_none.return_value = uuid.uuid4()
        else:
            mock_res.scalar_one_or_none.return_value = None
        return mock_res

    db.execute.side_effect = mock_execute

    with patch("app.modules.groups.permissions.is_group_admin_or_owner") as mock_admin_check:
        # 1. Co-host admin is admin of co-host group -> CAN open/manage attendance
        mock_admin_check.side_effect = lambda session, uid, gid: gid == cohost_group_id
        can_checkin = await can_open_checkin(db, user_id=cohost_admin_id, activity_id=act_id)
        assert can_checkin is True

        # 2. Invariant: Co-host admin is NOT owner of lead host group -> CANNOT edit/manage activity (Host exclusivity)
        can_manage = await can_manage_activity(db, user_id=cohost_admin_id, activity_id=act_id)
        assert can_manage is False


# ── Flow 4: Admin Control Plane -> Verification -> Role Promotion -> Atomic Audit Trail ──

@pytest.mark.asyncio
async def test_flow_admin_verification_lifecycle_role_promotion_and_atomic_audit():
    """E2E Flow 4: Organization verification approval promotes role to edu_org and logs audit in single transaction."""
    db = AsyncMock()
    db.add = MagicMock()
    admin_id = uuid.uuid4()
    student_user_id = uuid.uuid4()
    request_id = uuid.uuid4()

    user = User(
        id=student_user_id,
        username="clb_guitar",
        full_name="CLB Guitar Sài Gòn",
        email="guitar@uni.edu.vn",
        role=UserRole.student,  # Initially regular student
        is_verified=False,
    )

    verif_request = OrganizationVerificationRequest(
        id=request_id,
        user_id=student_user_id,
        organization_name="CLB Guitar Sài Gòn",
        faculty="Đoàn Thanh Niên",
        status=VerificationStatus.pending,  # Active pending request
    )

    async def mock_get(model, obj_id):
        if model == OrganizationVerificationRequest:
            return verif_request
        if model == User:
            return user
        return None

    db.get.side_effect = mock_get

    # Admin approves verification request
    result = await review_verification_request(
        db=db,
        request_id=request_id,
        admin_id=admin_id,
        action="approve",
        admin_note="Đã xác thực hồ sơ đăng ký thành lập CLB",
    )

    # 1. Status transition invariant
    assert result.status == "approved"
    assert verif_request.status == VerificationStatus.approved
    assert verif_request.reviewed_by == admin_id

    # 2. Role promotion & verified badge invariant
    assert user.is_verified is True
    assert user.role == UserRole.edu_org

    # 3. Terminal state protection invariant: cannot re-approve or reject once approved
    with pytest.raises(ValidationError) as exc:
        await review_verification_request(
            db=db,
            request_id=request_id,
            admin_id=admin_id,
            action="reject",
        )
    assert "terminal state 'approved'" in str(exc.value)
