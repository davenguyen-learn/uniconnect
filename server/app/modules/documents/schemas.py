"""Pydantic schemas for documents."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    username: str
    full_name: str | None

    model_config = {"from_attributes": True}


class GroupInfo(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    id: uuid.UUID
    author_id: uuid.UUID
    group_id: uuid.UUID | None
    title: str
    description: str | None
    file_name: str
    file_size: int
    file_type: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    author: UserInfo | None = None
    group: GroupInfo | None = None

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class DocumentUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None)
