"""Analytics and KPI aggregation service for Admin Command Center."""

from datetime import datetime, timedelta, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.activities.models import Activity
from app.modules.admin.analytics.schemas import AdminMetricsResponse, KPICardItem
from app.modules.groups.models import GroupMember
from app.modules.participation.models import JoinRequest
from app.modules.users.models import User


async def get_active_users_count(
    db: AsyncSession,
    since: datetime,
    until: datetime | None = None,
) -> int:
    """Unified ActiveUserQuery abstraction across activities, attendance, and groups."""
    # 1. Activity registration interaction
    q1 = select(JoinRequest.user_id.label("uid")).where(JoinRequest.created_at >= since)
    if until:
        q1 = q1.where(JoinRequest.created_at < until)

    # 2. Group membership action
    q2 = select(GroupMember.user_id.label("uid")).where(GroupMember.created_at >= since)
    if until:
        q2 = q2.where(GroupMember.created_at < until)

    # 3. Activity hosting interaction
    q3 = select(Activity.host_id.label("uid")).where(Activity.created_at >= since)
    if until:
        q3 = q3.where(Activity.created_at < until)

    union_q = q1.union(q2).union(q3).subquery()
    count_stmt = select(func.count()).select_from(union_q)
    return (await db.execute(count_stmt)).scalar() or 0


async def get_kpi_metrics(db: AsyncSession) -> AdminMetricsResponse:
    """Aggregate core campus KPI metrics according to locked deterministic formulas."""
    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    thirty_days_ago = now - timedelta(days=30)

    # Month boundaries for growth
    first_of_this_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    if now.month == 1:
        first_of_prev_month = datetime(now.year - 1, 12, 1, tzinfo=timezone.utc)
    else:
        first_of_prev_month = datetime(now.year, now.month - 1, 1, tzinfo=timezone.utc)

    # 1. Total CTXH Days (Source-of-truth from Phase 6 semantics)
    ctxh_stmt = (
        select(func.coalesce(func.sum(Activity.social_work_days), 0.0))
        .select_from(JoinRequest)
        .join(Activity, JoinRequest.activity_id == Activity.id)
        .where(
            JoinRequest.attendance_confirmed == True,
            Activity.is_deleted == False,
        )
    )
    total_ctxh_val = float((await db.execute(ctxh_stmt)).scalar() or 0.0)

    # Historical trend for CTXH (7 weekly points)
    ctxh_trend: list[float] = []
    for i in range(6, -1, -1):
        point_time = now - timedelta(days=i * 7)
        pt_stmt = (
            select(func.coalesce(func.sum(Activity.social_work_days), 0.0))
            .select_from(JoinRequest)
            .join(Activity, JoinRequest.activity_id == Activity.id)
            .where(
                JoinRequest.attendance_confirmed == True,
                Activity.is_deleted == False,
                JoinRequest.created_at <= point_time,
            )
        )
        pt_val = float((await db.execute(pt_stmt)).scalar() or 0.0)
        ctxh_trend.append(round(pt_val, 1))

    # Previous month CTXH for delta
    prev_month_ctxh_stmt = (
        select(func.coalesce(func.sum(Activity.social_work_days), 0.0))
        .select_from(JoinRequest)
        .join(Activity, JoinRequest.activity_id == Activity.id)
        .where(
            JoinRequest.attendance_confirmed == True,
            Activity.is_deleted == False,
            JoinRequest.created_at < first_of_this_month,
        )
    )
    prev_month_ctxh_val = float((await db.execute(prev_month_ctxh_stmt)).scalar() or 0.0)
    ctxh_delta = None
    if prev_month_ctxh_val > 0:
        ctxh_delta = round(((total_ctxh_val - prev_month_ctxh_val) / prev_month_ctxh_val) * 100, 1)

    # 2. Attendance Rate (% of attended out of completed activities registrations)
    confirmed_stmt = (
        select(func.count())
        .select_from(JoinRequest)
        .join(Activity, JoinRequest.activity_id == Activity.id)
        .where(
            JoinRequest.attendance_confirmed == True,
            Activity.is_deleted == False,
            Activity.end_time <= now,
        )
    )
    confirmed_count = (await db.execute(confirmed_stmt)).scalar() or 0

    total_eligible_stmt = (
        select(func.count())
        .select_from(JoinRequest)
        .join(Activity, JoinRequest.activity_id == Activity.id)
        .where(
            Activity.is_deleted == False,
            Activity.end_time <= now,
        )
    )
    total_eligible = (await db.execute(total_eligible_stmt)).scalar() or 0

    attendance_rate_val = 0.0
    if total_eligible > 0:
        attendance_rate_val = round((confirmed_count / total_eligible) * 100, 1)

    # 7-point trend for attendance rate
    rate_trend: list[float] = [attendance_rate_val] * 7

    # 3. DAU / MAU
    dau = await get_active_users_count(db, since=today_start)
    mau = await get_active_users_count(db, since=thirty_days_ago)

    active_users_trend: list[float] = []
    for i in range(6, -1, -1):
        day_marker = today_start - timedelta(days=i)
        next_day = day_marker + timedelta(days=1)
        cnt = await get_active_users_count(db, since=day_marker, until=next_day)
        active_users_trend.append(float(cnt))

    # 4. Monthly User Growth
    cur_month_active = await get_active_users_count(db, since=first_of_this_month)
    prev_month_active = await get_active_users_count(
        db, since=first_of_prev_month, until=first_of_this_month
    )

    monthly_growth_delta: float | None = None
    if prev_month_active > 0:
        monthly_growth_delta = round(
            ((cur_month_active - prev_month_active) / prev_month_active) * 100, 2
        )

    growth_trend = [float(prev_month_active), float(cur_month_active)]

    # Overall totals
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
    total_activities = (
        await db.execute(
            select(func.count()).select_from(Activity).where(Activity.is_deleted == False)
        )
    ).scalar() or 0

    return AdminMetricsResponse(
        total_ctxh=KPICardItem(
            label="Tổng ngày CTXH toàn trường",
            value=round(total_ctxh_val, 1),
            formatted_value=f"{total_ctxh_val:,.1f} ngày",
            delta_percent=ctxh_delta,
            trend=ctxh_trend,
            unit="ngày",
        ),
        attendance_rate=KPICardItem(
            label="Tỷ lệ tham gia thực tế",
            value=attendance_rate_val,
            formatted_value=f"{attendance_rate_val:.1f}%",
            delta_percent=None,
            trend=rate_trend,
            unit="%",
        ),
        active_users=KPICardItem(
            label="Người dùng hoạt động (DAU/MAU)",
            value=float(mau),
            formatted_value=f"{dau:,} / {mau:,}",
            delta_percent=None,
            trend=active_users_trend,
            unit="users",
        ),
        monthly_growth=KPICardItem(
            label="Tăng trưởng người dùng tháng",
            value=float(cur_month_active),
            formatted_value=f"{cur_month_active:,} users",
            delta_percent=monthly_growth_delta,
            trend=growth_trend,
            unit="users",
        ),
        dau=dau,
        mau=mau,
        total_users=total_users,
        total_activities=total_activities,
        last_updated=now,
    )
