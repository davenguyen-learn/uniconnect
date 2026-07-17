import enum
import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, func, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, PrimaryKeyMixin


class RequestStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    declined = "declined"
    cancelled = "cancelled"


class JoinRequest(PrimaryKeyMixin, Base):
    __tablename__ = "join_requests"
    __table_args__ = (
        # Partial unique index: only one active (pending/approved) request per user per activity
        Index(
            "uq_active_request_per_user",
            "activity_id",
            "user_id",
            unique=True,
            postgresql_where=(
                "status IN ('pending', 'approved')"
            ),
        ),
    )

    activity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("activities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus, name="request_status", create_constraint=True),
        default=RequestStatus.pending,
        server_default=RequestStatus.pending.value,
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    responded_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    form_responses: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    attendance_confirmed: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )

    # Relationships
    activity = relationship("Activity", backref="join_requests", lazy="joined")
    user = relationship("User", backref="join_requests", lazy="joined")
