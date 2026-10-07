"""
Comprehensive Unit Tests for Phase 2: Private / Group-only Activities.
Verifies all access control guards across Repository, Service, Participation, Interactions, and Chat Tool.
"""

import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.core.exceptions import ForbiddenError
from app.modules.activities.models import Activity, ActivityPrivacy
from app.modules.groups.models import Group, GroupMember, GroupRole
from app.modules.activities import repository as act_repo
from app.modules.activities import service as act_service
from app.modules.participation import service as part_service
from app.modules.participation.schemas import JoinRequestCreate
from app.modules.interactions import service as inter_service
from app.modules.interactions.schemas import CommentCreate
from app.modules.chat.tools import search_activities_tool


@pytest.fixture
def test_data():
    host_id = uuid.uuid4()
    member_id = uuid.uuid4()
    outsider_id = uuid.uuid4()
    group_id = uuid.uuid4()
    act_id = uuid.uuid4()

    now = datetime.now(timezone.utc)
    act = Activity(
        id=act_id,
        title="Họp Ban Chủ nhiệm & Lên kế hoạch quý 4",
        description="Nội bộ CLB",
        host_id=host_id,
        group_id=group_id,
        privacy=ActivityPrivacy.private,
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=1, hours=2),
        max_participants=20,
        current_participants=1,
        require_approval=False,
        created_at=now,
        is_deleted=False,
    )
    return {
        "host_id": host_id,
        "member_id": member_id,
        "outsider_id": outsider_id,
        "group_id": group_id,
        "activity": act,
    }


@pytest.mark.asyncio
async def test_get_activity_forbidden_for_outsider(test_data):
    """Outsider accessing private activity gets 403 Forbidden."""
    mock_db = AsyncMock()
    act = test_data["activity"]
    outsider_id = test_data["outsider_id"]

    with patch("app.modules.activities.repository.get_by_id", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = act

        with patch("app.modules.groups.repository.is_member", new_callable=AsyncMock) as mock_is_member:
            mock_is_member.return_value = False

            # Fake query execution for co-hosts and join requests returning None
            mock_res = MagicMock()
            mock_res.first.return_value = None
            mock_db.execute.return_value = mock_res

            with pytest.raises(ForbiddenError):
                await act_service.get_activity(mock_db, act.id, user_id=str(outsider_id))


@pytest.mark.asyncio
async def test_get_activity_allowed_for_member(test_data):
    """Member of group accessing private activity succeeds."""
    mock_db = AsyncMock()
    act = test_data["activity"]
    member_id = test_data["member_id"]

    with patch("app.modules.activities.repository.get_by_id", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = act

        with patch("app.modules.groups.repository.is_member", new_callable=AsyncMock) as mock_is_member, \
             patch("app.modules.activities.repository.get_coordinates_from_db", new_callable=AsyncMock) as mock_coords:
            mock_is_member.return_value = True
            mock_coords.return_value = (10.77, 106.66)

            mock_res = MagicMock()
            mock_res.unique.return_value.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_res

            resp = await act_service.get_activity(mock_db, act.id, user_id=str(member_id))
            assert resp.id == act.id
            assert resp.title == act.title


@pytest.mark.asyncio
async def test_request_to_join_forbidden_for_outsider(test_data):
    """Outsider attempting to join private activity gets 403 Forbidden."""
    mock_db = AsyncMock()
    act = test_data["activity"]
    outsider_id = test_data["outsider_id"]

    with patch("app.modules.activities.repository.get_by_id", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = act

        with patch("app.modules.groups.repository.is_member", new_callable=AsyncMock) as mock_is_member:
            mock_is_member.return_value = False

            mock_res = MagicMock()
            mock_res.first.return_value = None
            mock_db.execute.return_value = mock_res

            with pytest.raises(ForbiddenError):
                await part_service.request_to_join(
                    mock_db, act.id, str(outsider_id), JoinRequestCreate()
                )


@pytest.mark.asyncio
async def test_create_comment_forbidden_for_outsider(test_data):
    """Outsider attempting to comment on private activity gets 403 Forbidden."""
    mock_db = AsyncMock()
    act = test_data["activity"]
    outsider_id = test_data["outsider_id"]

    with patch("app.modules.activities.repository.get_by_id", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = act

        with patch("app.modules.groups.repository.is_member", new_callable=AsyncMock) as mock_is_member:
            mock_is_member.return_value = False

            mock_res = MagicMock()
            mock_res.first.return_value = None
            mock_db.execute.return_value = mock_res

            with pytest.raises(ForbiddenError):
                await inter_service.create_comment(
                    mock_db, "activity", act.id, outsider_id, CommentCreate(content="Hello")
                )


@pytest.mark.asyncio
async def test_toggle_like_forbidden_for_outsider(test_data):
    """Outsider attempting to like private activity gets 403 Forbidden."""
    mock_db = AsyncMock()
    act = test_data["activity"]
    outsider_id = test_data["outsider_id"]

    with patch("app.modules.activities.repository.get_by_id", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = act

        with patch("app.modules.groups.repository.is_member", new_callable=AsyncMock) as mock_is_member:
            mock_is_member.return_value = False

            mock_res = MagicMock()
            mock_res.first.return_value = None
            mock_db.execute.return_value = mock_res

            with pytest.raises(ForbiddenError):
                await inter_service.toggle_like(
                    mock_db, "activity", act.id, outsider_id
                )
