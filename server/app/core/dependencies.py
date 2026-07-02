"""Shared FastAPI dependencies."""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    """Extract and validate the current user from the JWT Bearer token.

    Returns a dict with 'sub' (user_id) and 'role'.
    """
    if not credentials:
        raise UnauthorizedError("Authentication required.")

    payload = decode_access_token(credentials.credentials)
    return payload


def require_role(*allowed_roles: str):
    """Factory returning a dependency that checks if the user has an allowed role."""

    async def _check_role(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("role") not in allowed_roles:
            raise ForbiddenError("Insufficient permissions.")
        return current_user

    return _check_role
