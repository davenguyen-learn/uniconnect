"""Auth business logic — uses session directly (no repository)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.auth.schemas import LoginRequest, RegisterRequest, TokenResponse
from app.modules.users.models import User


async def register(db: AsyncSession, data: RegisterRequest) -> TokenResponse:
    """Register a new user and return an access token."""
    # Check for duplicate email
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise ConflictError("A user with this email already exists.")

    # Check for duplicate username
    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        raise ConflictError("This username is already taken.")

    # Create user
    user = User(
        email=data.email,
        username=data.username,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        university=data.university,
    )
    db.add(user)
    await db.flush()  # Populate user.id without committing

    token = create_access_token(str(user.id), user.role.value)
    return TokenResponse(access_token=token)


async def login(db: AsyncSession, data: LoginRequest) -> TokenResponse:
    """Authenticate a user and return an access token."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise UnauthorizedError("Invalid email or password.")

    if not user.is_active:
        raise UnauthorizedError("This account has been deactivated.")

    token = create_access_token(str(user.id), user.role.value)
    return TokenResponse(access_token=token)
