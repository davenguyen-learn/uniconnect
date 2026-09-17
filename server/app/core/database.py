from collections.abc import AsyncGenerator

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# Engine configuration with safe pooling defaults
is_sqlite = "sqlite" in settings.DATABASE_URL.lower()

engine_kwargs: dict[str, Any] = {
    "echo": settings.DB_ECHO,
}

if not is_sqlite:
    engine_kwargs.update(
        {
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_timeout": settings.DB_POOL_TIMEOUT,
            "pool_recycle": settings.DB_POOL_RECYCLE,
            "pool_pre_ping": settings.DB_POOL_PRE_PING,
        }
    )

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_db_connectivity(timeout: float = 3.0) -> None:
    """Check database connectivity with strict timeout. Raises on failure."""
    import asyncio
    from sqlalchemy import text

    async with asyncio.timeout(timeout):
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
