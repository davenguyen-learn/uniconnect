import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.reports.models import Report


async def create_report(db: AsyncSession, report: Report) -> Report:
    db.add(report)
    await db.flush()
    return report


async def get_report_by_id(db: AsyncSession, report_id: uuid.UUID) -> Report | None:
    result = await db.execute(select(Report).where(Report.id == report_id))
    return result.scalar_one_or_none()


async def list_reports(
    db: AsyncSession,
    status: str | None = None,
    target_type: str | None = None,
    limit: int = 50,
    offset: int = 0
) -> Sequence[Report]:
    stmt = select(Report).order_by(Report.created_at.desc())
    
    if status:
        stmt = stmt.where(Report.status == status)
    if target_type:
        stmt = stmt.where(Report.target_type == target_type)
        
    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    return result.scalars().all()
