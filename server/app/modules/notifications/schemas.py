import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator


class ActorInfo(BaseModel):
    id: uuid.UUID
    username: str
    full_name: str | None = None
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    actor_id: uuid.UUID | None
    activity_id: uuid.UUID | None = None
    type: str
    target_type: str = "activity"
    target_id: uuid.UUID | None = None
    action_url: str | None = None
    message: str
    is_read: bool
    created_at: datetime
    
    actor: ActorInfo | None = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def populate_target(self) -> "NotificationResponse":
        if self.target_id is None and self.activity_id is not None:
            self.target_id = self.activity_id
        return self


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    unread_count: int
    limit: int
    offset: int
    has_more: bool
