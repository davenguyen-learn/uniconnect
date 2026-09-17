from unittest.mock import patch
import pytest


@pytest.mark.asyncio
async def test_health_check_healthy_with_latency_and_timing_header(async_client):
    """Verify /health returns 200, healthy DB status, latency_ms, and X-Process-Time header."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["db"] == "healthy"
    assert isinstance(data["latency_ms"], (int, float))
    assert data["latency_ms"] >= 0
    assert "version" in data
    # Observability timing header
    assert "X-Process-Time" in response.headers
    assert response.headers["X-Process-Time"].endswith("ms")


@pytest.mark.asyncio
async def test_health_check_db_failure_returns_503_without_leaking_info(async_client):
    """Verify that when database connection fails, /health returns 503 degraded without leaking credentials."""
    with patch("app.main.check_db_connectivity", side_effect=Exception("Database connection timeout or refused")):
        response = await async_client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["db"] == "unhealthy"
        assert "version" in data
        # Ensure no sensitive credentials, stacktrace, or hostnames leak to response
        assert "Database connection timeout" not in str(data)
        assert "password" not in str(data)
        assert "user" not in data
        # Observability header must still be present on 503
        assert "X-Process-Time" in response.headers
        assert response.headers["X-Process-Time"].endswith("ms")


@pytest.mark.asyncio
async def test_health_check_db_timeout_returns_503(async_client):
    """Verify that a DB timeout triggers 503 service unavailable."""
    with patch("app.main.check_db_connectivity", side_effect=TimeoutError("Timed out")):
        response = await async_client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["db"] == "unhealthy"
