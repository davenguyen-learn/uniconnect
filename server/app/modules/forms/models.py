import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, PrimaryKeyMixin, TimestampMixin


class FieldType(str, enum.Enum):
    text = "text"
    textarea = "textarea"
    checkbox = "checkbox"
    number = "number"


class CustomForm(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "custom_forms"

    # A form can belong to an activity OR a group
    activity_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("activities.id", ondelete="CASCADE"), nullable=True, index=True
    )
    group_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), nullable=True, index=True
    )

    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    fields = relationship(
        "FormField", 
        back_populates="form", 
        cascade="all, delete-orphan", 
        order_by="FormField.order",
        lazy="joined"
    )
    activity = relationship("Activity", back_populates="custom_form")
    group = relationship("Group", backref="custom_forms")


class FormField(PrimaryKeyMixin, Base):
    __tablename__ = "form_fields"

    form_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("custom_forms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    field_type: Mapped[FieldType] = mapped_column(
        Enum(FieldType, name="field_type", create_constraint=True),
        default=FieldType.text,
        nullable=False,
    )
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # E.g. options for dropdowns, or constraints like min/max
    meta_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    form = relationship("CustomForm", back_populates="fields")
