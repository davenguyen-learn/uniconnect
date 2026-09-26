"""Unit & integration tests for Trophy Privacy, Authorization, and Lifecycle Review."""

import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import HTTPException

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.modules.activities.models import Activity, ActivityPrivacy
from app.modules.activities.schemas import ActivityCreate, ActivityUpdate
from app.modules.activities.service import create_activity, update_activity
from app.modules.participation.models import JoinRequest, RequestStatus
from app.modules.participation.service import (
    finalize_activity_attendance,
    update_participant_attendance,
)
from app.modules.trophies.models import Trophy, TrophyGrantRequest, TrophyGrantStatus, UserTrophy
from app.modules.trophies.router import create_trophy, get_user_trophies
from app.modules.trophies.schemas import TrophyCreate
from app.modules.users.models import User, UserRole
from app.modules.admin.trophy_service import review_trophy_grant_request


# ─────────────────────────────────────────────────────────────────────────────
# Contract A: Private Activity Trophy Privacy Tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_outsider_private_activity_trophy_sanitized():
    """Verify outsider receives is_accessible=False, id=None, title='Sự kiện nội bộ'."""
    db = AsyncMock()
    user_id = uuid.uuid4()
    outsider_id = uuid.uuid4()
    act_id = uuid.uuid4()

    mock_act = MagicMock()
    mock_act.id = act_id
    mock_act.title = "Kỳ thi Thuật toán Kín K21"
    mock_act.privacy = ActivityPrivacy.private
    mock_act.host_id = uuid.uuid4()  # not outsider

    mock_trophy = MagicMock()
    mock_trophy.id = uuid.uuid4()
    mock_trophy.name = "Quán quân Thuật toán"
    mock_trophy.description = "Giải nhất vòng chung kết"
    mock_trophy.points = 100
    mock_trophy.icon = "🏆"
    mock_trophy.activity_id = None
    mock_trophy.creator_id = None
    mock_trophy.created_at = datetime.now(timezone.utc)

    mock_ut = MagicMock()
    mock_ut.id = uuid.uuid4()
    mock_ut.user_id = user_id
    mock_ut.trophy_id = mock_trophy.id
    mock_ut.activity_id = act_id
    mock_ut.trophy = mock_trophy
    mock_ut.activity = mock_act
    mock_ut.created_at = datetime.now(timezone.utc)

    # First execute: list user_trophies
    mock_ut_res = MagicMock()
    mock_ut_res.unique.return_value.scalars.return_value.all.return_value = [mock_ut]

    # Second execute: check approved join requests for outsider (empty set)
    mock_parts_res = MagicMock()
    mock_parts_res.scalars.return_value.all.return_value = []

    db.execute = AsyncMock(side_effect=[mock_ut_res, mock_parts_res])

    # Outsider viewer
    current_user = {"sub": str(outsider_id), "role": "student"}
    items = await get_user_trophies(user_id=user_id, current_user=current_user, db=db)

    assert len(items) == 1
    act_dto = items[0].activity
    assert act_dto is not None
    assert act_dto.is_accessible is False
    assert act_dto.id is None
    assert act_dto.title == "Sự kiện nội bộ"
    assert act_dto.privacy == "private"


@pytest.mark.asyncio
async def test_participant_or_host_private_activity_trophy_accessible():
    """Verify participant or host receives is_accessible=True, real id and real title."""
    db = AsyncMock()
    user_id = uuid.uuid4()
    participant_id = uuid.uuid4()
    act_id = uuid.uuid4()

    mock_act = MagicMock()
    mock_act.id = act_id
    mock_act.title = "Kỳ thi Thuật toán Kín K21"
    mock_act.privacy = ActivityPrivacy.private
    mock_act.host_id = uuid.uuid4()

    mock_trophy = MagicMock()
    mock_trophy.id = uuid.uuid4()
    mock_trophy.name = "Quán quân Thuật toán"
    mock_trophy.description = "Giải nhất vòng chung kết"
    mock_trophy.points = 100
    mock_trophy.icon = "🏆"
    mock_trophy.activity_id = None
    mock_trophy.creator_id = None
    mock_trophy.created_at = datetime.now(timezone.utc)

    mock_ut = MagicMock()
    mock_ut.id = uuid.uuid4()
    mock_ut.user_id = user_id
    mock_ut.trophy_id = mock_trophy.id
    mock_ut.activity_id = act_id
    mock_ut.trophy = mock_trophy
    mock_ut.activity = mock_act
    mock_ut.created_at = datetime.now(timezone.utc)

    mock_ut_res = MagicMock()
    mock_ut_res.unique.return_value.scalars.return_value.all.return_value = [mock_ut]

    # Participant is approved
    mock_parts_res = MagicMock()
    mock_parts_res.scalars.return_value.all.return_value = [act_id]

    db.execute = AsyncMock(side_effect=[mock_ut_res, mock_parts_res])

    current_user = {"sub": str(participant_id), "role": "student"}
    items = await get_user_trophies(user_id=user_id, current_user=current_user, db=db)

    assert len(items) == 1
    act_dto = items[0].activity
    assert act_dto is not None
    assert act_dto.is_accessible is True
    assert act_dto.id == act_id
    assert act_dto.title == "Kỳ thi Thuật toán Kín K21"


# ─────────────────────────────────────────────────────────────────────────────
# Contract B: Trophy Authorization RBAC Tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_student_role_cannot_create_or_attach_trophy():
    """Verify student role is rejected with 403 on create_trophy and attach trophy_id."""
    db = AsyncMock()
    student_id = uuid.uuid4()

    mock_student = MagicMock(spec=User)
    mock_student.id = student_id
    mock_student.role = UserRole.student
    mock_student.is_verified = True  # verified student still rejected!
    db.scalar = AsyncMock(return_value=mock_student)

    # 1. create_trophy endpoint
    data = TrophyCreate(name="Trophy Giả", points=50)
    current_user = {"sub": str(student_id), "role": "student"}
    with pytest.raises(HTTPException) as exc_info:
        await create_trophy(data=data, current_user=current_user, db=db)
    assert exc_info.value.status_code == 403

    # 2. create_activity with trophy_id
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_student
    db.execute = AsyncMock(return_value=mock_result)

    act_data = ActivityCreate(
        title="Test Activity",
        description="Description",
        meeting_location="Hội trường A5",
        start_time=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        end_time=(datetime.now(timezone.utc) + timedelta(hours=3)).isoformat(),
        max_participants=20,
        latitude=10.77,
        longitude=106.69,
        trophy_id=uuid.uuid4(),
    )
    with pytest.raises(ForbiddenError):
        await create_activity(db=db, user_id=str(student_id), data=act_data)


@pytest.mark.asyncio
async def test_edu_org_and_admin_can_create_trophy():
    """Verify edu_org and admin roles are allowed to create trophies."""
    db = AsyncMock()
    admin_id = uuid.uuid4()

    mock_admin = MagicMock(spec=User)
    mock_admin.id = admin_id
    mock_admin.role = UserRole.admin
    db.scalar = AsyncMock(return_value=mock_admin)

    data = TrophyCreate(name="BK Hackathon Champion", points=100)
    current_user = {"sub": str(admin_id), "role": "admin"}

    trophy = await create_trophy(data=data, current_user=current_user, db=db)
    assert trophy.name == "BK Hackathon Champion"
    db.commit.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# Contract C: Attendance Finalization & Quorum Tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_finalize_attendance_before_end_time_rejected():
    """Verify finalization before activity end_time raises ConflictError (409)."""
    db = AsyncMock()
    act_id = uuid.uuid4()
    host_id = uuid.uuid4()

    mock_act = MagicMock(spec=Activity)
    mock_act.id = act_id
    mock_act.host_id = host_id
    # End time is 2 hours in the future
    mock_act.end_time = datetime.now(timezone.utc) + timedelta(hours=2)

    db.scalar = AsyncMock(return_value=mock_act)

    with pytest.raises(ConflictError) as exc_info:
        await finalize_activity_attendance(
            db=db,
            activity_id=act_id,
            actor_id=str(host_id),
            actor_role="student",
        )
    assert "chưa kết thúc" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_finalize_activity_without_trophy_no_request_created():
    """Verify activity without trophy_id finalizes cleanly, sets attendance_finalized_at, and creates no TrophyGrantRequest."""
    db = AsyncMock()
    act_id = uuid.uuid4()
    host_id = uuid.uuid4()

    mock_act = MagicMock(spec=Activity)
    mock_act.id = act_id
    mock_act.host_id = host_id
    mock_act.trophy_id = None
    mock_act.attendance_finalized_at = None
    mock_act.end_time = datetime.now(timezone.utc) - timedelta(hours=1)

    db.scalar = AsyncMock(return_value=mock_act)

    res = await finalize_activity_attendance(
        db=db,
        activity_id=act_id,
        actor_id=str(host_id),
        actor_role="student",
    )
    assert res["has_trophy"] is False
    assert res["trophy_grant_request"] is None
    assert mock_act.attendance_finalized_at is not None
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_change_trophy_after_finalization_rejected():
    """Verify changing or attaching trophy_id after attendance finalization raises ConflictError."""
    db = AsyncMock()
    act_id = uuid.uuid4()
    host_id = uuid.uuid4()

    mock_act = MagicMock(spec=Activity)
    mock_act.id = act_id
    mock_act.host_id = host_id
    mock_act.attendance_finalized_at = datetime.now(timezone.utc) - timedelta(minutes=10)

    with patch("app.modules.activities.repository.get_by_id", AsyncMock(return_value=mock_act)):
        with pytest.raises(ConflictError) as exc_info:
            await update_activity(
                db=db,
                activity_id=act_id,
                data=ActivityUpdate(trophy_id=uuid.uuid4()),
                user_id=str(host_id),
            )
        assert "đã chốt điểm danh" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_quorum_boundary_insufficient_9():
    """Verify 9 attendees results in insufficient_quorum state."""
    db = AsyncMock()
    act_id = uuid.uuid4()
    host_id = uuid.uuid4()
    trophy_id = uuid.uuid4()

    mock_act = MagicMock(spec=Activity)
    mock_act.id = act_id
    mock_act.host_id = host_id
    mock_act.trophy_id = trophy_id
    mock_act.end_time = datetime.now(timezone.utc) - timedelta(hours=1)

    # 1. Activity query -> mock_act
    # 2. Existing request query -> None
    # 3. Attended count query -> 9
    db.scalar = AsyncMock(side_effect=[mock_act, None, 9])

    res = await finalize_activity_attendance(
        db=db,
        activity_id=act_id,
        actor_id=str(host_id),
        actor_role="student",
    )
    assert res["has_trophy"] is True
    assert res["attended_count"] == 9
    assert res["status"] == TrophyGrantStatus.insufficient_quorum.value


@pytest.mark.asyncio
async def test_quorum_boundary_eligible_10_and_11():
    """Verify 10 and 11 attendees result in eligible_for_review state."""
    act_id = uuid.uuid4()
    host_id = uuid.uuid4()
    trophy_id = uuid.uuid4()

    for count in [10, 11]:
        db = AsyncMock()
        mock_act = MagicMock(spec=Activity)
        mock_act.id = act_id
        mock_act.host_id = host_id
        mock_act.trophy_id = trophy_id
        mock_act.end_time = datetime.now(timezone.utc) - timedelta(hours=1)

        db.scalar = AsyncMock(side_effect=[mock_act, None, count])

        res = await finalize_activity_attendance(
            db=db,
            activity_id=act_id,
            actor_id=str(host_id),
            actor_role="student",
        )
        assert res["attended_count"] == count
        assert res["status"] == TrophyGrantStatus.eligible_for_review.value


@pytest.mark.asyncio
async def test_attendance_freeze_after_finalization():
    """Verify mutating attendance after finalization raises ConflictError."""
    db = AsyncMock()
    act_id = uuid.uuid4()
    host_id = uuid.uuid4()
    target_user_id = uuid.uuid4()

    mock_act = MagicMock(spec=Activity)
    mock_act.id = act_id
    mock_act.host_id = host_id

    # Existing TrophyGrantRequest found
    mock_req = MagicMock(spec=TrophyGrantRequest)

    with patch("app.modules.activities.repository.get_by_id", AsyncMock(return_value=mock_act)):
        db.scalar = AsyncMock(return_value=mock_req)
        with pytest.raises(ConflictError) as exc_info:
            await update_participant_attendance(
                db=db,
                activity_id=act_id,
                target_user_id=target_user_id,
                host_user_id=str(host_id),
                attended=True,
            )
        assert "đã được chốt" in str(exc_info.value.message)


# ─────────────────────────────────────────────────────────────────────────────
# Contract C: Admin Review, Idempotency & Rollback Safety Tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_approve_grants_user_trophies_atomic():
    """Verify Admin approval atomically transitions to approved and grants UserTrophies."""
    db = AsyncMock()
    req_id = uuid.uuid4()
    act_id = uuid.uuid4()
    trophy_id = uuid.uuid4()
    admin_id = uuid.uuid4()
    host_id = uuid.uuid4()

    mock_req = MagicMock(spec=TrophyGrantRequest)
    mock_req.id = req_id
    mock_req.activity_id = act_id
    mock_req.trophy_id = trophy_id
    mock_req.status = TrophyGrantStatus.eligible_for_review

    mock_req.actual_attended_count = 10

    mock_act = MagicMock(spec=Activity)
    mock_act.id = act_id
    mock_act.host_id = host_id

    # Claim request query returns mock_req, host_id query returns host_id
    db.scalar = AsyncMock(side_effect=[mock_req, host_id])

    # 10 attendee IDs (distinct, not including host)
    attendee_ids = [uuid.uuid4() for _ in range(10)]
    mock_attendees_res = MagicMock()
    mock_attendees_res.scalars.return_value.all.return_value = attendee_ids

    # Mock execute for select and inserts
    mock_insert_res = MagicMock()
    mock_insert_res.rowcount = 1
    db.execute = AsyncMock(side_effect=[mock_attendees_res] + [mock_insert_res] * 10)

    res = await review_trophy_grant_request(
        db=db,
        request_id=req_id,
        action="approve",
        admin_notes="Đã kiểm tra minh chứng hợp lệ",
        admin_id=admin_id,
    )

    assert res["status"] == TrophyGrantStatus.approved.value
    # Invariant: actual_attended_count == COUNT(UserTrophy granted)
    assert res["granted_count"] == mock_req.actual_attended_count == 10
    assert mock_req.status == TrophyGrantStatus.approved
    assert mock_req.reviewed_by == admin_id
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_admin_reject_grants_no_user_trophies():
    """Verify Admin rejection transitions to rejected with 0 UserTrophies granted."""
    db = AsyncMock()
    req_id = uuid.uuid4()
    admin_id = uuid.uuid4()

    mock_req = MagicMock(spec=TrophyGrantRequest)
    mock_req.id = req_id
    mock_req.status = TrophyGrantStatus.eligible_for_review

    db.scalar = AsyncMock(return_value=mock_req)

    res = await review_trophy_grant_request(
        db=db,
        request_id=req_id,
        action="reject",
        admin_notes="Không đủ hình ảnh chứng minh",
        admin_id=admin_id,
    )

    assert res["status"] == TrophyGrantStatus.rejected.value
    assert res["granted_count"] == 0
    assert mock_req.status == TrophyGrantStatus.rejected
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_invalid_state_transitions_rejected():
    """Verify reviewing an insufficient_quorum request raises ConflictError."""
    db = AsyncMock()
    req_id = uuid.uuid4()
    admin_id = uuid.uuid4()

    mock_req = MagicMock(spec=TrophyGrantRequest)
    mock_req.id = req_id
    mock_req.status = TrophyGrantStatus.insufficient_quorum

    db.scalar = AsyncMock(return_value=mock_req)

    with pytest.raises(ConflictError) as exc_info:
        await review_trophy_grant_request(
            db=db,
            request_id=req_id,
            action="approve",
            admin_id=admin_id,
        )
    assert "insufficient_quorum" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_side_effect_idempotency_retry():
    """Verify retrying review on an already approved request raises ConflictError without side effects."""
    db = AsyncMock()
    req_id = uuid.uuid4()
    admin_id = uuid.uuid4()

    mock_req = MagicMock(spec=TrophyGrantRequest)
    mock_req.id = req_id
    mock_req.status = TrophyGrantStatus.approved  # already approved!

    db.scalar = AsyncMock(return_value=mock_req)

    with pytest.raises(ConflictError) as exc_info:
        await review_trophy_grant_request(
            db=db,
            request_id=req_id,
            action="approve",
            admin_id=admin_id,
        )
    assert "approved" in str(exc_info.value.message)
    # db.commit should not be called
    db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_rollback_safety_on_grant_failure():
    """Verify that an exception during batch grant causes rollback leaving request as eligible_for_review."""
    db = AsyncMock()
    req_id = uuid.uuid4()
    act_id = uuid.uuid4()
    trophy_id = uuid.uuid4()
    admin_id = uuid.uuid4()

    mock_req = MagicMock(spec=TrophyGrantRequest)
    mock_req.id = req_id
    mock_req.activity_id = act_id
    mock_req.trophy_id = trophy_id
    mock_req.status = TrophyGrantStatus.eligible_for_review

    mock_act = MagicMock(spec=Activity)
    mock_act.id = act_id
    mock_act.host_id = uuid.uuid4()

    db.scalar = AsyncMock(side_effect=[mock_req, mock_act.host_id])

    attendee_ids = [uuid.uuid4() for _ in range(5)]
    mock_attendees_res = MagicMock()
    mock_attendees_res.scalars.return_value.all.return_value = attendee_ids

    # Simulate database error on insert
    db.execute = AsyncMock(side_effect=[mock_attendees_res, RuntimeError("Database connection lost during insert")])

    with pytest.raises(RuntimeError) as exc_info:
        await review_trophy_grant_request(
            db=db,
            request_id=req_id,
            action="approve",
            admin_id=admin_id,
        )
    assert "Database connection lost" in str(exc_info.value)
    # Commit must not be called
    db.commit.assert_not_called()
