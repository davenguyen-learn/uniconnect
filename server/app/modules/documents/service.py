"""Business logic for documents."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.core.storage import storage_service
from app.modules.documents import repository
from app.modules.documents.models import Document
from app.modules.documents.schemas import DocumentListResponse, DocumentResponse, DocumentUpdate
from app.modules.groups.repository import is_member


async def upload_document(
    db: AsyncSession,
    author_id: uuid.UUID,
    title: str,
    description: str | None,
    group_id: uuid.UUID | None,
    file: UploadFile,
) -> DocumentResponse:
    """Upload a file to R2 and create a Document record."""
    if group_id:
        from app.modules.groups.repository import get_group_by_id
        # Check membership
        if not await is_member(db, group_id, author_id):
            raise ForbiddenError("You must be a member of this group to upload documents.")
            
        group = await get_group_by_id(db, group_id)
        if group and group.owner_id != author_id and not group.allow_member_documents:
            raise ForbiddenError("Group members are not allowed to post documents.")

    # Validate file type
    if file.content_type not in settings.ALLOWED_FILE_TYPES:
        raise ValidationError(f"File type not allowed: {file.content_type}")

    # Validate file size (FastAPI doesn't have a direct way before reading, so we read it)
    file_bytes = await file.read()
    file_size = len(file_bytes)
    if file_size > settings.MAX_FILE_SIZE:
        raise ValidationError(f"File too large. Maximum size is {settings.MAX_FILE_SIZE / 1024 / 1024}MB")
    
    # Reset file cursor for upload
    await file.seek(0)

    # Upload to R2
    try:
        object_key = await storage_service.upload_file(
            file.file, 
            filename=file.filename,
            content_type=file.content_type,
            folder="documents"
        )
    except Exception as e:
        raise ValidationError(f"File upload failed: {str(e)}")

    # Create record
    document = Document(
        author_id=author_id,
        group_id=group_id,
        title=title,
        description=description,
        file_url=object_key,
        file_name=file.filename,
        file_size=file_size,
        file_type=file.content_type
    )

    created_doc = await repository.create_document(db, document)
    return DocumentResponse.model_validate(created_doc)


async def list_documents(
    db: AsyncSession,
    user_id: uuid.UUID,
    group_id: uuid.UUID | None = None,
    search: str | None = None,
    sort_by: str = "newest",
    limit: int = 20,
    offset: int = 0,
) -> DocumentListResponse:
    """List documents accessible to the user."""
    documents, total = await repository.list_documents(db, user_id, group_id, search, sort_by, limit, offset)
    return DocumentListResponse(
        items=[DocumentResponse.model_validate(d) for d in documents],
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )


async def get_document(
    db: AsyncSession,
    document_id: uuid.UUID,
    user_id: uuid.UUID,
) -> DocumentResponse:
    """Get a document by ID."""
    doc = await repository.get_by_id(db, document_id)
    if not doc:
        raise NotFoundError("Document not found.")

    # Access control
    if doc.group_id:
        if not await is_member(db, doc.group_id, user_id):
            raise ForbiddenError("You must be a member of this group to view this document.")

    return DocumentResponse.model_validate(doc)


async def update_document(
    db: AsyncSession,
    document_id: uuid.UUID,
    user_id: uuid.UUID,
    data: DocumentUpdate,
) -> DocumentResponse:
    """Update document metadata."""
    doc = await repository.get_by_id(db, document_id)
    if not doc:
        raise NotFoundError("Document not found.")
    
    if doc.author_id != user_id:
        raise ForbiddenError("Only the author can update this document.")

    update_data = data.model_dump(exclude_unset=True)
    if update_data:
        doc = await repository.update_document(db, doc, update_data)
        
    return DocumentResponse.model_validate(doc)


async def delete_document(
    db: AsyncSession,
    document_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """Soft delete a document and remove file from R2."""
    doc = await repository.get_by_id(db, document_id)
    if not doc:
        raise NotFoundError("Document not found.")
    
    if doc.author_id != user_id:
        raise ForbiddenError("Only the author can delete this document.")

    # Remove from storage
    await storage_service.delete_file(doc.file_url)
    
    # Soft delete in DB
    await repository.soft_delete_document(db, doc)


async def get_download_url(
    db: AsyncSession,
    document_id: uuid.UUID,
    user_id: uuid.UUID,
) -> dict:
    """Get a presigned URL to download the document."""
    doc = await repository.get_by_id(db, document_id)
    if not doc:
        raise NotFoundError("Document not found.")

    # Access control
    if doc.group_id:
        if not await is_member(db, doc.group_id, user_id):
            raise ForbiddenError("You must be a member of this group to download this document.")

    # If the file_url is already an absolute URL (e.g., from seed data), return it directly
    if doc.file_url.startswith("http://") or doc.file_url.startswith("https://"):
        return {"url": doc.file_url}

    # If public and we have a public URL configured, return it directly
    if not doc.group_id and storage_service.public_url:
        return {"url": storage_service.get_public_url(doc.file_url)}
        
    # Otherwise generate a presigned URL (valid for 1 hour)
    url = await storage_service.get_presigned_url(doc.file_url)
    return {"url": url}
