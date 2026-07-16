import uuid
from typing import Sequence

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.reports import repository
from app.modules.reports.models import Report
from app.modules.reports.schemas import ReportCreate, ReportResponse

from app.modules.activities import repository as activities_repo
from app.modules.documents import repository as documents_repo
from app.modules.users import repository as users_repo


async def create_report(
    db: AsyncSession, 
    reporter_id: uuid.UUID, 
    data: ReportCreate
) -> ReportResponse:
    # Validate target exists
    if data.target_type == "activity":
        target = await activities_repo.get_activity_by_id(db, data.target_id)
    elif data.target_type == "document":
        target = await documents_repo.get_document(db, data.target_id)
    elif data.target_type == "user":
        target = await users_repo.get_user_by_id(db, data.target_id)
    else:
        raise HTTPException(status_code=400, detail="Invalid target_type")
        
    if not target:
        raise HTTPException(status_code=404, detail=f"{data.target_type.capitalize()} not found")

    report = Report(
        reporter_id=reporter_id,
        target_type=data.target_type,
        target_id=data.target_id,
        reason=data.reason,
        description=data.description
    )
    
    report = await repository.create_report(db, report)
    return ReportResponse.model_validate(report)


async def list_reports(
    db: AsyncSession,
    status: str | None = None,
    target_type: str | None = None,
    limit: int = 50,
    offset: int = 0
) -> list[ReportResponse]:
    reports = await repository.list_reports(db, status, target_type, limit, offset)
    return [ReportResponse.model_validate(r) for r in reports]
