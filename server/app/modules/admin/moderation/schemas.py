"""Schemas for Moderation Reports & Actions."""

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ReportReviewAction(BaseModel):
    action: str = Field(..., pattern="^(resolve|dismiss)$")
    admin_note: str | None = None
    hide_activity: bool = False
    deactivate_user: bool = False


class AdminReportItem(BaseModel):
    id: uuid.UUID
    reporter_id: uuid.UUID
    target_type: str
    target_id: uuid.UUID
    reason: str
    description: str | None
    status: str
    admin_note: str | None
    resolved_by: uuid.UUID | None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    reporter_name: str | None = None
    target_title_or_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AdminReportList(BaseModel):
    items: list[AdminReportItem]
    total: int
    limit: int
    offset: int
    has_more: bool

    model_config = ConfigDict(from_attributes=True)
