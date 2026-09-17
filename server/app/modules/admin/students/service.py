"""Service for Master Student Audit queries."""

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.activities.models import Activity
from app.modules.admin.students.schemas import StudentAuditItem, StudentAuditList
from app.modules.participation.models import JoinRequest
from app.modules.users.models import User


def build_student_audit_query(
    search: str | None = None,
    university: str | None = None,
    is_active: bool | None = None,
    role: str | None = None,
):
    """Build base query for student audit aggregation."""
    ctxh_sum = func.coalesce(
        func.sum(
            case(
                (
                    and_(
                        JoinRequest.attendance_confirmed == True,
                        Activity.is_deleted == False,
                    ),
                    Activity.social_work_days,
                ),
                else_=0.0,
            )
        ),
        0.0,
    ).label("confirmed_ctxh_days")

    attendance_cnt = func.coalesce(
        func.sum(
            case(
                (
                    and_(
                        JoinRequest.attendance_confirmed == True,
                        Activity.is_deleted == False,
                    ),
                    1,
                ),
                else_=0,
            )
        ),
        0,
    ).label("attendance_count")

    base = (
        select(
            User.id,
            User.username,
            User.full_name,
            User.email,
            User.university,
            User.is_active,
            User.is_verified,
            User.role,
            User.created_at,
            ctxh_sum,
            attendance_cnt,
        )
        .outerjoin(JoinRequest, JoinRequest.user_id == User.id)
        .outerjoin(Activity, Activity.id == JoinRequest.activity_id)
        .group_by(User.id)
    )

    if search:
        pattern = f"%{search}%"
        base = base.where(
            or_(
                User.username.ilike(pattern),
                User.email.ilike(pattern),
                User.full_name.ilike(pattern),
            )
        )

    if university:
        base = base.where(User.university.ilike(f"%{university}%"))

    if is_active is not None:
        base = base.where(User.is_active == is_active)

    if role:
        base = base.where(User.role == role)

    return base


async def list_students_audit(
    db: AsyncSession,
    search: str | None = None,
    university: str | None = None,
    is_active: bool | None = None,
    role: str | None = None,
    limit: int = 25,
    offset: int = 0,
) -> StudentAuditList:
    """Execute paginated student audit query."""
    base = build_student_audit_query(
        search=search, university=university, is_active=is_active, role=role
    )

    # Count subquery
    subq = base.subquery()
    count_stmt = select(func.count()).select_from(subq)
    total = (await db.execute(count_stmt)).scalar() or 0

    # Paginated data
    stmt = base.order_by(User.created_at.desc()).limit(limit).offset(offset)
    rows = (await db.execute(stmt)).all()

    items = [
        StudentAuditItem(
            id=r[0],
            username=r[1],
            full_name=r[2],
            email=r[3],
            university=r[4],
            is_active=r[5],
            is_verified=r[6],
            role=r[7].value if hasattr(r[7], "value") else str(r[7]),
            created_at=r[8],
            confirmed_ctxh_days=round(float(r[9]), 1),
            attendance_count=int(r[10]),
        )
        for r in rows
    ]

    return StudentAuditList(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )
