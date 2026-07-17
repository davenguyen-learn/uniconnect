import uuid
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, PrimaryKeyMixin, TimestampMixin


class Trophy(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trophies"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    icon_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # The organization or verified user who created this trophy
    creator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    # Relationships
    creator = relationship("User", backref="created_trophies")


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
