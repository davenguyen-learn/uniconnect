"""Domain exceptions.

Each exception maps to a specific HTTP status code. The exception_handlers
module translates these into standardized JSON error responses so services
and repositories never need to know about HTTP.
"""


class AppException(Exception):
    """Base exception for all domain errors."""

    code: str = "INTERNAL_ERROR"
    status_code: int = 500
    message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None, details: dict | None = None):
        self.message = message or self.__class__.message
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppException):
    code = "NOT_FOUND"
    status_code = 404
    message = "The requested resource was not found."


class ConflictError(AppException):
    code = "CONFLICT"
    status_code = 409
    message = "A resource conflict occurred."


class ForbiddenError(AppException):
    code = "FORBIDDEN"
    status_code = 403
    message = "You do not have permission to perform this action."


class UnauthorizedError(AppException):
    code = "UNAUTHORIZED"
    status_code = 401
    message = "Authentication is required."


class ValidationError(AppException):
    code = "VALIDATION_ERROR"
    status_code = 422
    message = "The request contains invalid data."


class CapacityFullError(AppException):
    code = "CAPACITY_FULL"
    status_code = 409
    message = "This activity has reached its maximum capacity."
