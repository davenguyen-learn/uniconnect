from datetime import datetime
import uuid
from pydantic import BaseModel, Field

from app.modules.groups.models import GroupRole, GroupPrivacy
from app.modules.forms.schemas import CustomFormCreate, CustomFormResponse


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
    public_description: str | None = None
    private_description: str | None = None
    allow_member_activities: bool = True
    require_approval: bool = True
    privacy: str = "public"


class GroupCreate(GroupBase):
    custom_form: CustomFormCreate | None = None


class GroupUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    description: str | None = None
    public_description: str | None = None
    private_description: str | None = None
    allow_member_activities: bool | None = None
    require_approval: bool | None = None
    privacy: str | None = None


class GroupResponse(GroupBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    member_count: int | None = None

    class Config:
        from_attributes = True


class GroupDetailResponse(GroupResponse):
    members: list[GroupMemberResponse] = []
    custom_form: CustomFormResponse | None = None


class GroupStatsResponse(BaseModel):
    group_id: uuid.UUID
    member_count: int
    total_activities_count: int
    total_ctxh_contributed: float


class GroupJoinRequestResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    user_id: uuid.UUID
    status: str
    created_at: datetime
    username: str | None = None
    full_name: str | None = None
    form_responses: dict | None = None

    model_config = {"from_attributes": True}


class JoinRequestActionRequest(BaseModel):
    action: str = Field(..., description="'approved' or 'rejected'")


class CoHostInvitationCreate(BaseModel):
    invited_group_id: uuid.UUID
    message: str | None = None


class CoHostInvitationResponse(BaseModel):
    id: uuid.UUID
    activity_id: uuid.UUID
    activity_title: str | None = None
    host_group_id: uuid.UUID
    host_group_name: str | None = None
    invited_group_id: uuid.UUID
    invited_group_name: str | None = None
    status: str
    message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CoHostActionRequest(BaseModel):
    action: str = Field(..., description="'accepted' or 'declined'")


class CoHostGroupInfo(BaseModel):
    group_id: uuid.UUID
    name: str

