"""Activity schemas for request validation and response serialization."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator
from app.modules.forms.schemas import CustomFormCreate, CustomFormResponse
from app.modules.trophies.schemas import TrophyResponse
from app.modules.calendar.schemas import ConflictInfo


class HostInfo(BaseModel):
    username: str
    full_name: str | None
    avatar_url: str | None = None

    model_config = {"from_attributes": True}


class GroupInfo(BaseModel):
    id: uuid.UUID
    name: str
    avatar_url: str | None = None

    model_config = {"from_attributes": True}


class ActivityCreate(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    private_description: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default=None, max_length=50)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    meeting_location: str | None = Field(default=None, max_length=200)
    location_name: str | None = Field(default=None, max_length=200)  # Backward-compatible alias
    start_time: datetime
    end_time: datetime
    max_participants: int = Field(gt=0, le=1000)
    privacy: str = "public"
    require_approval: bool = False
    social_work_days: float | None = Field(default=None, ge=0)
    group_id: uuid.UUID | None = None
    trophy_id: uuid.UUID | None = None
    attendance_mode: str = "manual"
    check_in_radius: int = Field(default=300, ge=50, le=5000)
    custom_form_id: uuid.UUID | None = None
    custom_form: "CustomFormCreate | None" = None

    @model_validator(mode="before")
    @classmethod
    def extract_lat_lng_and_aliases(cls, data):
        if isinstance(data, dict):
            if "latitude" not in data or "longitude" not in data:
                marker = data.get("marker_location")
                if isinstance(marker, dict):
                    coords = marker.get("coordinates")
                    if isinstance(coords, (list, tuple)) and len(coords) >= 2:
                        data.setdefault("longitude", coords[0])
                        data.setdefault("latitude", coords[1])
            if "requires_approval" in data and "require_approval" not in data:
                data["require_approval"] = data["requires_approval"]
        return data

    @model_validator(mode="after")
    def validate_times(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        if not self.meeting_location and self.location_name:
            self.meeting_location = self.location_name
        if not self.meeting_location or not self.meeting_location.strip():
            raise ValueError("meeting_location is required")
        return self


class ActivityUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    private_description: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default=None, max_length=50)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    meeting_location: str | None = Field(default=None, max_length=200)
    location_name: str | None = Field(default=None, max_length=200)  # Backward-compatible alias
    start_time: datetime | None = None
    end_time: datetime | None = None
    max_participants: int | None = Field(default=None, gt=0, le=1000)
    privacy: str | None = None
    require_approval: bool | None = None
    social_work_days: float | None = Field(default=None, ge=0)
    group_id: uuid.UUID | None = None
    trophy_id: uuid.UUID | None = None
    attendance_mode: str | None = None
    check_in_radius: int | None = Field(default=None, ge=50, le=5000)
    custom_form: "CustomFormCreate | None" = None

    @model_validator(mode="before")
    @classmethod
    def extract_lat_lng_and_aliases(cls, data):
        if isinstance(data, dict):
            if "latitude" not in data or "longitude" not in data:
                marker = data.get("marker_location")
                if isinstance(marker, dict):
                    coords = marker.get("coordinates")
                    if isinstance(coords, (list, tuple)) and len(coords) >= 2:
                        data.setdefault("longitude", coords[0])
                        data.setdefault("latitude", coords[1])
            if "requires_approval" in data and "require_approval" not in data:
                data["require_approval"] = data["requires_approval"]
        return data


class ActivityResponse(BaseModel):
    id: uuid.UUID
    host_id: uuid.UUID
    group_id: uuid.UUID | None = None
    title: str
    description: str | None = None
    private_description: str | None = None
    category: str | None = None
    latitude: float = 0.0
    longitude: float = 0.0
    meeting_location: str | None = None
    location_name: str | None = None  # Backward-compatible alias
    start_time: datetime
    end_time: datetime
    max_participants: int = 1
    current_participants: int = 1
    privacy: str = "public"
    require_approval: bool = False
    attendance_mode: str = "manual"
    check_in_radius: int = 300
    social_work_days: float | None = None
    created_at: datetime | None = None
    host: HostInfo | None = None
    group: GroupInfo | None = None
    co_hosts: list[GroupInfo] = []
    distance_meters: float | None = None
    custom_form: "CustomFormResponse | None" = None
    trophy: TrophyResponse | None = None
    conflict_info: ConflictInfo | None = None
    attendance_confirmed: bool | None = None
    joined_at: datetime | None = None
    registration_status: str | None = None
    is_deleted: bool = False

    model_config = {"from_attributes": True}


class NearbyQuery(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    radius: int = Field(default=5000, ge=100, le=50000)
    category: str | None = None
    search: str | None = None
    free_to_join: bool | None = None
    days_ahead: int | None = Field(default=None, ge=1, le=365)
    is_ctxh: bool | None = None
    has_trophy: bool | None = None
    sort_by: str = Field(default="distance")
    exclude_my_activities: bool = Field(default=True)
    exclude_joined: bool = Field(default=False)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class ActivityListResponse(BaseModel):
    items: list[ActivityResponse]
    total: int
    limit: int
    offset: int
    has_more: bool
