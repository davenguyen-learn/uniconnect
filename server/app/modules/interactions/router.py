"""Interaction API endpoints — comments and likes (polymorphic)."""

import uuid
from enum import Enum

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.interactions import service
from app.modules.interactions.schemas import (
    CommentCreate,
    CommentListResponse,
    CommentResponse,
    CommentUpdate,
    ContentStatsResponse,
    LikeResponse,
)


class TargetType(str, Enum):
    """Allowed target types for interactions."""
    activities = "activities"
    documents = "documents"


def _map_target_type(target_type: TargetType) -> str:
    """Map URL path param to internal target_type string."""
    return {
        TargetType.activities: "activity",
        TargetType.documents: "document",
    }[target_type]


router = APIRouter(tags=["interactions"])


# ── Comments ──


@router.post(
    "/{target_type}/{target_id}/comments",
    response_model=CommentResponse,
    status_code=201,
)
async def create_comment(
    target_type: TargetType = Path(),
    target_id: uuid.UUID = Path(),
    data: CommentCreate = ...,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Post a comment on a target (activity or document)."""
    return await service.create_comment(
        db, _map_target_type(target_type), target_id, current_user["sub"], data
    )


@router.get(
    "/{target_type}/{target_id}/comments",
    response_model=CommentListResponse,
)
async def list_comments(
    target_type: TargetType = Path(),
    target_id: uuid.UUID = Path(),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List top-level comments with replies for a target."""
    return await service.list_comments(
        db, _map_target_type(target_type), target_id, limit, offset
    )


@router.patch(
    "/comments/{comment_id}",
    response_model=CommentResponse,
)
async def update_comment(
    comment_id: uuid.UUID,
    data: CommentUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Edit a comment (author only)."""
    return await service.update_comment(db, comment_id, current_user["sub"], data)


@router.delete(
    "/comments/{comment_id}",
    status_code=204,
)
async def delete_comment(
    comment_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a comment (author only)."""
    await service.delete_comment(db, comment_id, current_user["sub"])


# ── Likes ──


@router.post(
    "/{target_type}/{target_id}/like",
    response_model=LikeResponse,
)
async def toggle_like(
    target_type: TargetType = Path(),
    target_id: uuid.UUID = Path(),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle like on a target (like if not liked, unlike if already liked)."""
    return await service.toggle_like(
        db, _map_target_type(target_type), target_id, current_user["sub"]
    )


@router.get(
    "/{target_type}/{target_id}/like",
    response_model=LikeResponse,
)
async def get_like_status(
    target_type: TargetType = Path(),
    target_id: uuid.UUID = Path(),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check if current user has liked a target and get total likes."""
    return await service.get_like_status(
        db, _map_target_type(target_type), target_id, current_user["sub"]
    )


# ── Stats ──


@router.get(
    "/{target_type}/{target_id}/stats",
    response_model=ContentStatsResponse,
)
async def get_content_stats(
    target_type: TargetType = Path(),
    target_id: uuid.UUID = Path(),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get combined stats: like count, comment count, and user like status."""
    return await service.get_content_stats(
        db, _map_target_type(target_type), target_id, current_user["sub"]
    )
