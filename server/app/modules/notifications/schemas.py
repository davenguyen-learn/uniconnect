import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


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
    type: str
    target_type: str
    target_id: uuid.UUID
    message: str
    is_read: bool
    created_at: datetime
    
    actor: ActorInfo | None = None

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    unread_count: int
    limit: int
    offset: int
    has_more: bool
