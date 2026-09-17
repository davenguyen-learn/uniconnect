"""Admin business logic — dashboard stats, user/report/content management."""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.exceptions import NotFoundError, ValidationError
from app.modules.users.models import User, UserRole
from app.modules.activities.models import Activity
from app.modules.reports.models import Report
from app.modules.admin.schemas import (
    AdminStats,
    AdminUserItem, AdminUserList,
    AdminReportItem, AdminReportList, ReportReporterInfo,
    AdminActivityItem, AdminActivityList,
)


# ── Dashboard Stats ──

async def get_stats(db: AsyncSession) -> AdminStats:
    """Get aggregate dashboard statistics."""
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    total_users = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
    total_activities = (await db.execute(
        select(func.count()).select_from(Activity).where(Activity.is_deleted == False)
    )).scalar() or 0
    total_reports = (await db.execute(select(func.count()).select_from(Report))).scalar() or 0
    pending_reports = (await db.execute(
        select(func.count()).select_from(Report).where(Report.status == "pending")
    )).scalar() or 0
    new_users_this_week = (await db.execute(
        select(func.count()).select_from(User).where(User.created_at >= week_ago)
    )).scalar() or 0

    return AdminStats(
        total_users=total_users,
        total_activities=total_activities,
        total_reports=total_reports,
        pending_reports=pending_reports,
        new_users_this_week=new_users_this_week,
    )


# ── User Management ──

async def list_users(
    db: AsyncSession,
    search: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
    limit: int = 20,
    offset: int = 0,
) -> AdminUserList:
    """List all users with optional filters."""
    base = select(User)
    count_base = select(func.count()).select_from(User)

    if search:
        pattern = f"%{search}%"
        search_filter = or_(
            User.username.ilike(pattern),
            User.email.ilike(pattern),
            User.full_name.ilike(pattern),
        )
        base = base.where(search_filter)
        count_base = count_base.where(search_filter)

    if role:
        base = base.where(User.role == role)
        count_base = count_base.where(User.role == role)

    if is_active is not None:
        base = base.where(User.is_active == is_active)
        count_base = count_base.where(User.is_active == is_active)

    total = (await db.execute(count_base)).scalar() or 0

    stmt = base.order_by(User.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    users = result.scalars().all()

    return AdminUserList(
        items=[AdminUserItem.model_validate(u) for u in users],
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )


from app.modules.admin.models import AdminAuditAction, AdminAuditTargetType
from app.modules.admin.audit.service import record_audit_log


async def update_user_role(
    db: AsyncSession, user_id: uuid.UUID, new_role: str, admin_id: uuid.UUID | None = None
) -> AdminUserItem:
    """Change a user's role with audit trail."""
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundError("User not found.")

    prev_role = user.role.value if hasattr(user.role, 'value') else str(user.role)
    user.role = UserRole(new_role)

    await record_audit_log(
        db=db,
        actor_id=admin_id,
        action=AdminAuditAction.change_user_role,
        target_type=AdminAuditTargetType.user,
        target_id=user.id,
        metadata_json={
            "username": user.username,
            "previous_role": prev_role,
            "new_role": new_role,
        },
    )
    await db.flush()
    return AdminUserItem.model_validate(user)


async def update_user_status(
    db: AsyncSession, user_id: uuid.UUID, is_active: bool, admin_id: uuid.UUID | None = None
) -> AdminUserItem:
    """Activate or deactivate a user with audit trail."""
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundError("User not found.")

    user.is_active = is_active
    audit_act = AdminAuditAction.activate_user if is_active else AdminAuditAction.deactivate_user
    await record_audit_log(
        db=db,
        actor_id=admin_id,
        action=audit_act,
        target_type=AdminAuditTargetType.user,
        target_id=user.id,
        metadata_json={
            "username": user.username,
            "is_active": is_active,
        },
    )
    await db.flush()
    return AdminUserItem.model_validate(user)


# ── Report Management ──

async def list_reports(
    db: AsyncSession,
    status: str | None = None,
    target_type: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> AdminReportList:
    """List reports with reporter info attached."""
    base = select(Report).options(joinedload(Report.reporter))
    count_base = select(func.count()).select_from(Report)

    if status:
        base = base.where(Report.status == status)
        count_base = count_base.where(Report.status == status)

    if target_type:
        base = base.where(Report.target_type == target_type)
        count_base = count_base.where(Report.target_type == target_type)

    total = (await db.execute(count_base)).scalar() or 0

    stmt = base.order_by(Report.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    reports = result.unique().scalars().all()

    items = []
    for r in reports:
        item = AdminReportItem.model_validate(r)
        if r.reporter:
            item.reporter = ReportReporterInfo.model_validate(r.reporter)
        items.append(item)

    return AdminReportList(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )


async def update_report(
    db: AsyncSession,
    report_id: uuid.UUID,
    admin_id: uuid.UUID,
    status: str,
    admin_note: str | None = None,
) -> AdminReportItem:
    """Resolve or dismiss a report."""
    report = await db.get(Report, report_id)
    if not report:
        raise NotFoundError("Report not found.")

    report.status = status
    report.resolved_by = admin_id
    report.admin_note = admin_note
    await db.flush()

    # Reload with reporter
    stmt = select(Report).options(joinedload(Report.reporter)).where(Report.id == report_id)
    result = await db.execute(stmt)
    report = result.unique().scalar_one()

    item = AdminReportItem.model_validate(report)
    if report.reporter:
        item.reporter = ReportReporterInfo.model_validate(report.reporter)
    return item


# ── Activity Management ──

async def list_activities(
    db: AsyncSession,
    search: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> AdminActivityList:
    """List all activities (including soft-deleted) with host info."""
    base = select(Activity).options(joinedload(Activity.host))
    count_base = select(func.count()).select_from(Activity)

    if search:
        pattern = f"%{search}%"
        search_filter = Activity.title.ilike(pattern)
        base = base.where(search_filter)
        count_base = count_base.where(search_filter)

    total = (await db.execute(count_base)).scalar() or 0

    stmt = base.order_by(Activity.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    activities = result.unique().scalars().all()

    items = []
    for a in activities:
        item_data = {
            "id": a.id,
            "host_id": a.host_id,
            "title": a.title,
            "description": a.description,
            "category": a.category,
            "location_name": a.location_name,
            "start_time": a.start_time,
            "end_time": a.end_time,
            "max_participants": a.max_participants,
            "current_participants": a.current_participants,
            "privacy": a.privacy.value if hasattr(a.privacy, 'value') else a.privacy,
            "created_at": a.created_at,
            "host_username": a.host.username if a.host else None,
        }
        items.append(AdminActivityItem(**item_data))

    return AdminActivityList(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )


async def delete_activity(
    db: AsyncSession, activity_id: uuid.UUID, admin_id: uuid.UUID | None = None
) -> dict:
    """Soft-delete an activity with audit trail."""
    activity = await db.get(Activity, activity_id)
    if not activity:
        raise NotFoundError("Activity not found.")

    activity.is_deleted = True
    activity.deleted_at = datetime.now(timezone.utc)
    await record_audit_log(
        db=db,
        actor_id=admin_id,
        action=AdminAuditAction.hide_activity,
        target_type=AdminAuditTargetType.activity,
        target_id=activity.id,
        metadata_json={"title": activity.title},
    )
    await db.flush()
    return {"status": "deleted", "id": str(activity_id)}
