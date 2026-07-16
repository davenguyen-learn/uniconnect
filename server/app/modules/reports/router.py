import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.service import get_current_user
from app.modules.reports import service as reports_service
from app.modules.reports.schemas import ReportCreate, ReportResponse

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("", response_model=ReportResponse, status_code=201)
async def create_report(
    data: ReportCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a report for an activity, document, or user.
    """
    user_id = uuid.UUID(current_user["sub"])
    return await reports_service.create_report(db, user_id, data)


@router.get("", response_model=list[ReportResponse])
async def list_reports(
    status: str | None = Query(None, description="Filter by status"),
    target_type: str | None = Query(None, description="Filter by target_type"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List reports (Admin only).
    """
    # Assuming role is encoded in JWT
    if current_user.get("role") != "admin":
        # Let it be public for now if admin role isn't strictly enforced yet, 
        # but realistically we should protect it. We will just check it.
        # Currently the system doesn't have an admin role set up properly, 
        # but we'll prepare for it.
        raise HTTPException(status_code=403, detail="Admin access required")
        
    return await reports_service.list_reports(
        db, status=status, target_type=target_type, limit=limit, offset=offset
    )
