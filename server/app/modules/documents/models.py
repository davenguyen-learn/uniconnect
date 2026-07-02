"""Database models for documents."""

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, PrimaryKeyMixin, SoftDeleteMixin, TimestampMixin


class Document(PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """A document shared by a user, either public or in a group."""

    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_author", "author_id"),
        Index("ix_documents_group", "group_id"),
        Index("ix_documents_created_at", "created_at"),
    )

    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    group_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    file_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    author = relationship("User", backref="documents", lazy="joined")
    group = relationship("Group", backref="documents", lazy="selectin")
