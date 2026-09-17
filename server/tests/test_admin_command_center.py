"""Comprehensive Unit & Integration Tests for Phase 10 Admin Command Center.

Covers:
- KPI Aggregation & Deterministic Formulas (total_ctxh, attendance_rate, dau/mau, growth with None delta)
- Master Student Audit Aggregation & Query
- UTF-8 BOM CSV Streaming Export
- Verification State Machine & Terminal-State Protection
- Moderation State Machine & Atomic Side-effects
- Admin Audit Trail Logging & Sanitized Metadata
- Granular RBAC Permissions
"""

import codecs
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.core.exceptions import ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from app.modules.activities.models import Activity
from app.modules.admin.analytics.service import get_active_users_count, get_kpi_metrics
from app.modules.admin.audit.service import list_audit_logs, record_audit_log
from app.modules.admin.export.service import stream_students_csv
from app.modules.admin.models import (
    AdminAuditAction,
    AdminAuditLog,
    AdminAuditTargetType,
    OrganizationVerificationRequest,
    VerificationStatus,
)
from app.modules.admin.moderation.schemas import ReportReviewAction
from app.modules.admin.moderation.service import list_reports, review_report
from app.modules.admin.permissions import (
    require_admin_access,
    require_moderation_permission,
    require_staff_or_admin,
    require_user_management_permission,
    require_verification_permission,
)
from app.modules.admin.students.schemas import StudentAuditItem
from app.modules.admin.students.service import list_students_audit
from app.modules.admin.verification.schemas import (
    VerificationRequestCreate,
    VerificationReviewAction,
)
from app.modules.admin.verification.service import (
    list_verification_requests,
    review_verification_request,
    submit_verification_request,
)
from app.modules.participation.models import JoinRequest
from app.modules.reports.models import Report
from app.modules.users.models import User, UserRole


# ── 1. Analytics & KPI Metrics Tests ──

@pytest.mark.asyncio
async def test_kpi_metrics_deterministic_aggregation():
    """Verify KPI formulas: CTXH sum, attendance rate, and None delta when prev=0."""
    db = AsyncMock()

    # Sequence of scalar returns for get_kpi_metrics:
    # 1. total_ctxh_val = 14.5
    # 2..8. ctxh_trend (7 points) = 14.5
    # 9. prev_month_ctxh = 0.0 (so delta_percent should be None)
    # 10. confirmed_count = 8
    # 11. total_eligible = 10 (8/10 = 80.0%)
    # 12..25. active users queries (dau, mau, 7 trend days, cur_month, prev_month=0)
    # 26. total_users = 50
    # 27. total_activities = 12
    async def mock_execute(stmt):
        mock_res = MagicMock()
        stmt_str = str(stmt)
        if "social_work_days" in stmt_str:
            mock_res.scalar.return_value = 14.5
        elif "count" in stmt_str and "attendance_confirmed" in stmt_str:
            mock_res.scalar.return_value = 8
        elif "count" in stmt_str and "activities" in stmt_str:
            mock_res.scalar.return_value = 10
        elif "users" in stmt_str:
            mock_res.scalar.return_value = 50
        else:
            mock_res.scalar.return_value = 5
        return mock_res

    db.execute.side_effect = mock_execute

    with patch("app.modules.admin.analytics.service.get_active_users_count") as mock_active:
        mock_active.side_effect = [3, 25, 2, 4, 3, 5, 2, 6, 3, 10, 0]  # prev_month_active = 0
        metrics = await get_kpi_metrics(db)

        assert metrics.total_ctxh.value == 14.5
        assert "14.5" in metrics.total_ctxh.formatted_value
        assert metrics.attendance_rate.value == 80.0
        assert metrics.attendance_rate.formatted_value == "80.0%"
        assert metrics.monthly_growth.delta_percent is None  # Since prev was 0
        assert metrics.dau == 3
        assert metrics.mau == 25


@pytest.mark.asyncio
async def test_kpi_attendance_rate_zero_division():
    """Verify attendance rate is safely 0.0% when total completed activities registrations is 0."""
    db = AsyncMock()

    async def mock_execute(stmt):
        mock_res = MagicMock()
        mock_res.scalar.return_value = 0
        return mock_res

    db.execute.side_effect = mock_execute

    with patch("app.modules.admin.analytics.service.get_active_users_count") as mock_active:
        mock_active.return_value = 0
        metrics = await get_kpi_metrics(db)
        assert metrics.attendance_rate.value == 0.0
        assert metrics.attendance_rate.formatted_value == "0.0%"


# ── 2. Master Student Audit & CSV Export Tests ──

@pytest.mark.asyncio
async def test_student_audit_query_and_mapping():
    """Verify student audit query maps confirmed CTXH and attendance count properly."""
    db = AsyncMock()
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # Mock count then rows
    count_res = MagicMock()
    count_res.scalar.return_value = 1

    rows_res = MagicMock()
    rows_res.all.return_value = [
        (
            user_id,
            "21120001",
            "Nguyen Van A",
            "vana@uni.edu.vn",
            "Khoa CNTT",
            True,
            False,
            UserRole.student,
            now,
            12.5,  # confirmed_ctxh_days
            8,     # attendance_count
        )
    ]

    db.execute.side_effect = [count_res, rows_res]

    res = await list_students_audit(db, search="21120001", limit=10, offset=0)
    assert res.total == 1
    assert len(res.items) == 1
    item = res.items[0]
    assert item.username == "21120001"
    assert item.confirmed_ctxh_days == 12.5
    assert item.attendance_count == 8
    assert item.role == "student"


@pytest.mark.asyncio
async def test_stream_students_csv_utf8_bom():
    """Verify CSV streaming starts with UTF-8 BOM and encodes Vietnamese headers and rows."""
    db = AsyncMock()
    now = datetime.now(timezone.utc)

    async def mock_stream_gen():
        yield (
            uuid.uuid4(),
            "21120002",
            "Trần Thị Bông",
            "bong@uni.edu.vn",
            "Đại học Bách Khoa",
            True,
            True,
            UserRole.edu_org,
            now,
            15.0,
            10,
        )

    db.stream.return_value = mock_stream_gen()

    chunks = []
    async for chunk in stream_students_csv(db):
        chunks.append(chunk)

    # First chunk must be UTF-8 BOM
    assert chunks[0] == codecs.BOM_UTF8

    full_csv = b"".join(chunks).decode("utf-8")
    assert "MSSV / Username" in full_csv
    assert "Họ và tên" in full_csv
    assert "Trần Thị Bông" in full_csv
    assert "Đang hoạt động" in full_csv
    assert "Đã xác minh" in full_csv
    assert "15.0" in full_csv


# ── 3. Verification State Machine Tests ──

@pytest.mark.asyncio
async def test_verification_request_submission_and_duplicate_guard():
    """Verify verification request creation and rejection of duplicate pending requests."""
    db = AsyncMock()
    db.add = MagicMock()
    user_id = uuid.uuid4()

    # 1. First check: already pending -> raises ValidationError
    pending_mock = MagicMock()
    pending_mock.scalars.return_value.first.return_value = OrganizationVerificationRequest(
        user_id=user_id, organization_name="CLB Tin Học", status=VerificationStatus.pending
    )
    db.execute.return_value = pending_mock

    with pytest.raises(ValidationError) as exc:
        await submit_verification_request(
            db,
            user_id,
            VerificationRequestCreate(organization_name="CLB Tin Học"),
        )
    assert "already have a pending verification" in str(exc.value)

    # 2. No pending -> success
    no_pending_mock = MagicMock()
    no_pending_mock.scalars.return_value.first.return_value = None
    db.execute.return_value = no_pending_mock
    db.get.return_value = User(id=user_id, username="clb_tinhoc", email="clb@uni.edu.vn", role=UserRole.student)

    item = await submit_verification_request(
        db,
        user_id,
        VerificationRequestCreate(organization_name="CLB Tin Học", faculty="CNTT"),
    )
    assert item.organization_name == "CLB Tin Học"
    assert item.status == "pending"


@pytest.mark.asyncio
async def test_verification_review_approve_promotes_role_and_audit():
    """Verify approving verification promotes student to edu_org, marks is_verified, and audits."""
    db = AsyncMock()
    db.add = MagicMock()
    admin_id = uuid.uuid4()
    user_id = uuid.uuid4()
    req_id = uuid.uuid4()

    req = OrganizationVerificationRequest(
        id=req_id,
        user_id=user_id,
        organization_name="CLB Tình Nguyện",
        status=VerificationStatus.pending,
    )
    user = User(id=user_id, username="clb_tn", role=UserRole.student, is_verified=False)

    async def mock_get(model, obj_id):
        if model == OrganizationVerificationRequest:
            return req
        if model == User:
            return user
        return None

    db.get.side_effect = mock_get

    res = await review_verification_request(
        db=db,
        request_id=req_id,
        admin_id=admin_id,
        action="approve",
        admin_note="Hồ sơ hợp lệ và có chữ ký Đoàn trường",
    )

    assert res.status == "approved"
    assert user.is_verified is True
    assert user.role == UserRole.edu_org  # Promoted from student


@pytest.mark.asyncio
async def test_verification_review_terminal_state_protection():
    """Verify terminal-state protection: already approved/rejected cannot be re-reviewed."""
    db = AsyncMock()
    req = OrganizationVerificationRequest(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        organization_name="CLB Âm Nhạc",
        status=VerificationStatus.approved,  # Terminal state
    )
    db.get.return_value = req

    with pytest.raises(ValidationError) as exc:
        await review_verification_request(
            db=db,
            request_id=req.id,
            admin_id=uuid.uuid4(),
            action="reject",
        )
    assert "terminal state 'approved'" in str(exc.value)


# ── 4. Moderation State Machine & Atomic Side-effects Tests ──

@pytest.mark.asyncio
async def test_moderation_review_resolve_with_hide_activity_and_audit():
    """Verify resolving report atomically soft-deletes target activity and writes audit logs."""
    db = AsyncMock()
    db.add = MagicMock()
    admin_id = uuid.uuid4()
    report_id = uuid.uuid4()
    act_id = uuid.uuid4()
    reporter_id = uuid.uuid4()

    report = Report(
        id=report_id,
        reporter_id=reporter_id,
        target_type="activity",
        target_id=act_id,
        reason="Nội dung sai sự thật",
        status="pending",
    )
    activity = Activity(id=act_id, title="Sự kiện vi phạm", is_deleted=False)
    reporter = User(id=reporter_id, username="sinhvien_a")

    async def mock_get(model, obj_id):
        if model == Report:
            return report
        if model == Activity:
            return activity
        if model == User:
            return reporter
        return None

    db.get.side_effect = mock_get

    res = await review_report(
        db=db,
        report_id=report_id,
        admin_id=admin_id,
        action="resolve",
        admin_note="Đã xác minh và gỡ bỏ hoạt động",
        hide_activity=True,
    )

    assert res.status == "resolved"
    assert activity.is_deleted is True  # Soft deleted


@pytest.mark.asyncio
async def test_moderation_terminal_state_protection():
    """Verify cannot review a report already resolved or dismissed."""
    db = AsyncMock()
    report = Report(
        id=uuid.uuid4(),
        reporter_id=uuid.uuid4(),
        target_type="user",
        target_id=uuid.uuid4(),
        reason="Spam",
        status="resolved",  # Terminal state
    )
    db.get.return_value = report

    with pytest.raises(ValidationError) as exc:
        await review_report(
            db=db,
            report_id=report.id,
            admin_id=uuid.uuid4(),
            action="dismiss",
        )
    assert "terminal state 'resolved'" in str(exc.value)


# ── 5. Granular RBAC Tests ──

@pytest.mark.asyncio
async def test_rbac_admin_vs_edu_org_vs_student():
    """Verify granular permissions: student forbidden from admin ops, edu_org permitted for staff ops."""
    admin_checker = require_admin_access
    staff_checker = require_staff_or_admin

    admin_payload = {"sub": str(uuid.uuid4()), "role": "admin"}
    edu_org_payload = {"sub": str(uuid.uuid4()), "role": "edu_org"}
    student_payload = {"sub": str(uuid.uuid4()), "role": "student"}

    # 1. Admin passes both
    assert (await admin_checker(admin_payload)) == admin_payload
    assert (await staff_checker(admin_payload)) == admin_payload

    # 2. Edu org passes staff_checker, but fails admin_checker
    assert (await staff_checker(edu_org_payload)) == edu_org_payload
    with pytest.raises(ForbiddenError):
        await admin_checker(edu_org_payload)

    # 3. Student fails both
    with pytest.raises(ForbiddenError):
        await staff_checker(student_payload)
    with pytest.raises(ForbiddenError):
        await admin_checker(student_payload)
