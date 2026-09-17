"""Admin Command Center API endpoints with granular RBAC."""

import uuid
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.admin import service
from app.modules.admin.analytics.schemas import AdminMetricsResponse
from app.modules.admin.analytics.service import get_kpi_metrics
from app.modules.admin.audit.schemas import AdminAuditLogList
from app.modules.admin.audit.service import list_audit_logs
from app.modules.admin.export.service import stream_students_csv
from app.modules.admin.moderation.schemas import AdminReportItem, AdminReportList, ReportReviewAction
from app.modules.admin.moderation.service import list_reports as list_moderation_reports
from app.modules.admin.moderation.service import review_report
from app.modules.admin.permissions import (
    require_admin_access,
    require_moderation_permission,
    require_staff_or_admin,
    require_user_management_permission,
    require_verification_permission,
)
from app.modules.admin.schemas import (
    AdminActivityList,
    AdminStats,
    AdminUserItem,
    AdminUserList,
    ReportUpdate,
    RoleUpdate,
    StatusUpdate,
)
from app.modules.admin.students.schemas import StudentAuditList
from app.modules.admin.students.service import list_students_audit
from app.modules.admin.verification.schemas import (
    VerificationItem,
    VerificationList,
    VerificationRequestCreate,
    VerificationReviewAction,
)
from app.modules.admin.verification.service import (
    list_verification_requests,
    review_verification_request,
    submit_verification_request,
)

router = APIRouter(prefix="/admin", tags=["Admin"])


# ── 1. KPI Metrics Command Center ──

@router.get("/metrics", response_model=AdminMetricsResponse)
async def get_metrics(
    current_user: dict = Depends(require_staff_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get high-density campus KPI metrics with sparklines & growth delta."""
    return await get_kpi_metrics(db)


@router.get("/stats", response_model=AdminStats)
async def get_dashboard_stats(
    current_user: dict = Depends(require_staff_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Legacy aggregate dashboard statistics."""
    return await service.get_stats(db)


# ── 2. Master Student Audit & CSV Export ──

@router.get("/students", response_model=StudentAuditList)
async def list_students(
    search: str | None = Query(None, description="Search by username/MSSV, email, or name"),
    university: str | None = Query(None, description="Filter by university/faculty"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    role: str | None = Query(None, description="Filter by role"),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_staff_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Query Master Student Audit table with confirmed CTXH days and attendance count."""
    return await list_students_audit(
        db=db,
        search=search,
        university=university,
        is_active=is_active,
        role=role,
        limit=limit,
        offset=offset,
    )


@router.get("/students/export")
async def export_students_csv(
    search: str | None = Query(None, description="Search filter for export"),
    university: str | None = Query(None, description="University filter for export"),
    is_active: bool | None = Query(None, description="Status filter for export"),
    role: str | None = Query(None, description="Role filter for export"),
    current_user: dict = Depends(require_staff_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Stream Master Student Audit as UTF-8 BOM CSV file."""
    return StreamingResponse(
        stream_students_csv(
            db=db,
            search=search,
            university=university,
            is_active=is_active,
            role=role,
        ),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=danh_sach_sinh_vien.csv"},
    )


# ── 3. Organization Verification Queue & Actions ──

@router.get("/verifications", response_model=VerificationList)
async def list_verifications(
    status: str | None = Query(None, description="Filter by status: pending, approved, rejected"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_staff_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """List pending and historical organization verification requests."""
    return await list_verification_requests(db, status=status, limit=limit, offset=offset)


@router.post("/verifications/request", response_model=VerificationItem)
async def request_verification(
    data: VerificationRequestCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit an organization verification application."""
    user_id = uuid.UUID(current_user["sub"])
    return await submit_verification_request(db, user_id=user_id, data=data)


@router.post("/verifications/{request_id}/review", response_model=VerificationItem)
async def review_verification(
    request_id: uuid.UUID,
    data: VerificationReviewAction,
    current_user: dict = Depends(require_verification_permission),
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject an organization verification request (terminal state protected)."""
    admin_id = uuid.UUID(current_user["sub"])
    return await review_verification_request(
        db=db,
        request_id=request_id,
        admin_id=admin_id,
        action=data.action,
        admin_note=data.admin_note,
    )


# ── 4. Reports Moderation Queue & Actions ──

@router.get("/reports", response_model=AdminReportList)
async def list_reports_endpoint(
    status: str | None = Query(None, description="Filter: pending, resolved, dismissed"),
    target_type: str | None = Query(None, description="Filter: activity, user, document"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_staff_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """List moderation reports queue."""
    return await list_moderation_reports(
        db, status=status, target_type=target_type, limit=limit, offset=offset
    )


@router.post("/reports/{report_id}/review", response_model=AdminReportItem)
async def review_report_endpoint(
    report_id: uuid.UUID,
    data: ReportReviewAction,
    current_user: dict = Depends(require_moderation_permission),
    db: AsyncSession = Depends(get_db),
):
    """Resolve or dismiss a report with optional atomic side-effects (hide activity, deactivate user)."""
    admin_id = uuid.UUID(current_user["sub"])
    return await review_report(
        db=db,
        report_id=report_id,
        admin_id=admin_id,
        action=data.action,
        admin_note=data.admin_note,
        hide_activity=data.hide_activity,
        deactivate_user=data.deactivate_user,
    )


@router.patch("/reports/{report_id}", response_model=AdminReportItem)
async def update_report_legacy(
    report_id: uuid.UUID,
    data: ReportUpdate,
    current_user: dict = Depends(require_moderation_permission),
    db: AsyncSession = Depends(get_db),
):
    """Legacy PATCH endpoint mapping to atomic review_report."""
    admin_id = uuid.UUID(current_user["sub"])
    return await review_report(
        db=db,
        report_id=report_id,
        admin_id=admin_id,
        action=data.status,
        admin_note=data.admin_note,
    )


# ── 5. Admin Audit Trail ──

@router.get("/audit-logs", response_model=AdminAuditLogList)
async def list_audit_logs_endpoint(
    action: str | None = Query(None, description="Filter by action name"),
    target_type: str | None = Query(None, description="Filter by target type"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
):
    """Query administrative action audit logs."""
    return await list_audit_logs(
        db=db, action=action, target_type=target_type, limit=limit, offset=offset
    )


# ── 6. User & Activity Management ──

@router.get("/users", response_model=AdminUserList)
async def list_users(
    search: str | None = Query(None, description="Search by username, email, or name"),
    role: str | None = Query(None, description="Filter by role"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_user_management_permission),
    db: AsyncSession = Depends(get_db),
):
    """List all users with search and filters."""
    return await service.list_users(
        db, search=search, role=role, is_active=is_active, limit=limit, offset=offset
    )


@router.patch("/users/{user_id}/role", response_model=AdminUserItem)
async def update_user_role(
    user_id: uuid.UUID,
    data: RoleUpdate,
    current_user: dict = Depends(require_user_management_permission),
    db: AsyncSession = Depends(get_db),
):
    """Change a user's role with audit log."""
    admin_id = uuid.UUID(current_user["sub"])
    return await service.update_user_role(db, user_id, data.role, admin_id=admin_id)


@router.patch("/users/{user_id}/status", response_model=AdminUserItem)
async def update_user_status(
    user_id: uuid.UUID,
    data: StatusUpdate,
    current_user: dict = Depends(require_user_management_permission),
    db: AsyncSession = Depends(get_db),
):
    """Activate or deactivate a user with audit log."""
    admin_id = uuid.UUID(current_user["sub"])
    return await service.update_user_status(db, user_id, data.is_active, admin_id=admin_id)


@router.get("/activities", response_model=AdminActivityList)
async def list_activities(
    search: str | None = Query(None, description="Search by title"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_staff_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all activities."""
    return await service.list_activities(db, search=search, limit=limit, offset=offset)


@router.delete("/activities/{activity_id}")
async def delete_activity(
    activity_id: uuid.UUID,
    current_user: dict = Depends(require_moderation_permission),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete an activity with audit log."""
    admin_id = uuid.UUID(current_user["sub"])
    return await service.delete_activity(db, activity_id, admin_id=admin_id)
