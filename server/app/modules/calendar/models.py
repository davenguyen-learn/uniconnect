import enum
import uuid
from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, PrimaryKeyMixin, TimestampMixin


class RecurrenceType(str, enum.Enum):
    none = "none"
    weekly = "weekly"


class UserBusySlot(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_busy_slots"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    recurrence: Mapped[str] = mapped_column(
        String(20), default=RecurrenceType.none.value, server_default=RecurrenceType.none.value, nullable=False
    )

    # 1. One-off slots: specific absolute datetimes
    start_datetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_datetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # 2. Weekly recurring slots:
    # day_of_week: 0 = Monday, 6 = Sunday (ISO standard)
    day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_time_of_day: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time_of_day: Mapped[time | None] = mapped_column(Time, nullable=True)

    # Validity interval for recurrence (e.g. valid for this semester only)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Relationships
    user = relationship("User", backref="busy_slots", lazy="selectin")
    exceptions = relationship("BusySlotException", backref="busy_slot", cascade="all, delete-orphan", lazy="selectin")

    __table_args__ = (
        Index("idx_busy_user_weekly", "user_id", "day_of_week", "start_time_of_day", "end_time_of_day"),
        Index("idx_busy_user_onetime", "user_id", "start_datetime", "end_datetime"),
    )


class BusySlotException(PrimaryKeyMixin, Base):
    """Skipped instances of a recurring busy slot (e.g. single day off/holiday)."""
    __tablename__ = "busy_slot_exceptions"

    busy_slot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user_busy_slots.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skip_date: Mapped[date] = mapped_column(Date, nullable=False)

    __table_args__ = (
        Index("idx_busy_exception_slot_date", "busy_slot_id", "skip_date", unique=True),
    )


class UserVacationPeriod(PrimaryKeyMixin, TimestampMixin, Base):
    """Longer vacation or holiday period where weekly class commitments are suspended."""
    __tablename__ = "user_vacation_periods"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    user = relationship("User", backref="vacation_periods", lazy="selectin")

    __table_args__ = (
        Index("idx_vacation_user_dates", "user_id", "start_date", "end_date"),
    )
