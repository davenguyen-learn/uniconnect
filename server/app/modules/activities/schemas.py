"""Activity schemas for request validation and response serialization."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator
from app.modules.forms.schemas import CustomFormCreate, CustomFormResponse
from app.modules.trophies.schemas import TrophyResponse


class HostInfo(BaseModel):
    username: str
    full_name: str | None

    model_config = {"from_attributes": True}


class GroupInfo(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class ActivityCreate(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default=None, max_length=50)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    location_name: str | None = Field(default=None, max_length=200)
    start_time: datetime
    end_time: datetime
    max_participants: int = Field(gt=0, le=1000)
    privacy: str = "public"
    require_approval: bool = True
    group_id: uuid.UUID | None = None
    trophy_id: uuid.UUID | None = None
    custom_form_id: uuid.UUID | None = None
    custom_form: "CustomFormCreate | None" = None

    @model_validator(mode="after")
    def validate_times(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class ActivityUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default=None, max_length=50)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    location_name: str | None = Field(default=None, max_length=200)
    start_time: datetime | None = None
    end_time: datetime | None = None
    max_participants: int | None = Field(default=None, gt=0, le=1000)
    privacy: str | None = None
    require_approval: bool | None = None
    group_id: uuid.UUID | None = None


class ActivityResponse(BaseModel):
    id: uuid.UUID
    host_id: uuid.UUID
    group_id: uuid.UUID | None
    title: str
    description: str | None
    category: str | None
    latitude: float
    longitude: float
    location_name: str | None
    start_time: datetime
    end_time: datetime
    max_participants: int
    current_participants: int
    privacy: str
    require_approval: bool
    created_at: datetime
    host: HostInfo | None = None
    group: GroupInfo | None = None
    distance_meters: float | None = None
    custom_form: "CustomFormResponse | None" = None
    trophy: TrophyResponse | None = None

    model_config = {"from_attributes": True}


class NearbyQuery(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    radius: int = Field(default=5000, ge=100, le=50000)
    category: str | None = None
    search: str | None = None
    free_to_join: bool | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class ActivityListResponse(BaseModel):
    items: list[ActivityResponse]
    total: int
    limit: int
    offset: int
    has_more: bool
