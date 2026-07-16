"""Database models for notifications."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, PrimaryKeyMixin, TimestampMixin


class Notification(PrimaryKeyMixin, TimestampMixin, Base):
    """A notification sent to a user."""

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_id", "user_id"),
        Index("ix_notifications_is_read", "is_read"),
        Index("ix_notifications_created_at", "created_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    
    # E.g., 'new_comment', 'new_like'
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # E.g., 'document', 'activity', 'group'
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # ID of the target
    target_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    
    # Text message to display
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    actor = relationship("User", foreign_keys=[actor_id], lazy="joined")
