import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class ActivitySimple(BaseModel):
    id: uuid.UUID | None = None
    title: str
    privacy: str = "public"
    is_accessible: bool = True

    model_config = {"from_attributes": True}

class TrophyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = None
    activity_id: uuid.UUID | None = None
    points: int = Field(default=0, ge=0)
    icon: str | None = None

class TrophyResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    activity_id: uuid.UUID | None = None
    points: int = 0
    icon: str | None = "🏆"
    creator_id: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

class UserTrophyResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    trophy: TrophyResponse
    activity_id: uuid.UUID | None = None
    activity: ActivitySimple | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

class TrophyGrantRequestResponse(BaseModel):
    id: uuid.UUID
    activity_id: uuid.UUID
    trophy_id: uuid.UUID
    status: str
    min_participants_required: int
    actual_attended_count: int
    admin_notes: str | None = None
    reviewed_by: uuid.UUID | None = None
    reviewed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    activity: ActivitySimple | None = None
    trophy: TrophyResponse | None = None

    model_config = {"from_attributes": True}

class TrophyGrantReviewRequest(BaseModel):
    action: str = Field(description="'approve' or 'reject'")
    admin_notes: str | None = None
