import uuid
from typing import Any
from pydantic import BaseModel, Field, field_validator
from app.modules.forms.models import FieldType

class FormFieldBase(BaseModel):
    label: str = Field(min_length=1, max_length=200)
    field_type: FieldType = FieldType.text
    is_required: bool = True
    order: int = 0
    meta_data: dict | None = None

    @field_validator("field_type", mode="before")
    @classmethod
    def normalize_field_type(cls, v: Any) -> Any:
        if v == "boolean":
            return FieldType.checkbox
        return v


class FormFieldCreate(FormFieldBase):
    pass


class FormFieldResponse(FormFieldBase):
    id: uuid.UUID

    model_config = {"from_attributes": True}


class CustomFormCreate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    description: str | None = None
    fields: list[FormFieldCreate]


class CustomFormResponse(BaseModel):
    id: uuid.UUID
    title: str | None
    description: str | None
    fields: list[FormFieldResponse]

    model_config = {"from_attributes": True}
