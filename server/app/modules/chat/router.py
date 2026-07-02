"""Chat API endpoints."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.chat import service
from app.modules.chat.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat_with_bot(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message to the AI activity assistant."""
    return await service.handle_chat(
        db=db,
        user_id=uuid.UUID(current_user["sub"]),
        messages=request.messages,
        user_lat=request.user_lat,
        user_lng=request.user_lng,
    )
