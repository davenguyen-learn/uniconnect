import codecs
import io
import csv
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.activities.models import Activity
from app.modules.forms.models import CustomForm, FormField, FieldType
from app.modules.participation.models import JoinRequest, RequestStatus
from app.modules.users.models import User, UserRole
from app.modules.activities.export_service import (
    get_form_field_response,
    stream_activity_participants_csv,
    format_slug,
)
from app.modules.groups.permissions import can_export_activity_participants


# ── 1. Unit Tests for Field Lookup Priority & Slug ──

def test_get_form_field_response_priority():
    """Verify priority: 1. str(field.id) -> 2. legacy field.label -> 3. '-' without dropping false/0."""
    field_id = uuid.uuid4()
    field = FormField(id=field_id, label="MSSV", field_type=FieldType.text)

    # 1. Primary: match by str(field.id)
    resp1 = {str(field_id): "2212345", "MSSV": "legacy"}
    assert get_form_field_response(field, resp1) == "2212345"

    # 2. Legacy: match by field.label when id not present
    resp2 = {"MSSV": "2212345"}
    assert get_form_field_response(field, resp2) == "2212345"

    # 3. Explicit existence: zero '0' or boolean False should NOT be treated as empty
    num_field = FormField(id=uuid.uuid4(), label="Số năm kinh nghiệm", field_type=FieldType.number)
    resp3 = {str(num_field.id): 0}
    assert get_form_field_response(num_field, resp3) == "0"

    bool_field = FormField(id=uuid.uuid4(), label="Có xe máy?", field_type=FieldType.checkbox)
    resp4 = {str(bool_field.id): False}
    assert get_form_field_response(bool_field, resp4) == "Không"
    resp5 = {str(bool_field.id): True}
    assert get_form_field_response(bool_field, resp5) == "Có"

    # 4. Fallback '-' when missing or empty
    assert get_form_field_response(field, {}) == "-"
    assert get_form_field_response(field, None) == "-"
    assert get_form_field_response(field, {str(field_id): "   "}) == "-"


def test_format_slug():
    assert format_slug("Hiến Máu Nhân Đạo 2026!") == "hien_mau_nhan_dao_2026"
    assert format_slug("Workshop AI & IoT") == "workshop_ai_iot"


# ── 2. Permission Matrix Tests ──

@pytest.mark.asyncio
async def test_permission_matrix_for_export():
    """
    Verify strict permission matrix for export on the same activity:
    - Lead Host: True (200)
    - Lead Group Owner/Admin: True (200)
    - System Admin: True (200)
    - Accepted Co-Host: False (403)
    - Unrelated edu_org: False (403)
    - Normal Student: False (403)
    """
    mock_db = AsyncMock()

    host_id = uuid.uuid4()
    lead_group_admin_id = uuid.uuid4()
    lead_group_id = uuid.uuid4()
    cohost_group_admin_id = uuid.uuid4()
    unrelated_edu_org_id = uuid.uuid4()
    student_id = uuid.uuid4()
    admin_id = uuid.uuid4()
    activity_id = uuid.uuid4()

    activity = MagicMock(spec=Activity)
    activity.id = activity_id
    activity.host_id = host_id
    activity.group_id = lead_group_id
    activity.is_deleted = False

    # Mock DB query for activity
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = activity
    mock_res.unique.return_value = mock_res
    mock_db.execute.return_value = mock_res

    # 1. System Admin -> True regardless of ownership
    assert await can_export_activity_participants(mock_db, admin_id, "admin", activity_id) is True

    # 2. Lead Host -> True
    assert await can_export_activity_participants(mock_db, host_id, "student", activity_id) is True

    # 3. Lead Group Owner/Admin -> True
    with patch("app.modules.groups.permissions.is_group_admin_or_owner", new_callable=AsyncMock) as mock_grp_perm:
        mock_grp_perm.side_effect = lambda db, uid, gid: uid == lead_group_admin_id and gid == lead_group_id

        assert await can_export_activity_participants(mock_db, lead_group_admin_id, "student", activity_id) is True

        # 4. Accepted Co-Host -> False (Strictly forbidden from PII export!)
        assert await can_export_activity_participants(mock_db, cohost_group_admin_id, "student", activity_id) is False

        # 5. Unrelated edu_org -> False (Role edu_org alone gives NO export authority over unowned activities)
        assert await can_export_activity_participants(mock_db, unrelated_edu_org_id, "edu_org", activity_id) is False

        # 6. Normal Student -> False
        assert await can_export_activity_participants(mock_db, student_id, "student", activity_id) is False


# ── 3. Streaming CSV Export Content & UTF-8 BOM Tests ──

@pytest.mark.asyncio
async def test_stream_activity_participants_csv_output():
    """
    Verify complete CSV export stream:
    - Starts with UTF-8 BOM
    - Header contains base columns + dynamic form columns ordered by field.order
    - Row 1: Approved + Attended participant -> Attendance = 'Đã điểm danh', CTXH = derived value
    - Row 2: Approved + Not Attended participant -> Attendance = 'Chưa điểm danh', CTXH = '0'
    - Row 3: Pending participant -> Attendance = '-', CTXH = '0'
    - Row 4: Cancelled participant -> Preserved in history with status 'Đã hủy', Attendance = '-', CTXH = '0'
    - Dynamic questions map correctly via ID and legacy label
    """
    mock_db = AsyncMock()
    activity_id = uuid.uuid4()
    host_id = uuid.uuid4()

    # Create mock dynamic form fields (deliberately create in reverse order to test sorting by order)
    f_phone_id = uuid.uuid4()
    f_phone = FormField(id=f_phone_id, label="Số điện thoại", order=2)

    f_mssv_id = uuid.uuid4()
    f_mssv = FormField(id=f_mssv_id, label="MSSV", order=1)

    custom_form = MagicMock(spec=CustomForm)
    custom_form.fields = [f_phone, f_mssv]  # unordered list

    activity = MagicMock(spec=Activity)
    activity.id = activity_id
    activity.host_id = host_id
    activity.group_id = None
    activity.title = "Chiến dịch Mùa Hè Xanh"
    activity.social_work_days = 2.0
    activity.custom_form = custom_form
    activity.is_deleted = False

    # Mock user & join requests
    u1 = User(id=uuid.uuid4(), username="nguyenvana", full_name="Nguyễn Văn A", email="a@student.edu.vn", university="HCMUT")
    r1 = JoinRequest(
        id=uuid.uuid4(),
        activity_id=activity_id,
        user=u1,
        status=RequestStatus.approved,
        attendance_confirmed=True,
        created_at=datetime(2026, 7, 10, 8, 30, tzinfo=timezone.utc),
        form_responses={str(f_mssv_id): "2210001", str(f_phone_id): "0901234567"},
    )

    u2 = User(id=uuid.uuid4(), username="tranvanb", full_name="Trần Văn B", email="b@student.edu.vn", university="HCMUT")
    r2 = JoinRequest(
        id=uuid.uuid4(),
        activity_id=activity_id,
        user=u2,
        status=RequestStatus.approved,
        attendance_confirmed=False,
        created_at=datetime(2026, 7, 10, 9, 0, tzinfo=timezone.utc),
        form_responses={"MSSV": "2210002", "Số điện thoại": "0907654321"},  # legacy label mapping
    )

    u3 = User(id=uuid.uuid4(), username="lethic", full_name="Lê Thị C", email="c@student.edu.vn", university=None)
    r3 = JoinRequest(
        id=uuid.uuid4(),
        activity_id=activity_id,
        user=u3,
        status=RequestStatus.pending,
        attendance_confirmed=False,
        created_at=datetime(2026, 7, 11, 14, 15, tzinfo=timezone.utc),
        form_responses={str(f_mssv_id): "2210003"},  # phone missing -> should be '-'
    )

    u4 = User(id=uuid.uuid4(), username="phamvand", full_name="Phạm Văn D", email="d@student.edu.vn", university="HCMUT")
    r4 = JoinRequest(
        id=uuid.uuid4(),
        activity_id=activity_id,
        user=u4,
        status=RequestStatus.cancelled,
        attendance_confirmed=False,
        created_at=datetime(2026, 7, 11, 16, 0, tzinfo=timezone.utc),
        form_responses={str(f_mssv_id): "2210004", str(f_phone_id): "0911223344"},
    )

    # Setup DB execution mocks
    act_res = MagicMock()
    act_res.scalar_one_or_none.return_value = activity
    act_res.unique.return_value = act_res

    req_res = MagicMock()
    req_res.scalars.return_value.all.return_value = [r1, r2, r3, r4]

    async def fake_execute(stmt, *args, **kwargs):
        stmt_str = str(stmt)
        if "join_requests" in stmt_str:
            return req_res
        return act_res

    mock_db.execute.side_effect = fake_execute

    chunks = []
    async for chunk in stream_activity_participants_csv(
        db=mock_db,
        activity_id=activity_id,
        user_id=host_id,
        user_role="student",
    ):
        chunks.append(chunk)

    full_bytes = b"".join(chunks)

    # 1. Verify starts with UTF-8 BOM
    assert full_bytes.startswith(codecs.BOM_UTF8)

    # 2. Decode text without BOM
    csv_text = full_bytes[len(codecs.BOM_UTF8):].decode("utf-8")
    reader = list(csv.reader(io.StringIO(csv_text)))

    # Header check: columns must be ordered by field.order (MSSV first, then Số điện thoại)
    header = reader[0]
    assert header == [
        "STT",
        "Họ và tên",
        "Tên người dùng",
        "Email",
        "Trường / Đại học",
        "Thời gian đăng ký",
        "Trạng thái duyệt",
        "Điểm danh",
        "Số ngày CTXH",
        "[Câu hỏi] MSSV",
        "[Câu hỏi] Số điện thoại",
    ]

    # Row 1 (Approved + Attended):
    row1 = reader[1]
    assert row1[0] == "1"
    assert row1[1] == "Nguyễn Văn A"
    assert row1[6] == "Đã duyệt"
    assert row1[7] == "Đã điểm danh"
    assert row1[8] == "2"  # CTXH derived from activity.social_work_days
    assert row1[9] == "2210001"
    assert row1[10] == "0901234567"

    # Row 2 (Approved + Not Attended):
    row2 = reader[2]
    assert row2[1] == "Trần Văn B"
    assert row2[6] == "Đã duyệt"
    assert row2[7] == "Chưa điểm danh"
    assert row2[8] == "0"  # Not attended -> CTXH = 0
    assert row2[9] == "2210002"
    assert row2[10] == "0907654321"

    # Row 3 (Pending):
    row3 = reader[3]
    assert row3[1] == "Lê Thị C"
    assert row3[4] == "-"  # None university -> '-'
    assert row3[6] == "Đang chờ duyệt"
    assert row3[7] == "-"  # Attendance not applicable
    assert row3[8] == "0"
    assert row3[9] == "2210003"
    assert row3[10] == "-"  # Phone missing -> '-'

    # Row 4 (Cancelled):
    row4 = reader[4]
    assert row4[1] == "Phạm Văn D"
    assert row4[6] == "Đã hủy"
    assert row4[7] == "-"
    assert row4[8] == "0"
    assert row4[9] == "2210004"
    assert row4[10] == "0911223344"
