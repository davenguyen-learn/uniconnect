import uuid
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, PrimaryKeyMixin, TimestampMixin


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
