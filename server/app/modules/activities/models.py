import enum
import uuid

from geoalchemy2 import Geography
from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, PrimaryKeyMixin, SoftDeleteMixin, TimestampMixin


class ActivityPrivacy(str, enum.Enum):
    public = "public"
    private = "private"


class Activity(PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "activities"
    __table_args__ = (
        CheckConstraint("max_participants > 0", name="ck_positive_capacity"),
        CheckConstraint("end_time > start_time", name="ck_end_after_start"),
        CheckConstraint("current_participants >= 0", name="ck_nonneg_participants"),
    )

    host_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    # PostGIS geography column — uses SRID 4326 (WGS 84)
    location = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,
    )
    location_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    start_time: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)

    max_participants: Mapped[int] = mapped_column(Integer, nullable=False)
    current_participants: Mapped[int] = mapped_column(Integer, default=1, server_default="1")

    privacy: Mapped[ActivityPrivacy] = mapped_column(
        Enum(ActivityPrivacy, name="activity_privacy", create_constraint=True),
        default=ActivityPrivacy.public,
        server_default=ActivityPrivacy.public.value,
    )
    
    require_approval: Mapped[bool] = mapped_column(
        default=True,
        server_default="true",
    )

    group_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Relationships
    host = relationship("User", backref="hosted_activities", lazy="joined")
    group = relationship("Group", back_populates="activities", lazy="joined")
