"""Schemas for chat module."""

from pydantic import BaseModel
from app.modules.activities.schemas import ActivityResponse

class ChatMessage(BaseModel):
    role: str  # 'user' or 'model'
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    user_lat: float | None = None
    user_lng: float | None = None

class ChatResponse(BaseModel):
    reply: str
    recommended_activities: list[ActivityResponse] | None = None
