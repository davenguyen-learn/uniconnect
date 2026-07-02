from datetime import datetime
import uuid
from pydantic import BaseModel, Field

from app.modules.groups.models import GroupRole


class GroupMemberResponse(BaseModel):
    user_id: uuid.UUID
    role: GroupRole
    joined_at: datetime
    
    # We can include basic user info
    username: str | None = None
    full_name: str | None = None

    class Config:
        from_attributes = True


class GroupBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: str | None = None
    allow_member_activities: bool = True
    allow_member_documents: bool = True


class GroupCreate(GroupBase):
    pass


class GroupUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    description: str | None = None
    allow_member_activities: bool | None = None
    allow_member_documents: bool | None = None


class GroupResponse(GroupBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    member_count: int | None = None

    class Config:
        from_attributes = True


class GroupDetailResponse(GroupResponse):
    members: list[GroupMemberResponse] = []
