import enum
import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, Integer, String, Text, Enum, UniqueConstraint, CheckConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, PrimaryKeyMixin, TimestampMixin


class TrophyGrantStatus(str, enum.Enum):
    insufficient_quorum = "insufficient_quorum"
    eligible_for_review = "eligible_for_review"
    approved = "approved"
    rejected = "rejected"


class Trophy(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trophies"

    activity_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("activities.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    activity = relationship("Activity", back_populates="trophies")

    # Backward compatibility properties
    @property
    def points(self) -> int:
        return 0

    @property
    def icon(self) -> str:
        return "🏆"

    @property
    def creator_id(self) -> uuid.UUID | None:
        return None


class UserTrophy(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_trophies"
    __table_args__ = (
        UniqueConstraint("activity_id", "user_id", name="uq_user_trophy_activity_user"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    trophy_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("trophies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    activity_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("activities.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    user = relationship("User", backref="trophies")
    trophy = relationship("Trophy")
    activity = relationship("Activity")


class TrophyGrantRequest(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trophy_grant_requests"
    __table_args__ = (
        UniqueConstraint("activity_id", name="uq_trophy_grant_request_activity"),
        CheckConstraint("actual_attended_count >= 0", name="ck_trophy_request_attended_count_nonneg"),
        CheckConstraint("min_participants_required > 0", name="ck_trophy_request_min_participants_pos"),
    )

    activity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("activities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    trophy_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("trophies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[TrophyGrantStatus] = mapped_column(
        Enum(TrophyGrantStatus, name="trophy_grant_status", create_type=False),
        nullable=False,
        default=TrophyGrantStatus.insufficient_quorum,
    )
    min_participants_required: Mapped[int] = mapped_column(
        Integer, default=10, server_default="10", nullable=False
    )
    actual_attended_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    activity = relationship("Activity")
    trophy = relationship("Trophy")
    reviewer = relationship("User", foreign_keys=[reviewed_by])

