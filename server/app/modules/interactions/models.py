"""Database models for comments and likes (polymorphic — works with any content type)."""

import uuid

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, PrimaryKeyMixin, SoftDeleteMixin, TimestampMixin


class Comment(PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """A comment on an activity."""

    __tablename__ = "comments"
    __table_args__ = (
        Index("ix_comments_activity", "activity_id", "created_at"),
    )

    activity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("activities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    activity = relationship("Activity", backref="comments")
    user = relationship("User", backref="comments", lazy="joined")
    parent = relationship(
        "Comment",
        remote_side="Comment.id",
        backref="replies",
        lazy="joined",
    )

    # Backward compatibility properties
    @property
    def target_id(self) -> uuid.UUID:
        return self.activity_id

    @property
    def target_type(self) -> str:
        return "activity"


class ContentLike(PrimaryKeyMixin, Base):
    """A like on an activity — one per user per activity."""

    __tablename__ = "content_likes"
    __table_args__ = (
        UniqueConstraint(
            "activity_id", "user_id", name="uq_content_like_per_user"
        ),
        Index("ix_content_likes_activity", "activity_id"),
    )

    activity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("activities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    activity = relationship("Activity", backref="likes")

    # Backward compatibility properties
    @property
    def target_id(self) -> uuid.UUID:
        return self.activity_id

    @property
    def target_type(self) -> str:
        return "activity"
