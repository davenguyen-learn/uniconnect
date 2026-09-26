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


class CheckInRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=20)
    latitude: float | None = Field(None, ge=-90.0, le=90.0)
    longitude: float | None = Field(None, ge=-180.0, le=180.0)
    accuracy: float | None = Field(None, gt=0.0)


class CheckInResponse(BaseModel):
    message: str
    attendance_confirmed: bool
    trophy_awarded: bool = False
    already_confirmed: bool = False


class CheckInCodeResponse(BaseModel):
    check_in_code: str
    rotating_token: str
    expires_in_seconds: int
    check_in_radius: int


class AttendanceUpdateRequest(BaseModel):
    attended: bool


class CertificateCustomField(BaseModel):
    label: str
    value: str


class CertificateResponse(BaseModel):
    certificate_code: str
    activity_id: uuid.UUID
    user_id: uuid.UUID
    participant_name: str
    participant_username: str
    participant_email: str | None = None
    participant_university: str | None = None
    activity_title: str
    activity_date: str
    meeting_location: str | None = None
    location_name: str | None = None
    host_id: uuid.UUID | None = None
    host_name: str
    host_university: str | None = None
    group_id: uuid.UUID | None = None
    group_name: str | None = None
    group_is_private: bool = False
    social_work_days: float | None = None
    trophy_name: str | None = None
    trophy_icon: str | None = None
    trophy_points: int | None = None
    custom_fields: list[CertificateCustomField] = []
    issued_at: datetime
    verification_url: str
    is_host: bool = False

