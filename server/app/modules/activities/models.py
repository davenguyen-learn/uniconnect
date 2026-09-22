import enum
import uuid

from geoalchemy2 import Geography
from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym
from pgvector.sqlalchemy import Vector

from app.core.models import Base, PrimaryKeyMixin, SoftDeleteMixin, TimestampMixin
import app.modules.trophies.models  # noqa: F401
import app.modules.forms.models  # noqa: F401



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
    private_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    # PostGIS geography column — uses SRID 4326 (WGS 84)
    marker_location = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,
    )
    meeting_location: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Synonyms for backward compatibility
    location = synonym("marker_location")
    location_name = synonym("meeting_location")
    
    # 768 is the default dimension for Gemini embeddings (models/text-embedding-004)
    embedding = mapped_column(Vector(768), nullable=True)

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

    social_work_days: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)

    group_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), nullable=True, index=True
    )
    
    custom_form_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("custom_forms.id", ondelete="SET NULL"), nullable=True
    )
    
    attendance_mode: Mapped[str] = mapped_column(
        String(20), default="manual", server_default="manual", nullable=False
    )
    check_in_code: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )
    check_in_radius: Mapped[int] = mapped_column(
        Integer, default=300, server_default="300", nullable=False
    )

    # Relationships
    host = relationship("User", backref="hosted_activities", lazy="joined")
    group = relationship("Group", back_populates="activities", lazy="joined")
    trophies = relationship("Trophy", back_populates="activity", cascade="all, delete-orphan")
    custom_form = relationship("CustomForm", back_populates="activity", uselist=False, lazy="joined")

    # Backward compatibility properties
    @property
    def trophy(self):
        return self.trophies[0] if self.trophies else None

    @property
    def trophy_id(self) -> uuid.UUID | None:
        return self.trophies[0].id if self.trophies else None

    @trophy_id.setter
    def trophy_id(self, value: uuid.UUID | None) -> None:
        pass
