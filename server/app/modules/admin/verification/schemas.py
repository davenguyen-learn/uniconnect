"""Schemas for Organization Verification requests & reviews."""

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class VerificationRequestCreate(BaseModel):
    organization_name: str = Field(..., min_length=2, max_length=150)
    faculty: str | None = Field(None, max_length=150)
    document_url: str | None = Field(None, max_length=500)
    description: str | None = None


class VerificationReviewAction(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    admin_note: str | None = None


class VerificationItem(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    organization_name: str
    faculty: str | None
    document_url: str | None
    description: str | None
    status: str
    admin_note: str | None
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    created_at: datetime | None = None
    applicant_name: str | None = None
    applicant_email: str | None = None

    model_config = ConfigDict(from_attributes=True)


class VerificationList(BaseModel):
    items: list[VerificationItem]
    total: int
    limit: int
    offset: int
    has_more: bool

    model_config = ConfigDict(from_attributes=True)
