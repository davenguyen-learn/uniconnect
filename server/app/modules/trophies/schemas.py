import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class ActivitySimple(BaseModel):
    id: uuid.UUID
    title: str

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
