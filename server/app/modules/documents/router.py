"""Document API endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.documents import service as document_service
from app.modules.documents.schemas import DocumentListResponse, DocumentResponse, DocumentUpdate

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    title: Annotated[str, Form()],
    description: Annotated[str | None, Form()] = None,
    group_id: Annotated[uuid.UUID | None, Form()] = None,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a new document."""
    return await document_service.upload_document(
        db, uuid.UUID(current_user["sub"]), title, description, group_id, file
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    group_id: uuid.UUID | None = Query(default=None),
    search: str | None = Query(default=None, description="Search term for title or description"),
    sort_by: str = Query(default="newest", pattern="^(newest|oldest|most_interactions)$"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List documents."""
    return await document_service.list_documents(
        db, uuid.UUID(current_user["sub"]), group_id, search, sort_by, limit, offset
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get document details."""
    return await document_service.get_document(db, document_id, uuid.UUID(current_user["sub"]))


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: uuid.UUID,
    data: DocumentUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update document metadata (author only)."""
    return await document_service.update_document(
        db, document_id, uuid.UUID(current_user["sub"]), data
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document (author only)."""
    await document_service.delete_document(db, document_id, uuid.UUID(current_user["sub"]))


@router.get("/{document_id}/download")
async def get_download_url(
    document_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a download URL (presigned if private)."""
    return await document_service.get_download_url(db, document_id, uuid.UUID(current_user["sub"]))
