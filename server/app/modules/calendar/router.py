import uuid
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.calendar import repository as cal_repo
from app.modules.calendar import service as cal_service
from app.modules.calendar.schemas import (
    BusySlotCreate,
    BusySlotResponse,
    CalendarEventItem,
    ConflictCheckRequest,
    ConflictInfo,
)

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/events", response_model=list[CalendarEventItem])
async def get_calendar_events(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated calendar events (busy slots + joined activities + hosted activities)."""
    user_id = uuid.UUID(current_user["sub"])
    today = date.today()
    s_date = start_date or (today - timedelta(days=7))
    e_date = end_date or (today + timedelta(days=35))

    return await cal_service.get_user_calendar_events(db, user_id, s_date, e_date)


@router.get("/busy-slots", response_model=list[BusySlotResponse])
async def list_busy_slots(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all custom busy slots for the current user."""
    user_id = uuid.UUID(current_user["sub"])
    slots = await cal_repo.get_user_busy_slots(db, user_id)
    return [
        BusySlotResponse(
            id=s.id,
            user_id=s.user_id,
            title=s.title,
            recurrence=s.recurrence,
            start_datetime=s.start_datetime,
            end_datetime=s.end_datetime,
            day_of_week=s.day_of_week,
            start_time_of_day=s.start_time_of_day,
            end_time_of_day=s.end_time_of_day,
            valid_from=s.valid_from,
            valid_until=s.valid_until,
            exception_dates=[e.skip_date for e in s.exceptions],
        )
        for s in slots
    ]


@router.post("/busy-slots", response_model=BusySlotResponse, status_code=status.HTTP_201_CREATED)
async def create_busy_slot(
    data: BusySlotCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new custom busy slot (one-off or weekly recurring)."""
    user_id = uuid.UUID(current_user["sub"])
    return await cal_service.create_busy_slot(db, user_id, data)


@router.delete("/busy-slots/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_busy_slot(
    slot_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a custom busy slot."""
    user_id = uuid.UUID(current_user["sub"])
    await cal_service.delete_busy_slot(db, user_id, slot_id)


@router.post("/check-conflict", response_model=ConflictInfo)
async def check_schedule_conflict(
    data: ConflictCheckRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pre-check whether a time window conflicts with current user's schedule."""
    user_id = uuid.UUID(current_user["sub"])
    detector = await cal_service.get_detector_for_user(db, user_id)
    return detector.check_conflict(
        data.start_time, data.end_time, exclude_activity_id=data.exclude_activity_id
    )
