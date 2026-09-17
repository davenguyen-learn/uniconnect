"""Schemas for Master Student Audit."""

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class StudentAuditItem(BaseModel):
    id: uuid.UUID
    username: str
    full_name: str | None
    email: str
    university: str | None
    is_active: bool
    is_verified: bool
    role: str
    confirmed_ctxh_days: float
    attendance_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentAuditList(BaseModel):
    items: list[StudentAuditItem]
    total: int
    limit: int
    offset: int
    has_more: bool

    model_config = ConfigDict(from_attributes=True)
