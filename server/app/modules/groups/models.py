import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, PrimaryKeyMixin, SoftDeleteMixin, TimestampMixin
import app.modules.activities.models  # noqa: F401
import app.modules.forms.models  # noqa: F401



class GroupRole(str, enum.Enum):
    admin = "admin"
    member = "member"


class GroupPrivacy(str, enum.Enum):
    public = "public"
    private = "private"


class Group(PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "groups"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    public_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    private_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    allow_member_activities: Mapped[bool] = mapped_column(default=True, server_default="true")
    require_approval: Mapped[bool] = mapped_column(default=True, server_default="true", nullable=False)
    
    privacy: Mapped[GroupPrivacy] = mapped_column(
        Enum(GroupPrivacy, name="group_privacy", create_constraint=True),
        default=GroupPrivacy.public,
        server_default=GroupPrivacy.public.value,
    )
    
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationships
    owner = relationship("User", backref="owned_groups", lazy="joined")
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="group")
    
    custom_form_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("custom_forms.id", ondelete="SET NULL"), nullable=True
    )
    custom_form = relationship("CustomForm", lazy="joined")


class GroupMember(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "group_members"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_user"),
    )

    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[GroupRole] = mapped_column(
        Enum(GroupRole, name="group_role", create_constraint=True),
        default=GroupRole.member,
        server_default=GroupRole.member.value,
    )

    # Relationships
    group = relationship("Group", back_populates="members")
    user = relationship("User", backref="group_memberships", lazy="joined")


class GroupJoinRequest(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "group_join_requests"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_active_group_request"),
        Index("idx_join_req_group_status", "group_id", "status"),
    )

    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    
    # Optional form responses
    form_responses: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    user = relationship("User", lazy="joined")
    group = relationship("Group", lazy="joined")


class ActivityCoHost(PrimaryKeyMixin, TimestampMixin, Base):
    """Represents an accepted co-host relationship between an Activity and a Group."""
    __tablename__ = "activity_cohosts"
    __table_args__ = (
        UniqueConstraint("activity_id", "group_id", name="uq_activity_cohost"),
        Index("idx_cohost_group", "group_id"),
        Index("idx_cohost_activity", "activity_id"),
    )

    activity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("activities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationships
    activity = relationship("Activity", backref="co_hosts", lazy="joined")
    group = relationship("Group", backref="co_hosted_activities", lazy="joined")


class ActivityCoHostInvitation(PrimaryKeyMixin, TimestampMixin, Base):
    """Represents a co-host invitation sent from Lead Host group to an invited group."""
    __tablename__ = "activity_cohost_invitations"
    __table_args__ = (
        Index("idx_invite_group_status", "invited_group_id", "status"),
        Index("idx_invite_act_status", "activity_id", "status"),
    )

    activity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("activities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    host_group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    invited_group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # 'pending', 'accepted', 'declined'
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    activity = relationship("Activity", lazy="joined")
    host_group = relationship("Group", foreign_keys=[host_group_id], lazy="joined")
    invited_group = relationship("Group", foreign_keys=[invited_group_id], lazy="joined")

