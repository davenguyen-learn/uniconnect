"""Service for Moderation Reports queue, atomic resolution, and audit logging."""

import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.exceptions import NotFoundError, ValidationError
from app.modules.activities.models import Activity
from app.modules.admin.audit.service import record_audit_log
from app.modules.admin.models import AdminAuditAction, AdminAuditTargetType
from app.modules.admin.moderation.schemas import AdminReportItem, AdminReportList
from app.modules.reports.models import Report
from app.modules.users.models import User


async def list_reports(
    db: AsyncSession,
    status: str | None = None,
    target_type: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> AdminReportList:
    """List paginated moderation reports with reporter attached."""
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
        reporter_name = r.reporter.full_name or r.reporter.username if r.reporter else None
        item = AdminReportItem(
            id=r.id,
            reporter_id=r.reporter_id,
            target_type=r.target_type,
            target_id=r.target_id,
            reason=r.reason,
            description=r.description,
            status=r.status,
            admin_note=r.admin_note,
            resolved_by=r.resolved_by,
            created_at=r.created_at,
            updated_at=r.updated_at,
            reporter_name=reporter_name,
        )
        items.append(item)

    return AdminReportList(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )


async def review_report(
    db: AsyncSession,
    report_id: uuid.UUID,
    admin_id: uuid.UUID,
    action: str,
    admin_note: str | None = None,
    hide_activity: bool = False,
    deactivate_user: bool = False,
) -> AdminReportItem:
    """Atomic report review with terminal-state protection, side-effects, and audit logging."""
    report = await db.get(Report, report_id)
    if not report:
        raise NotFoundError("Report not found.")

    # Terminal state check
    if report.status != "pending":
        raise ValidationError(f"Cannot review report already in terminal state '{report.status}'.")

    if action == "resolve":
        report.status = "resolved"
        audit_act = AdminAuditAction.resolve_report

        # Optional side-effect: hide activity
        if hide_activity and report.target_type == "activity":
            act = await db.get(Activity, report.target_id)
            if act:
                act.is_deleted = True
                await record_audit_log(
                    db=db,
                    actor_id=admin_id,
                    action=AdminAuditAction.hide_activity,
                    target_type=AdminAuditTargetType.activity,
                    target_id=act.id,
                    metadata_json={"report_id": str(report.id), "activity_title": act.title},
                )

        # Optional side-effect: deactivate user
        if deactivate_user and report.target_type == "user":
            usr = await db.get(User, report.target_id)
            if usr:
                usr.is_active = False
                await record_audit_log(
                    db=db,
                    actor_id=admin_id,
                    action=AdminAuditAction.deactivate_user,
                    target_type=AdminAuditTargetType.user,
                    target_id=usr.id,
                    metadata_json={"report_id": str(report.id), "username": usr.username},
                )

    elif action == "dismiss":
        report.status = "dismissed"
        audit_act = AdminAuditAction.dismiss_report
    else:
        raise ValidationError(f"Invalid review action '{action}'.")

    report.admin_note = admin_note
    report.resolved_by = admin_id

    # Record report review audit log
    await record_audit_log(
        db=db,
        actor_id=admin_id,
        action=audit_act,
        target_type=AdminAuditTargetType.report,
        target_id=report.id,
        metadata_json={
            "target_type": report.target_type,
            "target_id": str(report.target_id),
            "action": action,
            "admin_note_provided": bool(admin_note),
            "hide_activity": hide_activity,
            "deactivate_user": deactivate_user,
        },
    )

    await db.flush()

    # Fetch reporter for item
    reporter = await db.get(User, report.reporter_id)

    return AdminReportItem(
        id=report.id,
        reporter_id=report.reporter_id,
        target_type=report.target_type,
        target_id=report.target_id,
        reason=report.reason,
        description=report.description,
        status=report.status,
        admin_note=report.admin_note,
        resolved_by=report.resolved_by,
        created_at=report.created_at,
        updated_at=report.updated_at,
        reporter_name=reporter.full_name or reporter.username if reporter else None,
    )
