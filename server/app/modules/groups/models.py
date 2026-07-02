import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, PrimaryKeyMixin, SoftDeleteMixin, TimestampMixin


class GroupRole(str, enum.Enum):
    admin = "admin"
    member = "member"


class Group(PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "groups"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    allow_member_activities: Mapped[bool] = mapped_column(
        default=True, server_default="true", nullable=False
    )
    allow_member_documents: Mapped[bool] = mapped_column(
        default=True, server_default="true", nullable=False
    )

    # Relationships
    owner = relationship("User", backref="owned_groups", lazy="joined")
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="group")


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
