"""
Unit tests for Chatbot Action Tool (add_personal_busy_slot) and Self-Study Scheduling.
Phase 1 of GVPB improvement plan.
"""

import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.modules.calendar.schemas import BusySlotResponse, ConflictInfo, ConflictDetail
from app.modules.chat.schemas import ChatRequest, AddBusySlotToolResult
from app.modules.chat.tools import add_personal_busy_slot_tool
from app.modules.chat.service import handle_chat
from app.modules.chat.fallback import generate_deterministic_fallback, classify_fallback_intent


@pytest.fixture(autouse=True)
def mock_gemini_api_key():
    with patch("app.modules.chat.service.settings.GEMINI_API_KEY", "test-mock-gemini-key"):
        yield


@pytest.mark.asyncio
async def test_add_personal_busy_slot_tool_success_one_off():
    """Test adding a one-off busy slot successfully without conflict."""
    mock_db = AsyncMock()
    user_id = uuid.uuid4()
    slot_id = uuid.uuid4()

    fake_slot = BusySlotResponse(
        id=slot_id,
        user_id=user_id,
        title="Tự học Lập trình Web",
        recurrence="none",
        start_datetime=datetime(2026, 10, 14, 19, 30, tzinfo=timezone.utc),
        end_datetime=datetime(2026, 10, 14, 21, 30, tzinfo=timezone.utc),
    )

    with patch("app.modules.calendar.service.get_detector_for_user", new_callable=AsyncMock) as mock_detector_getter, \
         patch("app.modules.calendar.service.create_busy_slot", new_callable=AsyncMock) as mock_create_slot:

        detector = MagicMock()
        detector.check_conflict.return_value = ConflictInfo(has_conflict=False, level="none", can_join=True)
        mock_detector_getter.return_value = detector
        mock_create_slot.return_value = fake_slot

        result = await add_personal_busy_slot_tool(
            db=mock_db,
            user_id=user_id,
            title="Tự học Lập trình Web",
            start_time="2026-10-14T19:30:00Z",
            end_time="2026-10-14T21:30:00Z",
            recurrence="none",
        )

        assert result.success is True
        assert result.slot_id == str(slot_id)
        assert result.title == "Tự học Lập trình Web"
        assert result.has_conflict is False
        assert "Đã thêm thành công" in result.message
        mock_create_slot.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_personal_busy_slot_tool_success_weekly():
    """Test adding a weekly recurring busy slot."""
    mock_db = AsyncMock()
    user_id = uuid.uuid4()
    slot_id = uuid.uuid4()

    fake_slot = BusySlotResponse(
        id=slot_id,
        user_id=user_id,
        title="Lịch tự học định kỳ",
        recurrence="weekly",
        day_of_week=2,
    )

    with patch("app.modules.calendar.service.get_detector_for_user", new_callable=AsyncMock) as mock_detector_getter, \
         patch("app.modules.calendar.service.create_busy_slot", new_callable=AsyncMock) as mock_create_slot:

        detector = MagicMock()
        detector.check_conflict.return_value = ConflictInfo(has_conflict=False, level="none", can_join=True)
        mock_detector_getter.return_value = detector
        mock_create_slot.return_value = fake_slot

        result = await add_personal_busy_slot_tool(
            db=mock_db,
            user_id=user_id,
            title="Lịch tự học định kỳ",
            start_time="2026-10-14T19:30:00+07:00",
            end_time="2026-10-14T21:30:00+07:00",
            recurrence="weekly",
            day_of_week=2,
        )

        assert result.success is True
        assert result.slot_id == str(slot_id)
        assert result.recurrence == "weekly"


@pytest.mark.asyncio
async def test_add_personal_busy_slot_tool_conflict():
    """Test rejection when schedule conflict is detected."""
    mock_db = AsyncMock()
    user_id = uuid.uuid4()

    conflict_detail = ConflictDetail(
        type="approved_activity",
        title="Hội thảo Khoa học 2026",
        time_range="19:00 - 21:00",
        target_id=str(uuid.uuid4()),
    )
    conflict_info = ConflictInfo(
        has_conflict=True,
        level="hard_conflict",
        can_join=False,
        warning_message="Bạn đã được duyệt tham gia hoạt động 'Hội thảo Khoa học 2026'.",
        conflicting_with=conflict_detail,
    )

    with patch("app.modules.calendar.service.get_detector_for_user", new_callable=AsyncMock) as mock_detector_getter:
        detector = MagicMock()
        detector.check_conflict.return_value = conflict_info
        mock_detector_getter.return_value = detector

        result = await add_personal_busy_slot_tool(
            db=mock_db,
            user_id=user_id,
            title="Tự học",
            start_time="2026-10-14T19:30:00Z",
            end_time="2026-10-14T21:30:00Z",
        )

        assert result.success is False
        assert result.has_conflict is True
        assert "Xung đột lịch" in result.message
        assert "Hội thảo Khoa học 2026" in result.message


@pytest.mark.asyncio
async def test_add_personal_busy_slot_tool_invalid_times():
    """Test rejection when end_time is before or equal to start_time."""
    mock_db = AsyncMock()
    user_id = uuid.uuid4()

    result = await add_personal_busy_slot_tool(
        db=mock_db,
        user_id=user_id,
        title="Tự học",
        start_time="2026-10-14T21:30:00Z",
        end_time="2026-10-14T19:30:00Z",
    )

    assert result.success is False
    assert "sau thời gian bắt đầu" in result.message


@pytest.mark.asyncio
async def test_handle_chat_executes_add_personal_busy_slot():
    """Test handle_chat dispatches add_personal_busy_slot tool call and commits DB."""
    user_id = uuid.uuid4()
    mock_db = AsyncMock()

    tool_mock_result = AddBusySlotToolResult(
        success=True,
        slot_id=str(uuid.uuid4()),
        title="Lịch tự học",
        start_time="2026-10-14T19:30:00+07:00",
        end_time="2026-10-14T21:30:00+07:00",
        recurrence="weekly",
        message="Đã thêm thành công",
        has_conflict=False,
    )

    with patch("app.modules.chat.service.genai.Client") as mock_client_cls, \
         patch("app.modules.chat.service.add_personal_busy_slot_tool", new_callable=AsyncMock) as mock_action_tool:

        mock_action_tool.return_value = tool_mock_result
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # Turn 1: Gemini calls add_personal_busy_slot
        func_call = MagicMock()
        func_call.name = "add_personal_busy_slot"
        func_call.args = {
            "title": "Lịch tự học",
            "start_time": "2026-10-14T19:30:00+07:00",
            "end_time": "2026-10-14T21:30:00+07:00",
            "recurrence": "weekly",
        }

        turn1_resp = MagicMock()
        turn1_resp.function_calls = [func_call]
        turn1_resp.candidates = [MagicMock()]

        # Turn 2: Synthesis response confirming action
        turn2_resp = MagicMock()
        turn2_resp.function_calls = None
        turn2_resp.text = "Mình đã thêm lịch tự học tối thứ 4 vào [Lịch Thông Minh](/calendar) cho bạn rồi nhé!"

        mock_client.models.generate_content.side_effect = [turn1_resp, turn2_resp]

        req = ChatRequest(message="Với lịch hiện tại, tôi nên xếp thời gian tự học thế nào cho hợp lý?")
        chat_resp = await handle_chat(db=mock_db, user_id=user_id, request=req)

        mock_action_tool.assert_awaited_once()
        mock_db.commit.assert_awaited_once()
        assert "[Lịch Thông Minh](/calendar)" in chat_resp.reply


@pytest.mark.asyncio
async def test_fallback_study_planning():
    """Test deterministic fallback handles self-study scheduling query."""
    user_id = uuid.uuid4()
    mock_db = AsyncMock()

    # Verify intent classification
    intent = classify_fallback_intent("Với lịch hiện tại, tôi nên xếp thời gian tự học thế nào cho hợp lý?")
    assert intent == "STUDY_PLANNING"

    fake_res = AddBusySlotToolResult(
        success=True,
        slot_id=str(uuid.uuid4()),
        title="Lịch tự học",
        start_time="2026-10-14T19:30:00+07:00",
        end_time="2026-10-14T21:30:00+07:00",
        recurrence="weekly",
        message="Đã lưu thành công",
        has_conflict=False,
    )

    with patch("app.modules.chat.fallback.add_personal_busy_slot_tool", new_callable=AsyncMock) as mock_action_tool:
        mock_action_tool.return_value = fake_res

        chat_resp = await generate_deterministic_fallback(
            db=mock_db,
            user_id=user_id,
            conversation_id=str(uuid.uuid4()),
            user_message="Với lịch hiện tại, tôi nên xếp thời gian tự học thế nào cho hợp lý?",
        )

        mock_action_tool.assert_awaited_once()
        mock_db.commit.assert_awaited_once()
        assert "Lịch tự học" in chat_resp.reply
        assert "[Lịch Thông Minh](/calendar)" in chat_resp.reply


@pytest.mark.asyncio
async def test_create_schedule_plan_tool_success():
    """Test creating multiple slots in a single schedule plan."""
    from app.modules.chat.tools import create_schedule_plan_tool

    mock_db = AsyncMock()
    user_id = uuid.uuid4()
    slot_id_1 = uuid.uuid4()
    slot_id_2 = uuid.uuid4()

    fake_slot_1 = BusySlotResponse(
        id=slot_id_1,
        user_id=user_id,
        title="Ôn thi sáng",
        recurrence="weekly",
        day_of_week=0,
    )
    fake_slot_2 = BusySlotResponse(
        id=slot_id_2,
        user_id=user_id,
        title="Rèn luyện thể thao",
        recurrence="weekly",
        day_of_week=0,
    )

    with patch("app.modules.calendar.service.get_detector_for_user", new_callable=AsyncMock) as mock_detector_getter, \
         patch("app.modules.calendar.service.create_busy_slot", new_callable=AsyncMock) as mock_create_slot:

        detector = MagicMock()
        detector.check_conflict.return_value = ConflictInfo(has_conflict=False, level="none", can_join=True)
        mock_detector_getter.return_value = detector
        mock_create_slot.side_effect = [fake_slot_1, fake_slot_2]

        result = await create_schedule_plan_tool(
            db=mock_db,
            user_id=user_id,
            plan_title="Kế hoạch ôn thi 10 ngày",
            slots=[
                {
                    "title": "Ôn thi sáng",
                    "start_time": "2026-10-07T08:30:00+07:00",
                    "end_time": "2026-10-07T11:00:00+07:00",
                    "recurrence": "weekly",
                    "day_of_week": 0,
                    "valid_until": "2026-10-17",
                },
                {
                    "title": "Rèn luyện thể thao",
                    "start_time": "2026-10-07T16:30:00+07:00",
                    "end_time": "2026-10-07T17:30:00+07:00",
                    "recurrence": "weekly",
                    "day_of_week": 0,
                    "valid_until": "2026-10-17",
                },
            ],
        )

        assert result.success is True
        assert result.total_slots_created == 2
        assert len(result.slots) == 2
        assert mock_create_slot.await_count == 2


@pytest.mark.asyncio
async def test_fallback_exam_sprint_multi_activity():
    """Test deterministic fallback schedules multiple slots when user asks for 10-day exam prep with sports."""
    user_id = uuid.uuid4()
    mock_db = AsyncMock()

    with patch("app.modules.chat.fallback.create_schedule_plan_tool", new_callable=AsyncMock) as mock_plan_tool:
        from app.modules.chat.schemas import CreateSchedulePlanToolResult, CreateSchedulePlanItemResult
        mock_plan_tool.return_value = CreateSchedulePlanToolResult(
            success=True,
            total_slots_created=3,
            slots=[
                CreateSchedulePlanItemResult(success=True, title="Ôn thi sáng", start_time="08:30", end_time="11:00", recurrence="weekly", message="ok"),
                CreateSchedulePlanItemResult(success=True, title="Thể thao chiều", start_time="16:30", end_time="17:30", recurrence="weekly", message="ok"),
                CreateSchedulePlanItemResult(success=True, title="Luyện đề tối", start_time="19:30", end_time="21:30", recurrence="weekly", message="ok"),
            ],
            message="Đã xếp 3 khung giờ",
        )

        chat_resp = await generate_deterministic_fallback(
            db=mock_db,
            user_id=user_id,
            conversation_id=str(uuid.uuid4()),
            user_message="10 ngày nữa là tôi phải thi rồi, tôi thi 4 môn, sắp xếp thời gian học tập, nghỉ ngơi và tập luyện thể thao cho tôi đi",
        )

        mock_plan_tool.assert_awaited_once()
        mock_db.commit.assert_awaited_once()
        assert "10 ngày" in chat_resp.reply
        assert "[Lịch Thông Minh](/calendar)" in chat_resp.reply

