import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, PrimaryKeyMixin, TimestampMixin


class VerificationStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class AdminAuditAction(str, enum.Enum):
    verify_organization = "verify_organization"
    reject_organization = "reject_organization"
    deactivate_user = "deactivate_user"
    activate_user = "activate_user"
    change_user_role = "change_user_role"
    resolve_report = "resolve_report"
    dismiss_report = "dismiss_report"
    hide_activity = "hide_activity"
    suspend_group = "suspend_group"
    activate_group = "activate_group"


class AdminAuditTargetType(str, enum.Enum):
    user = "user"
    activity = "activity"
    report = "report"
    verification = "verification"
    group = "group"


class OrganizationVerificationRequest(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "organization_verification_requests"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization_name: Mapped[str] = mapped_column(String(150), nullable=False)
    faculty: Mapped[str | None] = mapped_column(String(150), nullable=True)
    document_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="verification_status", create_constraint=True),
        default=VerificationStatus.pending,
        server_default=VerificationStatus.pending.value,
        nullable=False,
        index=True,
    )
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("app.modules.users.models.User", foreign_keys=[user_id])
    reviewer = relationship("app.modules.users.models.User", foreign_keys=[reviewed_by])


class AdminAuditLog(PrimaryKeyMixin, Base):
    __tablename__ = "admin_audit_logs"

    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    target_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    actor = relationship("app.modules.users.models.User", foreign_keys=[actor_id])
