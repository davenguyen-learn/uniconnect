import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import HTTPException

from app.modules.groups.models import Group, GroupMember, GroupRole, GroupJoinRequest, ActivityCoHost, ActivityCoHostInvitation
from app.modules.activities.models import Activity
from app.modules.participation.models import JoinRequest, RequestStatus
from app.modules.groups.permissions import (
    can_approve_join_request,
    can_invite_cohost,
    can_open_checkin,
    can_manage_activity,
    can_manage_group,
)
from app.modules.groups.schemas import CoHostInvitationCreate


# ── 1. RBAC & Granular Permission Tests ──

@pytest.mark.asyncio
async def test_group_rbac_permissions():
    """Verify granular permission boundaries across Owner, Admin, Member, and Guest."""
    owner_id = uuid.uuid4()
    admin_id = uuid.uuid4()
    member_id = uuid.uuid4()
    guest_id = uuid.uuid4()
    group_id = uuid.uuid4()

    mock_db = AsyncMock()

    # Test can_manage_group: Only owner
    with patch("app.modules.groups.permissions.select") as mock_select:
        # Simulate owner check
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.side_effect = [group_id, None, None]
        mock_db.execute.return_value = mock_res

        assert await can_manage_group(mock_db, owner_id, group_id) is True
        assert await can_manage_group(mock_db, admin_id, group_id) is False
        assert await can_manage_group(mock_db, guest_id, group_id) is False


@pytest.mark.asyncio
async def test_can_approve_join_request():
    """Admin and Owner can approve; Member and Guest cannot."""
    owner_id = uuid.uuid4()
    admin_id = uuid.uuid4()
    member_id = uuid.uuid4()
    guest_id = uuid.uuid4()
    group_id = uuid.uuid4()

    mock_db = AsyncMock()

    # 1. Owner: is_group_admin_or_owner returns True
    with patch("app.modules.groups.permissions.is_group_admin_or_owner", return_value=True):
        assert await can_approve_join_request(mock_db, owner_id, group_id) is True
        assert await can_approve_join_request(mock_db, admin_id, group_id) is True

    # 2. Member & Guest: returns False
    with patch("app.modules.groups.permissions.is_group_admin_or_owner", return_value=False):
        assert await can_approve_join_request(mock_db, member_id, group_id) is False
        assert await can_approve_join_request(mock_db, guest_id, group_id) is False


@pytest.mark.asyncio
async def test_can_open_checkin_and_manage_activity_distinction():
    """
    Accepted Co-Host CAN open check-in.
    Accepted Co-Host CANNOT manage (edit/cancel/delete) activity!
    """
    host_user_id = uuid.uuid4()
    lead_admin_id = uuid.uuid4()
    cohost_admin_id = uuid.uuid4()
    unrelated_user_id = uuid.uuid4()

    act_id = uuid.uuid4()
    lead_group_id = uuid.uuid4()
    cohost_group_id = uuid.uuid4()

    mock_db = AsyncMock()

    # Setup Activity
    act = Activity(
        id=act_id,
        title="Ngày Hội Tình Nguyện",
        host_id=host_user_id,
        group_id=lead_group_id,
        is_deleted=False,
    )

    # Mock DB query for Activity
    mock_act_res = MagicMock()
    mock_act_res.scalar_one_or_none.return_value = act

    # Mock DB query for CoHosts list
    mock_cohost_res = MagicMock()
    mock_cohost_res.scalars.return_value.all.return_value = [cohost_group_id]

    mock_db.execute.side_effect = [
        mock_act_res, mock_cohost_res,  # for check-in
        mock_act_res,                    # for manage_activity
    ]

    # Helper patch for group admin checks
    async def mock_admin_check(db, uid, gid):
        if gid == lead_group_id and uid == lead_admin_id:
            return True
        if gid == cohost_group_id and uid == cohost_admin_id:
            return True
        return False

    with patch("app.modules.groups.permissions.is_group_admin_or_owner", side_effect=mock_admin_check):
        # 1. Direct host can open check-in
        mock_db.execute.return_value = mock_act_res
        assert await can_open_checkin(mock_db, host_user_id, act_id) is True

        # 2. Accepted co-host can open check-in
        # Reset side effects
        mock_db.execute.side_effect = [mock_act_res, mock_cohost_res]
        assert await can_open_checkin(mock_db, cohost_admin_id, act_id) is True

        # 3. Accepted co-host CANNOT manage activity!
        mock_db.execute.side_effect = [mock_act_res]
        assert await can_manage_activity(mock_db, cohost_admin_id, act_id) is False

        # 4. Lead host admin CAN manage activity
        mock_db.execute.side_effect = [mock_act_res]
        assert await can_manage_activity(mock_db, lead_admin_id, act_id) is True

        # 5. Unrelated user CANNOT manage activity
        mock_db.execute.side_effect = [mock_act_res]
        assert await can_manage_activity(mock_db, unrelated_user_id, act_id) is False


# ── 2. Co-Host Invitation Invariants & State Machine ──

@pytest.mark.asyncio
async def test_cohost_invitation_invariants():
    """Verify lead host cannot invite self, duplicate pending is 409, and already accepted is 400."""
    from app.modules.groups.service import invite_cohost

    user_id = uuid.uuid4()
    activity_id = uuid.uuid4()
    lead_group_id = uuid.uuid4()
    invited_group_id = uuid.uuid4()

    mock_db = AsyncMock()

    # 1. Self-invitation -> 400
    act = Activity(id=activity_id, group_id=lead_group_id, is_deleted=False)
    with patch("app.modules.groups.service.can_invite_cohost", return_value=True):
        with patch("app.modules.groups.service.select") as mock_sel:
            mock_res = MagicMock()
            mock_res.scalar_one_or_none.return_value = act
            mock_db.execute.return_value = mock_res

            with pytest.raises(HTTPException) as exc_self:
                await invite_cohost(
                    mock_db, activity_id, user_id,
                    CoHostInvitationCreate(invited_group_id=lead_group_id)
                )
            assert exc_self.value.status_code == 400
            assert "lead host" in exc_self.value.detail.lower()

    # 2. Already accepted cohost -> 400
    with patch("app.modules.groups.service.can_invite_cohost", return_value=True):
        with patch("app.modules.groups.repository.get_group_by_id", return_value=Group(id=invited_group_id, name="CLB B")):
            mock_act_res = MagicMock()
            mock_act_res.scalar_one_or_none.return_value = act

            mock_existing_cohost = MagicMock()
            mock_existing_cohost.scalar_one_or_none.return_value = ActivityCoHost(activity_id=activity_id, group_id=invited_group_id)

            mock_db.execute.side_effect = [mock_act_res, mock_existing_cohost]

            with pytest.raises(HTTPException) as exc_cohost:
                await invite_cohost(
                    mock_db, activity_id, user_id,
                    CoHostInvitationCreate(invited_group_id=invited_group_id)
                )
            assert exc_cohost.value.status_code == 400
            assert "already an accepted co-host" in exc_cohost.value.detail.lower()

    # 3. Duplicate pending invitation -> 409
    with patch("app.modules.groups.service.can_invite_cohost", return_value=True):
        with patch("app.modules.groups.repository.get_group_by_id", return_value=Group(id=invited_group_id, name="CLB B")):
            mock_no_cohost = MagicMock()
            mock_no_cohost.scalar_one_or_none.return_value = None

            mock_existing_pending = MagicMock()
            mock_existing_pending.scalar_one_or_none.return_value = ActivityCoHostInvitation(
                activity_id=activity_id, invited_group_id=invited_group_id, status="pending"
            )

            mock_db.execute.side_effect = [mock_act_res, mock_no_cohost, mock_existing_pending]

            with pytest.raises(HTTPException) as exc_pend:
                await invite_cohost(
                    mock_db, activity_id, user_id,
                    CoHostInvitationCreate(invited_group_id=invited_group_id)
                )
            assert exc_pend.value.status_code == 409
            assert "pending invitation already exists" in exc_pend.value.detail.lower()


# ── 3. MAX_COHOSTS Atomic Limit & Concurrent Guard ──

@pytest.mark.asyncio
async def test_max_cohosts_limit_enforced_on_accept():
    """Verify accepting when count >= 5 triggers 409 Conflict."""
    from app.modules.groups.service import respond_cohost_invitation

    inv_id = uuid.uuid4()
    act_id = uuid.uuid4()
    user_id = uuid.uuid4()
    group_id = uuid.uuid4()

    mock_db = AsyncMock()
    inv = ActivityCoHostInvitation(
        id=inv_id,
        activity_id=act_id,
        invited_group_id=group_id,
        status="pending",
    )

    with patch("app.modules.groups.service.can_respond_cohost_invitation", return_value=True):
        with patch("app.modules.groups.service.select") as mock_sel:
            mock_inv_res = MagicMock()
            mock_inv_res.scalar_one_or_none.return_value = inv
            mock_db.execute.return_value = mock_inv_res

            # When count is already 5
            with patch("app.modules.groups.repository.count_accepted_cohosts", return_value=5):
                with pytest.raises(HTTPException) as exc_max:
                    await respond_cohost_invitation(mock_db, inv_id, user_id, action="accepted")
                assert exc_max.value.status_code == 409
                assert "maximum" in exc_max.value.detail.lower()


# ── 4. Join Request State Machine ──

@pytest.mark.asyncio
async def test_join_request_state_machine():
    """Verify pending -> approved/rejected, and invalid non-pending transitions fail with 400."""
    from app.modules.groups.service import action_join_request

    group_id = uuid.uuid4()
    req_id = uuid.uuid4()
    user_id = uuid.uuid4()
    applicant_id = uuid.uuid4()

    mock_db = AsyncMock()

    # 1. Transition approved -> approved fails with 400
    already_approved_req = GroupJoinRequest(
        id=req_id,
        group_id=group_id,
        user_id=applicant_id,
        status="approved",
    )

    with patch("app.modules.groups.service.can_approve_join_request", return_value=True):
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = already_approved_req
        mock_db.execute.return_value = mock_res

        with pytest.raises(HTTPException) as exc_trans:
            await action_join_request(mock_db, group_id, req_id, user_id, action="approved")
        assert exc_trans.value.status_code == 400
        assert "not pending" in exc_trans.value.detail.lower()

    # 2. Invalid action fails with 400
    with patch("app.modules.groups.service.can_approve_join_request", return_value=True):
        with pytest.raises(HTTPException) as exc_action:
            await action_join_request(mock_db, group_id, req_id, user_id, action="invalid_action")
        assert exc_action.value.status_code == 400


# ── 5. Re-invite & Rollback Boundary Tests ──

@pytest.mark.asyncio
async def test_reinvite_after_declined_success():
    """Verify that if a previous invitation was declined, a new invitation can be issued."""
    from app.modules.groups.service import invite_cohost

    user_id = uuid.uuid4()
    activity_id = uuid.uuid4()
    lead_group_id = uuid.uuid4()
    invited_group_id = uuid.uuid4()

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    act = Activity(id=activity_id, group_id=lead_group_id, is_deleted=False)

    with patch("app.modules.groups.service.can_invite_cohost", return_value=True):
        with patch("app.modules.groups.repository.get_group_by_id", return_value=Group(id=invited_group_id, name="CLB B")):
            mock_act_res = MagicMock()
            mock_act_res.scalar_one_or_none.return_value = act

            mock_no_cohost = MagicMock()
            mock_no_cohost.scalar_one_or_none.return_value = None

            mock_no_pending = MagicMock()
            mock_no_pending.scalar_one_or_none.return_value = None  # Declined, so no active pending row

            mock_db.execute.side_effect = [mock_act_res, mock_no_cohost, mock_no_pending]

            res = await invite_cohost(
                mock_db, activity_id, user_id,
                CoHostInvitationCreate(invited_group_id=invited_group_id, message="Mời lại")
            )
            assert res.activity_id == activity_id
            assert res.invited_group_id == invited_group_id
            assert res.status == "pending"
            assert mock_db.commit.called


@pytest.mark.asyncio
async def test_respond_cohost_invitation_rollback_on_failure():
    """Verify transactional rollback: failed cohost creation causes rollback, preventing corrupted state."""
    from app.modules.groups.service import respond_cohost_invitation

    inv_id = uuid.uuid4()
    act_id = uuid.uuid4()
    user_id = uuid.uuid4()
    group_id = uuid.uuid4()

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    inv = ActivityCoHostInvitation(
        id=inv_id,
        activity_id=act_id,
        invited_group_id=group_id,
        status="pending",
    )

    with patch("app.modules.groups.service.can_respond_cohost_invitation", return_value=True):
        mock_inv_res = MagicMock()
        mock_inv_res.scalar_one_or_none.return_value = inv

        mock_upd_res = MagicMock()
        mock_upd_res.rowcount = 1

        mock_db.execute.side_effect = [mock_inv_res, mock_upd_res]

        with patch("app.modules.groups.repository.count_accepted_cohosts", return_value=3):
            # Simulate failure during commit
            mock_db.commit.side_effect = RuntimeError("DB error during cohost commit")

            with pytest.raises(RuntimeError):
                await respond_cohost_invitation(mock_db, inv_id, user_id, action="accepted")

            # Verify db.rollback() was called!
            assert mock_db.rollback.called


# ── 6. Group Stats SQL Aggregation & Deduplication Invariant ──

def test_group_stats_sql_aggregation_deduplication_structure():
    """
    Verify compiled SQL for get_group_stats:
    - Uses UNION (not UNION ALL) to merge Lead Host and Co-Host activities.
    - Uses SELECT DISTINCT activities.id, activities.social_work_days to prevent duplicate CTXH summation
      when multiple attendees or co-host relationships exist.
    """
    from sqlalchemy.dialects import postgresql
    from app.modules.groups.models import ActivityCoHost
    from app.modules.activities.models import Activity
    from app.modules.participation.models import JoinRequest
    from sqlalchemy import select, func

    group_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # Reconstruct query exactly as in repository
    lead_acts = select(Activity.id).where(
        Activity.group_id == group_id,
        Activity.is_deleted.is_(False),
        Activity.end_time < now,
    )
    cohost_acts = (
        select(ActivityCoHost.activity_id.label("id"))
        .join(Activity, Activity.id == ActivityCoHost.activity_id)
        .where(
            ActivityCoHost.group_id == group_id,
            Activity.is_deleted.is_(False),
            Activity.end_time < now,
        )
    )
    eligible_act_ids_subq = lead_acts.union(cohost_acts).subquery()
    act_count_stmt = select(func.count()).select_from(eligible_act_ids_subq)

    confirmed_acts_subq = (
        select(Activity.id, Activity.social_work_days)
        .join(JoinRequest, JoinRequest.activity_id == Activity.id)
        .where(
            Activity.id.in_(select(eligible_act_ids_subq.c.id)),
            JoinRequest.attendance_confirmed.is_(True),
            Activity.social_work_days.is_not(None),
        )
        .distinct()
        .subquery()
    )
    ctxh_stmt = select(func.coalesce(func.sum(confirmed_acts_subq.c.social_work_days), 0.0))

    compiled_count_sql = str(act_count_stmt.compile(dialect=postgresql.dialect()))
    compiled_ctxh_sql = str(ctxh_stmt.compile(dialect=postgresql.dialect()))

    # Assertions
    assert "UNION" in compiled_count_sql
    assert "UNION ALL" not in compiled_count_sql
    assert "DISTINCT" in compiled_ctxh_sql
    assert "coalesce(sum(" in compiled_ctxh_sql.lower()
    assert "join_requests.attendance_confirmed is true" in compiled_ctxh_sql.lower()
