"""Admin business logic — dashboard stats, user/report/content management."""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.exceptions import NotFoundError, ValidationError
from app.modules.users.models import User, UserRole
from app.modules.activities.models import Activity
from app.modules.documents.models import Document
from app.modules.reports.models import Report
from app.modules.admin.schemas import (
    AdminStats,
    AdminUserItem, AdminUserList,
    AdminReportItem, AdminReportList, ReportReporterInfo,
    AdminActivityItem, AdminActivityList,
    AdminDocumentItem, AdminDocumentList,
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
    total_documents = (await db.execute(
        select(func.count()).select_from(Document).where(Document.is_deleted == False)
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
        total_documents=total_documents,
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


async def update_user_role(
    db: AsyncSession, user_id: uuid.UUID, new_role: str
) -> AdminUserItem:
    """Change a user's role."""
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundError("User not found.")

    user.role = UserRole(new_role)
    await db.flush()
    return AdminUserItem.model_validate(user)


async def update_user_status(
    db: AsyncSession, user_id: uuid.UUID, is_active: bool
) -> AdminUserItem:
    """Activate or deactivate a user."""
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundError("User not found.")

    user.is_active = is_active
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


async def delete_activity(db: AsyncSession, activity_id: uuid.UUID) -> dict:
    """Soft-delete an activity."""
    activity = await db.get(Activity, activity_id)
    if not activity:
        raise NotFoundError("Activity not found.")

    activity.is_deleted = True
    activity.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    return {"status": "deleted", "id": str(activity_id)}


# ── Document Management ──

async def list_documents(
    db: AsyncSession,
    search: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> AdminDocumentList:
    """List all documents with author info."""
    base = select(Document).options(joinedload(Document.author))
    count_base = select(func.count()).select_from(Document)

    if search:
        pattern = f"%{search}%"
        search_filter = Document.title.ilike(pattern)
        base = base.where(search_filter)
        count_base = count_base.where(search_filter)

    total = (await db.execute(count_base)).scalar() or 0

    stmt = base.order_by(Document.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    documents = result.unique().scalars().all()

    items = []
    for d in documents:
        item_data = {
            "id": d.id,
            "author_id": d.author_id,
            "title": d.title,
            "description": d.description,
            "file_name": d.file_name,
            "file_size": d.file_size,
            "file_type": d.file_type,
            "is_deleted": d.is_deleted,
            "created_at": d.created_at,
            "author_username": d.author.username if d.author else None,
        }
        items.append(AdminDocumentItem(**item_data))

    return AdminDocumentList(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )


async def delete_document(db: AsyncSession, document_id: uuid.UUID) -> dict:
    """Soft-delete a document."""
    doc = await db.get(Document, document_id)
    if not doc:
        raise NotFoundError("Document not found.")

    doc.is_deleted = True
    doc.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    return {"status": "deleted", "id": str(document_id)}
