"""Pydantic schemas for comments and likes (polymorphic)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator


# ── Shared ──

class UserInfo(BaseModel):
    username: str
    full_name: str | None
    avatar_url: str | None = None

    model_config = {"from_attributes": True}


# ── Comments ──

class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=1000)
    parent_id: uuid.UUID | None = None


class CommentUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=1000)


class CommentResponse(BaseModel):
    id: uuid.UUID
    activity_id: uuid.UUID
    target_type: str = "activity"
    target_id: uuid.UUID | None = None
    user_id: uuid.UUID
    parent_id: uuid.UUID | None
    content: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    user: UserInfo | None = None
    replies: list["CommentResponse"] = []

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def populate_target(self) -> "CommentResponse":
        if self.target_id is None:
            self.target_id = self.activity_id
        return self


class CommentListResponse(BaseModel):
    items: list[CommentResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


# ── Likes ──

class LikeResponse(BaseModel):
    liked: bool
    total_likes: int


class ContentStatsResponse(BaseModel):
    like_count: int
    comment_count: int
    is_liked: bool
