"""User profile schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    full_name: str | None
    bio: str | None
    university: str | None
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=100)
    bio: str | None = Field(default=None, max_length=1000)
    university: str | None = Field(default=None, max_length=150)


class UserFollowResponse(BaseModel):
    items: list[UserProfile]
    total: int
    limit: int
    offset: int
    has_more: bool


class FollowStatusResponse(BaseModel):
    is_following: bool
    followers_count: int
    following_count: int
