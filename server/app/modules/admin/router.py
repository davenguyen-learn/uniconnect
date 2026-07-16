"""Admin API endpoints — all require admin role."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_role
from app.modules.admin import service
from app.modules.admin.schemas import (
    AdminStats,
    AdminUserList, AdminUserItem, RoleUpdate, StatusUpdate,
    AdminReportList, AdminReportItem, ReportUpdate,
    AdminActivityList,
    AdminDocumentList,
)

router = APIRouter(prefix="/admin", tags=["Admin"])

# All routes use this dependency — only admin users can access
admin_user = require_role("admin")


# ── Dashboard ──

@router.get("/stats", response_model=AdminStats)
async def get_dashboard_stats(
    current_user: dict = Depends(admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregate dashboard statistics."""
    return await service.get_stats(db)


# ── User Management ──

@router.get("/users", response_model=AdminUserList)
async def list_users(
    search: str | None = Query(None, description="Search by username, email, or name"),
    role: str | None = Query(None, description="Filter by role"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List all users with search and filters."""
    return await service.list_users(db, search=search, role=role, is_active=is_active, limit=limit, offset=offset)


@router.patch("/users/{user_id}/role", response_model=AdminUserItem)
async def update_user_role(
    user_id: uuid.UUID,
    data: RoleUpdate,
    current_user: dict = Depends(admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Change a user's role."""
    return await service.update_user_role(db, user_id, data.role)


@router.patch("/users/{user_id}/status", response_model=AdminUserItem)
async def update_user_status(
    user_id: uuid.UUID,
    data: StatusUpdate,
    current_user: dict = Depends(admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Activate or deactivate a user."""
    return await service.update_user_status(db, user_id, data.is_active)


# ── Report Management ──

@router.get("/reports", response_model=AdminReportList)
async def list_reports(
    status: str | None = Query(None, description="Filter by status: pending, resolved, dismissed"),
    target_type: str | None = Query(None, description="Filter by target type"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List reports with reporter info."""
    return await service.list_reports(db, status=status, target_type=target_type, limit=limit, offset=offset)


@router.patch("/reports/{report_id}", response_model=AdminReportItem)
async def update_report(
    report_id: uuid.UUID,
    data: ReportUpdate,
    current_user: dict = Depends(admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Resolve or dismiss a report."""
    admin_id = uuid.UUID(current_user["sub"])
    return await service.update_report(db, report_id, admin_id, data.status, data.admin_note)


# ── Activity Management ──

@router.get("/activities", response_model=AdminActivityList)
async def list_activities(
    search: str | None = Query(None, description="Search by title"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List all activities."""
    return await service.list_activities(db, search=search, limit=limit, offset=offset)


@router.delete("/activities/{activity_id}")
async def delete_activity(
    activity_id: uuid.UUID,
    current_user: dict = Depends(admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete an activity."""
    return await service.delete_activity(db, activity_id)


# ── Document Management ──

@router.get("/documents", response_model=AdminDocumentList)
async def list_documents(
    search: str | None = Query(None, description="Search by title"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List all documents."""
    return await service.list_documents(db, search=search, limit=limit, offset=offset)


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: uuid.UUID,
    current_user: dict = Depends(admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a document."""
    return await service.delete_document(db, document_id)
