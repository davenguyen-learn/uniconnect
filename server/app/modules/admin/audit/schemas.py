"""Schemas for Admin Audit Trail."""

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AdminAuditLogItem(BaseModel):
    id: uuid.UUID
    actor_id: uuid.UUID | None
    action: str
    target_type: str
    target_id: uuid.UUID
    metadata_json: dict | None
    created_at: datetime
    actor_username: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AdminAuditLogList(BaseModel):
    items: list[AdminAuditLogItem]
    total: int
    limit: int
    offset: int
    has_more: bool

    model_config = ConfigDict(from_attributes=True)
