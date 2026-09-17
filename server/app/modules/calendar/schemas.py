import uuid
from datetime import date, datetime, time
from typing import Any
from pydantic import BaseModel, Field, model_validator


class BusySlotCreate(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    recurrence: str = Field(default="none", description="'none' or 'weekly'")
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    day_of_week: int | None = Field(default=None, ge=0, le=6)
    start_time_of_day: time | None = None
    end_time_of_day: time | None = None
    valid_from: date | None = None
    valid_until: date | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.recurrence == "weekly":
            if self.day_of_week is None:
                raise ValueError("day_of_week is required for weekly recurrence.")
            if self.start_time_of_day is None or self.end_time_of_day is None:
                raise ValueError("start_time_of_day and end_time_of_day are required for weekly recurrence.")
            if self.start_time_of_day >= self.end_time_of_day:
                raise ValueError("end_time_of_day must be after start_time_of_day.")
        else:
            if not self.start_datetime or not self.end_datetime:
                raise ValueError("start_datetime and end_datetime are required for one-off busy slots.")
            if self.start_datetime >= self.end_datetime:
                raise ValueError("end_datetime must be after start_datetime.")
        return self


class BusySlotUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=150)
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    day_of_week: int | None = Field(default=None, ge=0, le=6)
    start_time_of_day: time | None = None
    end_time_of_day: time | None = None
    valid_from: date | None = None
    valid_until: date | None = None


class BusySlotResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    recurrence: str
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    day_of_week: int | None = None
    start_time_of_day: time | None = None
    end_time_of_day: time | None = None
    valid_from: date | None = None
    valid_until: date | None = None
    exception_dates: list[date] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class CalendarEventItem(BaseModel):
    id: str
    title: str
    start_time: datetime
    end_time: datetime
    event_type: str  # 'busy_slot' | 'activity_joined' | 'activity_hosted'
    activity_id: uuid.UUID | None = None
    category: str | None = None
    location_name: str | None = None
    is_recurring: bool = False
    color_tag: str = "busy"  # 'busy' (orange/gray), 'joined' (blue), 'hosted' (purple)


class ConflictDetail(BaseModel):
    type: str  # 'busy_slot' | 'approved_activity' | 'hosted_activity' | 'pending_request'
    title: str
    time_range: str
    target_id: str | None = None


class ConflictInfo(BaseModel):
    has_conflict: bool = False
    level: str = "none"  # 'none' | 'soft_conflict' | 'hard_conflict'
    can_join: bool = True
    warning_message: str | None = None
    conflicting_with: ConflictDetail | None = None
    swap_candidate: dict[str, Any] | None = None


class ConflictCheckRequest(BaseModel):
    start_time: datetime
    end_time: datetime
    exclude_activity_id: uuid.UUID | None = None


class ReschedulePreviewRequest(BaseModel):
    new_start_time: datetime
    new_end_time: datetime


class ConflictedMemberInfo(BaseModel):
    user_id: str
    full_name: str
    reason_code: str = "personal_busy"  # 'personal_busy' | 'university_activity' | 'recurring_schedule'
    reason_label: str = "Trùng lịch bận cá nhân"
    conflict_type: str = "busy_slot"  # 'busy_slot' | 'other_activity' (legacy compatibility)
    reason: str = "Trùng lịch bận cá nhân"  # legacy compatibility


class ReschedulePreviewResponse(BaseModel):
    total_participants: int
    conflicted_count: int
    safe_to_reschedule: bool
    free_percentage: int
    conflicted_members: list[ConflictedMemberInfo]
