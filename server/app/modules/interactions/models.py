"""Database models for comments and likes (polymorphic — works with any content type)."""

import uuid

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, PrimaryKeyMixin, SoftDeleteMixin, TimestampMixin


class Comment(PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """A comment on any content type (activity, document, etc.)."""

    __tablename__ = "comments"
    __table_args__ = (
        Index("ix_comments_target", "target_type", "target_id", "created_at"),
    )

    target_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    target_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    user = relationship("User", backref="comments", lazy="joined")
    parent = relationship(
        "Comment",
        remote_side="Comment.id",
        backref="replies",
        lazy="joined",
    )


class ContentLike(PrimaryKeyMixin, Base):
    """A like on any content type — one per user per target."""

    __tablename__ = "content_likes"
    __table_args__ = (
        UniqueConstraint(
            "target_type", "target_id", "user_id", name="uq_content_like_per_user"
        ),
        Index("ix_content_likes_target", "target_type", "target_id"),
    )

    target_type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(nullable=False)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
