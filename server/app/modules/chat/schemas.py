"""Schemas for chat module and structured tool execution."""

import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from app.modules.activities.schemas import ActivityResponse


# ── Structured Tool Result Schemas (LOCK 2) ──

class ActivitySearchToolItem(BaseModel):
    activity_id: str
    title: str
    start_time: str
    end_time: str
    meeting_location: str = "Khuôn viên trường"
    location_name: str = "Khuôn viên trường"
    social_work_days: float | None = None
    distance_meters: float | None = None
    distance_status: str = "unknown"  # "nearby", "moderate", "far", "unknown"
    conflict_status: str = "none"     # "none", "soft_conflict", "hard_conflict"
    registration_status: str = "available"  # "available", "registered", "capacity_full", "deadline_passed"
    eligibility_status: str = "eligible"    # "eligible", "not_eligible"


class ActivitySearchToolResult(BaseModel):
    items: list[ActivitySearchToolItem]
    total: int


class BusySlotItem(BaseModel):
    start_time: str
    end_time: str
    reason_code: str = "personal_busy"  # "personal_busy", "university_activity"


class UserScheduleToolResult(BaseModel):
    busy_slots: list[BusySlotItem]
    total_busy_slots: int


class GroupSearchToolItem(BaseModel):
    group_id: str
    name: str
    description: str | None = None
    privacy: str = "public"
    member_count: int = 0


class GroupSearchToolResult(BaseModel):
    items: list[GroupSearchToolItem]
    total: int


# ── Chat Request & Response Schemas ──

class ChatEventCardItem(BaseModel):
    activity_id: str
    title: str
    start_time: str
    end_time: str
    meeting_location: str = "Khuôn viên trường"
    location_name: str = "Khuôn viên trường"
    social_work_days: float | None = None
    distance_meters: float | None = None
    distance_status: str = "unknown"
    conflict_status: str = "none"
    registration_status: str = "available"
    eligibility_status: str = "eligible"


class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str  # 'user', 'assistant', 'model'
    content: str
    cards: list[ChatEventCardItem] | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str | None = None
    messages: list[ChatMessage] | None = None
    user_lat: float | None = None
    user_lng: float | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    message: ChatMessage
    reply: str  # Backward-compatible convenience field pointing to message.content
    recommended_activities: list[ActivityResponse] | None = None  # Backward-compatible
    suggestions: list[str] = Field(default_factory=list)
