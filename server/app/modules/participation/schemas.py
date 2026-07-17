"""Participation schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    username: str
    full_name: str | None

    model_config = {"from_attributes": True}


class JoinRequestCreate(BaseModel):
    message: str | None = Field(default=None, max_length=500)
    form_responses: dict | None = None


class JoinRequestResponse(BaseModel):
    id: uuid.UUID
    activity_id: uuid.UUID
    user_id: uuid.UUID
    status: str
    message: str | None
    form_responses: dict | None = None
    attendance_confirmed: bool = False
    responded_at: datetime | None
    created_at: datetime
    user: UserInfo | None = None

    model_config = {"from_attributes": True}
