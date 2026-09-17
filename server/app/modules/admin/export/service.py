"""Service for streaming CSV exports with UTF-8 BOM encoding."""

import codecs
import csv
import io
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.students.service import build_student_audit_query
from app.modules.users.models import User


async def stream_students_csv(
    db: AsyncSession,
    search: str | None = None,
    university: str | None = None,
    is_active: bool | None = None,
    role: str | None = None,
) -> AsyncGenerator[bytes, None]:
    """Stream student audit records as UTF-8 BOM CSV for flawless Excel/Sheets display."""
    # 1. Yield UTF-8 BOM prefix
    yield codecs.BOM_UTF8

    # 2. Header row
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow([
        "MSSV / Username",
        "Họ và tên",
        "Email",
        "Trường / Khoa",
        "Vai trò",
        "Trạng thái",
        "Tổ chức xác minh",
        "Tổng ngày CTXH",
        "Số hoạt động tham gia",
    ])
    yield output.getvalue().encode("utf-8")
    output.seek(0)
    output.truncate(0)

    # 3. Stream data query
    query = build_student_audit_query(
        search=search, university=university, is_active=is_active, role=role
    ).order_by(User.created_at.desc())

    result = await db.stream(query)
    async for r in result:
        role_val = r[7].value if hasattr(r[7], "value") else str(r[7])
        status_str = "Đang hoạt động" if r[5] else "Đã khóa"
        verified_str = "Đã xác minh" if r[6] else "Chưa"
        ctxh_val = f"{float(r[9]):.1f}"
        attendance_val = str(int(r[10]))

        writer.writerow([
            r[1],  # username
            r[2] or "",  # full_name
            r[3],  # email
            r[4] or "",  # university
            role_val,
            status_str,
            verified_str,
            ctxh_val,
            attendance_val,
        ])
        yield output.getvalue().encode("utf-8")
        output.seek(0)
        output.truncate(0)
