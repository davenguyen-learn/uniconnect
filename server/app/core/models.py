import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class TimestampMixin:
    """Adds created_at and updated_at columns to a model."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Adds soft delete support via is_deleted flag and deleted_at timestamp."""

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
        index=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )


class PrimaryKeyMixin:
    """UUID primary key with auto-generation."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )


# Automatically pre-load all model classes into Base registry
import app.modules.users.models  # noqa: F401, E402
import app.modules.trophies.models  # noqa: F401, E402
import app.modules.forms.models  # noqa: F401, E402
import app.modules.activities.models  # noqa: F401, E402
import app.modules.groups.models  # noqa: F401, E402
import app.modules.participation.models  # noqa: F401, E402
import app.modules.interactions.models  # noqa: F401, E402
import app.modules.documents.models  # noqa: F401, E402
import app.modules.notifications.models  # noqa: F401, E402
import app.modules.reports.models  # noqa: F401, E402

