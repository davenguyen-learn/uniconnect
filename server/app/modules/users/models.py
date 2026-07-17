import enum
import uuid

from sqlalchemy import Boolean, Enum, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, PrimaryKeyMixin, TimestampMixin


class UserRole(str, enum.Enum):
    student = "student"
    moderator = "moderator"
    admin = "admin"


class User(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    university: Mapped[str | None] = mapped_column(String(150), nullable=True)

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", create_constraint=True),
        default=UserRole.student,
        server_default=UserRole.student.value,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )

    # Relationships
    following = relationship(
        "UserFollow",
        foreign_keys="UserFollow.follower_id",
        back_populates="follower",
        cascade="all, delete-orphan"
    )
    followers = relationship(
        "UserFollow",
        foreign_keys="UserFollow.following_id",
        back_populates="following",
        cascade="all, delete-orphan"
    )


class UserFollow(TimestampMixin, Base):
    __tablename__ = "user_follows"

    follower_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    following_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )

    # Relationships
    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")
    following = relationship("User", foreign_keys=[following_id], back_populates="followers")
