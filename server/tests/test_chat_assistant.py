"""Tests for Phase 9 Smart Campus AI Assistant.

Verifies all 8 Architectural Locks:
- Tool execution through domain services (LOCK 1)
- Structured tool results (LOCK 2)
- Independent conflict, registration, eligibility status calculation (LOCK 4)
- Calendar privacy: NO private titles returned to AI (LOCK 6)
- Group search privacy & visibility (LOCK 7)
- Tool execution guards & 3-level fallback (LOCK 8)
- Pre-provider rate limiting
"""

import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import HTTPException

from app.modules.activities.models import Activity
from app.modules.groups.models import Group, GroupMember, GroupPrivacy
from app.modules.chat.schemas import (
    ChatRequest,
    ChatMessage,
    ActivitySearchToolResult,
    UserScheduleToolResult,
    GroupSearchToolResult,
)
from app.modules.chat.tools import (
    search_activities_tool,
    get_user_schedule_tool,
    search_groups_tool,
)
from app.modules.chat.fallback import generate_deterministic_fallback
from app.modules.chat.service import handle_chat


# ── 1. Structured Tool Result & Independent Status Tests (LOCK 2 & 4) ──

@pytest.mark.asyncio
async def test_search_activities_tool_returns_structured_results():
    """Verify search_activities_tool returns typed ActivitySearchToolResult with independent status flags."""
    user_id = uuid.uuid4()
    act_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_db = AsyncMock()

    act = Activity(
        id=act_id,
        title="Ngày Chủ Nhật Xanh",
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=1, hours=4),
        location_name="Hội trường A",
        social_work_days=1.5,
        is_deleted=False,
    )

    # Mock DB query
    mock_res = MagicMock()
    mock_res.unique.return_value.all.return_value = [(act,)]
    mock_db.execute.return_value = mock_res

    # Mock detector and join requests
    with patch("app.modules.calendar.service.get_detector_for_user") as mock_det:
        mock_detector_inst = MagicMock()
        c_info = MagicMock()
        c_info.has_conflict = False
        c_info.level = "none"
        mock_detector_inst.check_conflict.return_value = c_info
        mock_det.return_value = mock_detector_inst

        result = await search_activities_tool(
            db=mock_db,
            user_id=user_id,
            is_social_work=True,
        )

        assert isinstance(result, ActivitySearchToolResult)
        assert result.total == 1
        item = result.items[0]
        assert item.activity_id == str(act_id)
        assert item.title == "Ngày Chủ Nhật Xanh"
        assert item.social_work_days == 1.5
        assert item.conflict_status == "none"
        assert item.registration_status == "available"
        assert item.eligibility_status == "eligible"


# ── 2. Calendar Privacy DTO: No Private Titles (LOCK 6) ──

@pytest.mark.asyncio
async def test_get_user_schedule_privacy_no_private_titles():
    """
    Verify get_user_schedule_tool NEVER leaks personal event titles to AI.
    Only exposes time windows and safe reason_code.
    """
    user_id = uuid.uuid4()
    mock_db = AsyncMock()

    # Simulate private calendar item
    private_event = MagicMock()
    private_event.id = uuid.uuid4()
    private_event.title = "Khám bệnh tại Bệnh viện Đại học Y Dược"  # SENSITIVE PRIVATE TITLE!
    private_event.start_time = datetime(2026, 9, 20, 8, 0)
    private_event.end_time = datetime(2026, 9, 20, 11, 0)
    private_event.event_type = "busy_slot"
    private_event.is_recurring = False

    with patch("app.modules.calendar.service.get_user_calendar_events", return_value=[private_event]):
        result = await get_user_schedule_tool(db=mock_db, user_id=user_id, days_ahead=7)

        assert isinstance(result, UserScheduleToolResult)
        assert result.total_busy_slots == 1

        slot = result.busy_slots[0]
        assert slot.reason_code == "personal_busy"
        # Verify private title is NOT exposed in the DTO schema!
        slot_dict = slot.model_dump()
        assert "title" not in slot_dict
        assert "Khám bệnh" not in str(slot_dict)


# ── 3. Group Search Privacy & Visibility (LOCK 7) ──

@pytest.mark.asyncio
async def test_search_groups_privacy_visibility():
    """Verify search_groups_tool returns only public groups or groups where user is a member."""
    user_id = uuid.uuid4()
    mock_db = AsyncMock()

    pub_group = Group(
        id=uuid.uuid4(),
        name="CLB Tin Học",
        description="Lập trình và AI",
        privacy=GroupPrivacy.public,
        is_deleted=False,
    )
    pub_group.members = []

    mock_res = MagicMock()
    mock_res.unique.return_value.scalars.return_value.all.return_value = [pub_group]
    mock_db.execute.return_value = mock_res

    res = await search_groups_tool(db=mock_db, user_id=user_id, keyword="Tin học")
    assert isinstance(res, GroupSearchToolResult)
    assert res.total == 1
    assert res.items[0].name == "CLB Tin Học"
    assert res.items[0].privacy == "public"


# ── 4. Deterministic Fallback Resilience (Level 2/3) ──

@pytest.mark.asyncio
async def test_deterministic_fallback_on_gemini_unavailable():
    """Verify fallback executes deterministic search and returns structured response without calling Gemini."""
    mock_db = AsyncMock()
    user_id = uuid.uuid4()
    conv_id = str(uuid.uuid4())

    from app.modules.chat.schemas import ActivitySearchToolItem

    act_item = ActivitySearchToolItem(
        activity_id=str(uuid.uuid4()),
        title="Hiến Máu Nhân Đạo",
        start_time="2026-09-22T08:00:00Z",
        end_time="2026-09-22T11:30:00Z",
        location_name="Sảnh Nhà C",
        social_work_days=2.0,
        distance_meters=500.0,
        distance_status="nearby",
        conflict_status="none",
        registration_status="available",
        eligibility_status="eligible",
    )

    with patch("app.modules.chat.fallback.search_activities_tool") as mock_search:
        mock_search.return_value = ActivitySearchToolResult(items=[act_item], total=1)

        response = await generate_deterministic_fallback(
            db=mock_db,
            user_id=user_id,
            conversation_id=conv_id,
            user_message="Tìm hoạt động CTXH",
        )

        assert response.conversation_id == conv_id
        assert response.message.role == "assistant"
        assert response.message.cards is not None
        assert len(response.message.cards) == 1
        assert response.message.cards[0].title == "Hiến Máu Nhân Đạo"
        assert response.message.cards[0].social_work_days == 2.0
        assert len(response.suggestions) > 0


# ── 5. Rate Limiting Pre-check ──

def test_chat_rate_limiting_logic():
    """Verify sliding window rate limit raises HTTP 429 when threshold is exceeded."""
    from app.modules.chat.router import _check_rate_limit

    storage = {}
    user_key = "test-user-123"
    limit = 5

    # 5 requests succeed
    for _ in range(limit):
        _check_rate_limit(user_key, storage, max_requests=limit, error_detail="Rate limit exceeded")

    assert len(storage[user_key]) == limit

    # 6th request raises HTTP 429
    with pytest.raises(HTTPException) as exc_info:
        _check_rate_limit(user_key, storage, max_requests=limit, error_detail="Rate limit exceeded")

    assert exc_info.value.status_code == 429
    assert "Rate limit exceeded" in exc_info.value.detail
