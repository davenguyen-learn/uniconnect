"""Tests for Pillar 3: DB Connection Pooling, Session Lifecycle & Observability."""

import time
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.core.config import settings
from app.core.database import get_db, is_sqlite
from app.modules.chat.router import (
    MAX_STORAGE_ENTRIES,
    WINDOW_SECONDS,
    _check_rate_limit,
    _sweep_if_exceeded_ceiling,
    cleanup_rate_limits,
)
from fastapi import HTTPException


# ── 1. Database Pooling & Configuration Tests ──

def test_db_pool_configuration_parameters():
    """Verify that DB pool parameters have robust, configurable defaults in Settings."""
    assert settings.DB_POOL_SIZE == 20
    assert settings.DB_MAX_OVERFLOW == 10
    assert settings.DB_POOL_TIMEOUT == 30.0
    assert settings.DB_POOL_RECYCLE == 1800
    assert settings.DB_POOL_PRE_PING is True


def test_sqlite_compatibility_check():
    """Verify is_sqlite flag correctly reflects database dialect in DATABASE_URL."""
    # When DATABASE_URL contains postgresql, is_sqlite should be False
    assert ("postgresql" in settings.DATABASE_URL.lower()) is (not is_sqlite)


# ── 2. DB Session Lifecycle & Rollback Tests ──

@pytest.mark.asyncio
async def test_get_db_commits_on_normal_completion():
    """Verify get_db commits pending changes when no exception is raised."""
    mock_session = AsyncMock()
    mock_session_factory = MagicMock(return_value=mock_session)
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    with patch("app.core.database.async_session_factory", mock_session_factory):
        async for session in get_db():
            assert session == mock_session

        # Verifying normal exit calls commit
        assert mock_session.commit.called
        assert not mock_session.rollback.called


@pytest.mark.asyncio
async def test_get_db_rolls_back_on_exception():
    """Verify get_db rolls back transaction and re-raises when an exception occurs inside request."""
    mock_session = AsyncMock()
    mock_session_factory = MagicMock(return_value=mock_session)
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    with patch("app.core.database.async_session_factory", mock_session_factory):
        gen = get_db()
        session = await anext(gen)
        assert session == mock_session

        with pytest.raises(RuntimeError, match="Service-level failure"):
            await gen.athrow(RuntimeError("Service-level failure"))

        # Must have called rollback, not commit
        assert mock_session.rollback.called
        assert not mock_session.commit.called


# ── 3. Rate Limiter Memory Lifecycle Tests ──

def test_rate_limiter_prunes_expired_timestamps_and_keys():
    """Verify that timestamps older than WINDOW_SECONDS are pruned and empty keys removed."""
    storage: dict[str, list[float]] = {}
    now = 1000.0

    # Old entries: expired 100s ago
    storage["ip_old_1"] = [now - 100.0, now - 90.0]
    storage["ip_old_2"] = [now - 61.0]

    # Active entry: recent
    storage["ip_active"] = [now - 10.0]

    removed_count = cleanup_rate_limits(storage, now=now)
    assert removed_count == 2
    assert "ip_old_1" not in storage
    assert "ip_old_2" not in storage
    assert "ip_active" in storage
    assert storage["ip_active"] == [now - 10.0]


def test_rate_limiter_sweep_when_exceeding_max_ceiling():
    """Verify that storage dictionary is bounded by MAX_STORAGE_ENTRIES ceiling."""
    storage: dict[str, list[float]] = {}
    now = 5000.0

    # Populate storage slightly above MAX_STORAGE_ENTRIES
    for i in range(MAX_STORAGE_ENTRIES + 50):
        # Even numbered keys are expired, odd numbered keys are recent
        if i % 2 == 0:
            storage[f"key_{i}"] = [now - WINDOW_SECONDS - 10.0]
        else:
            storage[f"key_{i}"] = [now - 5.0]

    assert len(storage) == MAX_STORAGE_ENTRIES + 50

    # Trigger sweep
    _sweep_if_exceeded_ceiling(storage, now=now)

    # Expired keys should be removed, bringing total down well below ceiling
    assert len(storage) <= MAX_STORAGE_ENTRIES


def test_rate_limiter_enforces_limit_and_stores_current():
    """Verify sliding window limit correctly rejects after max requests."""
    storage: dict[str, list[float]] = {}
    key = "test_user_1"

    # Make requests up to limit
    for _ in range(5):
        _check_rate_limit(key=key, storage=storage, max_requests=5, error_detail="Rate limited")

    assert len(storage[key]) == 5

    # 6th request must raise 429
    with pytest.raises(HTTPException) as exc:
        _check_rate_limit(key=key, storage=storage, max_requests=5, error_detail="Rate limited")
    assert exc.value.status_code == 429
