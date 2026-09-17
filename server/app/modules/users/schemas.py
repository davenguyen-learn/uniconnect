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
    interests: list[str] | None = None
    role: str
    is_verified: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=100)
    bio: str | None = Field(default=None, max_length=1000)
    university: str | None = Field(default=None, max_length=150)
    interests: list[str] | None = None


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


class MyUserStatsResponse(BaseModel):
    user_id: str
    total_ctxh_days: float
    target_ctxh_days: float
    ctxh_completion_percent: float
    remaining_ctxh_days: float
    is_target_reached: bool
    total_attended_activities: int
    total_trophies_count: int
    total_trophy_points: int
    rank_title: str


class PublicUserStatsResponse(BaseModel):
    user_id: str
    total_ctxh_days: float
    total_attended_activities: int
    total_trophies_count: int
    total_trophy_points: int
    rank_title: str

