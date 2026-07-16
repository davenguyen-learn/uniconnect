"""Data access layer for documents."""

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.documents.models import Document
from app.modules.groups.models import GroupMember


async def create_document(db: AsyncSession, document: Document) -> Document:
    """Insert a new document."""
    db.add(document)
    await db.flush()
    # Reload with author and group relationships
    result = await db.execute(
        select(Document)
        .options(joinedload(Document.author), joinedload(Document.group))
        .where(Document.id == document.id)
    )
    return result.scalar_one()


async def get_by_id(db: AsyncSession, document_id: uuid.UUID) -> Document | None:
    """Fetch a single document by ID."""
    result = await db.execute(
        select(Document)
        .options(joinedload(Document.author), joinedload(Document.group))
        .where(Document.id == document_id, Document.is_deleted.is_(False))
    )
    return result.scalar_one_or_none()


async def list_documents(
    db: AsyncSession,
    user_id: uuid.UUID,
    group_id: uuid.UUID | None = None,
    search: str | None = None,
    sort_by: str = "newest",
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Document], int]:
    """
    List documents with access control:
    Users can see public documents (group_id is None) and documents in groups they belong to.
    """
    from app.modules.interactions.models import Comment, ContentLike

    base_filter = Document.is_deleted.is_(False)

    if group_id:
        base_filter = (base_filter) & (Document.group_id == group_id)
        
    if search:
        search_filter = or_(
            Document.title.ilike(f"%{search}%"),
            Document.description.ilike(f"%{search}%")
        )
        base_filter = (base_filter) & search_filter

    # Access filter: Public OR (belongs to a group the user is a member of)
    # Using a subquery for group membership
    member_groups = select(GroupMember.group_id).where(GroupMember.user_id == user_id)
    access_filter = or_(
        Document.group_id.is_(None),
        Document.group_id.in_(member_groups)
    )

    # Count total
    count_q = (
        select(func.count())
        .select_from(Document)
        .where(base_filter, access_filter)
    )
    total = (await db.execute(count_q)).scalar() or 0

    # Fetch with relationships
    q = (
        select(Document)
        .options(joinedload(Document.author), joinedload(Document.group))
        .where(base_filter, access_filter)
        .limit(limit)
        .offset(offset)
    )
    
    if sort_by == "most_interactions":
        comments_count = (
            select(func.count(Comment.id))
            .where(Comment.target_type == "document", Comment.target_id == Document.id)
            .scalar_subquery()
            .correlate(Document)
        )
        likes_count = (
            select(func.count(ContentLike.id))
            .where(ContentLike.target_type == "document", ContentLike.target_id == Document.id)
            .scalar_subquery()
            .correlate(Document)
        )
        interaction_count = func.coalesce(comments_count, 0) + func.coalesce(likes_count, 0)
        q = q.order_by(interaction_count.desc(), Document.created_at.desc())
    elif sort_by == "oldest":
        q = q.order_by(Document.created_at.asc())
    else:
        # Default newest
        q = q.order_by(Document.created_at.desc())

    result = await db.execute(q)
    documents = result.unique().scalars().all()

    return list(documents), total


async def update_document(db: AsyncSession, document: Document, update_data: dict) -> Document:
    """Update document fields."""
    for key, value in update_data.items():
        setattr(document, key, value)
    await db.flush()
    return document


async def soft_delete_document(db: AsyncSession, document: Document) -> Document:
    """Soft delete a document."""
    document.is_deleted = True
    await db.flush()
    return document
