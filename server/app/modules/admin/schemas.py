"""Admin module Pydantic schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ── Stats ──

class AdminStats(BaseModel):
    total_users: int
    total_activities: int
    total_documents: int
    total_reports: int
    pending_reports: int
    new_users_this_week: int


# ── User management ──

class AdminUserItem(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    full_name: str | None
    university: str | None
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminUserList(BaseModel):
    items: list[AdminUserItem]
    total: int
    limit: int
    offset: int
    has_more: bool


class RoleUpdate(BaseModel):
    role: str = Field(..., pattern="^(student|moderator|admin)$")


class StatusUpdate(BaseModel):
    is_active: bool


# ── Report management ──

class ReportReporterInfo(BaseModel):
    id: uuid.UUID
    username: str
    full_name: str | None
    email: str

    model_config = ConfigDict(from_attributes=True)


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
    created_at: datetime
    updated_at: datetime
    reporter: ReportReporterInfo | None = None

    model_config = ConfigDict(from_attributes=True)


class AdminReportList(BaseModel):
    items: list[AdminReportItem]
    total: int
    limit: int
    offset: int
    has_more: bool


class ReportUpdate(BaseModel):
    status: str = Field(..., pattern="^(resolved|dismissed)$")
    admin_note: str | None = None


# ── Activity management ──

class AdminActivityItem(BaseModel):
    id: uuid.UUID
    host_id: uuid.UUID
    title: str
    description: str | None
    category: str | None
    location_name: str | None
    start_time: datetime
    end_time: datetime
    max_participants: int
    current_participants: int
    privacy: str
    created_at: datetime
    host_username: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AdminActivityList(BaseModel):
    items: list[AdminActivityItem]
    total: int
    limit: int
    offset: int
    has_more: bool


# ── Document management ──

class AdminDocumentItem(BaseModel):
    id: uuid.UUID
    author_id: uuid.UUID
    title: str
    description: str | None
    file_name: str
    file_size: int
    file_type: str
    is_deleted: bool
    created_at: datetime
    author_username: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AdminDocumentList(BaseModel):
    items: list[AdminDocumentItem]
    total: int
    limit: int
    offset: int
    has_more: bool
