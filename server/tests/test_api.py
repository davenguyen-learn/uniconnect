from unittest.mock import AsyncMock, MagicMock, patch
import pytest


@pytest.mark.asyncio
async def test_health_check_healthy_with_latency_and_timing_header(async_client):
    """Verify /health returns 200, healthy DB status, latency_ms, and X-Process-Time header."""
    with patch("app.main.check_db_connectivity", new_callable=AsyncMock):
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


@pytest.mark.asyncio
async def test_cors_preflight_allows_vercel_preview_domains(async_client):
    """Verify that dynamic Vercel preview domains pass CORS preflight with Access-Control-Allow-Origin."""
    headers = {
        "Origin": "https://uniconnect-hb3395h42-daven-sub0.vercel.app",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,authorization",
    }
    response = await async_client.options("/api/v1/auth/register", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://uniconnect-hb3395h42-daven-sub0.vercel.app"
    assert response.headers.get("access-control-allow-credentials") == "true"


@pytest.mark.asyncio
async def test_get_my_activities_upcoming_success(async_client):
    """Verify GET /api/v1/activities/mine?status=upcoming&limit=20 handles related models and returns 200."""
    import uuid
    from datetime import datetime, timezone
    from app.core.dependencies import get_current_user
    from app.core.database import get_db
    from app.modules.activities.models import Activity, ActivityPrivacy

    test_user_id = uuid.uuid4()
    app_instance = async_client._transport.app

    async def mock_current_user():
        return {"sub": str(test_user_id), "role": "student"}

    mock_db = AsyncMock()
    async def mock_get_db():
        yield mock_db

    app_instance.dependency_overrides[get_current_user] = mock_current_user
    app_instance.dependency_overrides[get_db] = mock_get_db

    act_id = uuid.uuid4()
    mock_act = MagicMock(spec=Activity)
    mock_act.id = act_id
    mock_act.host_id = test_user_id
    mock_act.group_id = uuid.uuid4()
    mock_act.title = "Kỳ thi thử Thuật toán BK"
    mock_act.description = "Luyện đề cùng CLB"
    mock_act.private_description = None
    mock_act.category = "Study"
    mock_act.meeting_location = "Hội trường C6"
    mock_act.location_name = "Hội trường C6"
    mock_act.start_time = datetime.now(timezone.utc)
    mock_act.end_time = datetime.now(timezone.utc)
    mock_act.max_participants = 50
    mock_act.current_participants = 10
    mock_act.privacy = ActivityPrivacy.public
    mock_act.require_approval = False
    mock_act.social_work_days = 0.5
    mock_act.created_at = datetime.now(timezone.utc)
    mock_act.attendance_mode = "manual"
    mock_act.check_in_radius = 300
    mock_act.is_deleted = False

    # Simulate loaded host and group in __dict__
    mock_host = MagicMock()
    mock_host.username = "test_host"
    mock_host.full_name = "Test Host"
    mock_host.avatar_url = None

    mock_grp = MagicMock()
    mock_grp.id = mock_act.group_id
    mock_grp.name = "CLB Tin Hoc"
    mock_grp.avatar_url = None

    mock_act.__dict__["host"] = mock_host
    mock_act.__dict__["group"] = mock_grp
    mock_act.__dict__["trophies"] = []
    mock_act.__dict__["custom_form"] = None
    mock_act.trophy = None
    mock_act.custom_form = None

    with patch("app.modules.activities.repository.list_hosted_activities", new_callable=AsyncMock) as mock_list, \
         patch("app.modules.activities.repository.get_coordinates_from_db", new_callable=AsyncMock) as mock_coords:
        mock_list.return_value = ([mock_act], 1)
        mock_coords.return_value = (10.772, 106.657)

        try:
            response = await async_client.get("/api/v1/activities/mine?status=upcoming&limit=20")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert len(data["items"]) == 1
            assert data["items"][0]["title"] == "Kỳ thi thử Thuật toán BK"
            assert data["items"][0]["group"]["name"] == "CLB Tin Hoc"
            assert data["items"][0]["latitude"] == 10.772
            assert data["items"][0]["longitude"] == 106.657
        finally:
            app_instance.dependency_overrides.pop(get_current_user, None)
            app_instance.dependency_overrides.pop(get_db, None)

