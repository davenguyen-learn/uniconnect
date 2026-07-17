import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class TrophyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    points: int = Field(default=0, ge=0)
    icon_url: str | None = None

class TrophyResponse(BaseModel):
    id: uuid.UUID
    name: str
    points: int
    icon_url: str | None
    creator_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}

class UserTrophyResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    trophy: TrophyResponse
    activity_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}
