"""Shared response schemas used across all modules."""

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Standardized error response envelope."""

    error: ErrorDetail


class PaginatedResponse(BaseModel):
    """Pagination metadata returned alongside list results."""

    total: int
    limit: int
    offset: int
    has_more: bool
