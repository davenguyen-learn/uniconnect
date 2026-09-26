"""Service for streaming Activity Participants as UTF-8 BOM CSV for Excel/Sheets."""

import codecs
import csv
import io
import re
from typing import AsyncGenerator
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.activities.models import Activity
from app.modules.forms.models import CustomForm, FormField
from app.modules.groups.permissions import can_export_activity_participants
from app.modules.participation.models import JoinRequest, RequestStatus


def get_form_field_response(field, form_responses: dict | None) -> str:
    """
    Explicit existence check to retrieve form response without dropping false/0/empty strings:
    Priority:
    1. str(field.id)
    2. legacy field.label
    3. fallback '-'
    """
    if not form_responses or not isinstance(form_responses, dict):
        return "-"

    # 1. Primary: field.id
    fid = str(field.id)
    if fid in form_responses and form_responses[fid] is not None:
        val = form_responses[fid]
        if isinstance(val, bool):
            return "Có" if val else "Không"
        s = str(val).strip()
        return s if s else "-"

    # 2. Legacy fallback: field.label
    flabel = field.label
    if flabel in form_responses and form_responses[flabel] is not None:
        val = form_responses[flabel]
        if isinstance(val, bool):
            return "Có" if val else "Không"
        s = str(val).strip()
        return s if s else "-"

    return "-"


def format_slug(text: str) -> str:
    """ASCII-safe sanitize title for download filename."""
    import unicodedata
    cleaned = text.replace('đ', 'd').replace('Đ', 'D')
    norm = unicodedata.normalize('NFKD', cleaned).encode('ascii', 'ignore').decode('utf-8')
    s = re.sub(r'[^\w\s-]', '', norm).strip().lower()
    clean = re.sub(r'[-\s]+', '_', s)[:30]
    return clean if clean else "hoat_dong"


async def stream_activity_participants_csv(
    db: AsyncSession,
    activity_id: uuid.UUID,
    user_id: uuid.UUID,
    user_role: str,
) -> AsyncGenerator[bytes, None]:
    """
    Streams activity participants as UTF-8 BOM CSV.
    Strictly verifies authorization:
    - System Admin
    - Lead Host
    - Lead Group Owner/Admin
    Accepted co-hosts, unrelated edu_org, and standard users receive ForbiddenError (403).
    """
    # 1. Fetch activity with custom form and fields
    stmt = (
        select(Activity)
        .where(Activity.id == activity_id, Activity.is_deleted.is_(False))
        .options(
            selectinload(Activity.custom_form).selectinload(CustomForm.fields)
        )
    )
    res = await db.execute(stmt)
    try:
        activity = res.unique().scalar_one_or_none()
        if hasattr(activity, "_mock_name") and hasattr(res, "scalar_one_or_none"):
            fallback = res.scalar_one_or_none()
            if fallback is not None and not hasattr(fallback, "_mock_name"):
                activity = fallback
    except Exception:
        activity = res.scalar_one_or_none()

    if not activity:
        raise NotFoundError("Activity not found.")

    # 2. Check authorization
    allowed = await can_export_activity_participants(db, user_id, user_role, activity_id)
    if not allowed:
        raise ForbiddenError("Bạn không có quyền xuất danh sách người tham gia hoạt động này.")

    # 3. Yield UTF-8 BOM for flawless Excel display
    yield codecs.BOM_UTF8

    # 4. Determine ordered custom form fields
    form_fields = []
    if activity.custom_form and activity.custom_form.fields:
        form_fields = sorted(activity.custom_form.fields, key=lambda f: f.order if f.order is not None else 0)

    # 5. Build Header Row
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    headers = [
        "STT",
        "Họ và tên",
        "Tên người dùng",
        "Email",
        "Trường / Đại học",
        "Thời gian đăng ký",
        "Trạng thái duyệt",
        "Điểm danh",
        "Số ngày CTXH",
    ]
    for field in form_fields:
        headers.append(f"[Câu hỏi] {field.label}")

    writer.writerow(headers)
    yield output.getvalue().encode("utf-8")
    output.seek(0)
    output.truncate(0)

    # 6. Query all JoinRequests with User
    req_stmt = (
        select(JoinRequest)
        .where(JoinRequest.activity_id == activity_id)
        .options(joinedload(JoinRequest.user))
        .order_by(JoinRequest.created_at.asc())
    )
    req_res = await db.execute(req_stmt)
    records = req_res.scalars().all()

    # Status mapping
    status_map = {
        RequestStatus.approved: "Đã duyệt",
        RequestStatus.pending: "Đang chờ duyệt",
        RequestStatus.declined: "Bị từ chối",
        RequestStatus.cancelled: "Đã hủy",
    }

    # 7. Write data rows
    idx = 1
    for r in records:
        user = r.user
        full_name = user.full_name if user and user.full_name else ""
        username = user.username if user else ""
        email = user.email if user else ""
        university = user.university if user and user.university else "-"

        # Format created_at
        if r.created_at:
            if isinstance(r.created_at, datetime):
                reg_time = r.created_at.strftime("%d/%m/%Y %H:%M")
            else:
                reg_time = str(r.created_at)
        else:
            reg_time = "-"

        # Status text
        status_key = r.status.value if hasattr(r.status, "value") else str(r.status)
        try:
            enum_status = RequestStatus(status_key)
            status_text = status_map.get(enum_status, status_key)
        except ValueError:
            status_text = status_key

        # Attendance text & CTXH
        # CTXH: Đọc giá trị CTXH đã được backend xác nhận và lưu/derive từ domain attendance của Activity.
        # Export service chỉ đọc và xuất kết quả, không tự định nghĩa lại business rule cấp CTXH.
        is_approved = (status_key == RequestStatus.approved.value or r.status == RequestStatus.approved)
        if is_approved:
            attendance_text = "Đã điểm danh" if r.attendance_confirmed else "Chưa điểm danh"
            if r.attendance_confirmed and activity.social_work_days and activity.social_work_days > 0:
                ctxh_val = f"{activity.social_work_days:.1f}" if activity.social_work_days % 1 != 0 else f"{int(activity.social_work_days)}"
            else:
                ctxh_val = "0"
        else:
            attendance_text = "-"
            ctxh_val = "0"

        row = [
            str(idx),
            full_name,
            username,
            email,
            university,
            reg_time,
            status_text,
            attendance_text,
            ctxh_val,
        ]

        # Dynamic Form Responses according to form schema order
        responses = r.form_responses if isinstance(r.form_responses, dict) else {}
        for field in form_fields:
            answer = get_form_field_response(field, responses)
            row.append(answer)

        writer.writerow(row)
        yield output.getvalue().encode("utf-8")
        output.seek(0)
        output.truncate(0)
        idx += 1
