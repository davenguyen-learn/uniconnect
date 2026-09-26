"""
Unit tests for the 4 fallback branches of handle_chat when LLM synthesis is empty or tools fail.

Tests:
1. Search returns cards (collected_cards > 0) -> cards returned + proper card preamble.
2. In-domain no-match (tool executed, 0 cards, no error) -> polite no-match message.
3. Tool exception/timeout (had_tool_error = True) -> technical error message.
4. Conversational / no tool called (total_tool_calls == 0) -> standard assistant greeting.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.modules.chat.schemas import ChatRequest, ChatMessage, ActivitySearchToolResult, ActivitySearchToolItem
from app.modules.chat.service import handle_chat


@pytest.mark.asyncio
async def test_branch_1_search_returns_cards_with_empty_synthesis():
    """Branch 1: Tool returns cards, synthesis response is empty string -> preamble with cards."""
    user_id = uuid.uuid4()
    mock_db = AsyncMock()

    # Create mock tool result with cards
    fake_item = ActivitySearchToolItem(
        activity_id=str(uuid.uuid4()),
        title="Bách Khoa Hackathon 2026",
        start_time="2026-10-01T08:00:00Z",
        end_time="2026-10-01T17:00:00Z",
        location_name="Hội trường A5",
        conflict_status="none",
        registration_status="available",
        eligibility_status="eligible",
    )
    mock_tool_res = ActivitySearchToolResult(
        items=[fake_item],
        total=1,
        query="hackathon",
    )

    # Mock Gemini client
    with patch("app.modules.chat.service.genai.Client") as mock_client_cls, \
         patch("app.modules.chat.service.search_activities_tool", new_callable=AsyncMock) as mock_search:
        
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        # Turn 1: model calls tool
        func_call = MagicMock()
        func_call.name = "search_activities"
        func_call.args = {"keyword": "hackathon"}
        
        turn1_resp = MagicMock()
        turn1_resp.function_calls = [func_call]
        turn1_resp.candidates = [MagicMock()]
        turn1_resp.text = ""
        
        # Turn 2 (synthesis): model returns empty text
        turn2_resp = MagicMock()
        turn2_resp.function_calls = None
        turn2_resp.text = ""
        
        mock_client.models.generate_content.side_effect = [turn1_resp, turn2_resp]
        mock_search.return_value = mock_tool_res

        chat_req = ChatRequest(message="Tìm cuộc thi hackathon")
        result = await handle_chat(db=mock_db, user_id=user_id, request=chat_req)

        assert result.message.cards is not None
        assert len(result.message.cards) == 1
        assert "UniConnect đã tìm thấy 1 hoạt động" in result.message.content
        assert result.message.cards[0].title == "Bách Khoa Hackathon 2026"


@pytest.mark.asyncio
async def test_branch_2_in_domain_no_match():
    """Branch 2: Tool runs successfully but finds 0 cards -> polite in-domain no-match message."""
    user_id = uuid.uuid4()
    mock_db = AsyncMock()

    mock_tool_res = ActivitySearchToolResult(
        items=[],
        total=0,
        query="bóng rổ 23h",
    )

    with patch("app.modules.chat.service.genai.Client") as mock_client_cls, \
         patch("app.modules.chat.service.search_activities_tool", new_callable=AsyncMock) as mock_search:
        
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        func_call = MagicMock()
        func_call.name = "search_activities"
        func_call.args = {"keyword": "bóng rổ 23h"}
        
        turn1_resp = MagicMock()
        turn1_resp.function_calls = [func_call]
        turn1_resp.candidates = [MagicMock()]
        turn1_resp.text = ""
        
        turn2_resp = MagicMock()
        turn2_resp.function_calls = None
        turn2_resp.text = ""
        
        mock_client.models.generate_content.side_effect = [turn1_resp, turn2_resp]
        mock_search.return_value = mock_tool_res

        chat_req = ChatRequest(message="Có giải bóng rổ 23h không?")
        result = await handle_chat(db=mock_db, user_id=user_id, request=chat_req)

        assert result.message.cards is None
        assert "UniConnect hiện chưa tìm thấy hoạt động nào phù hợp" in result.message.content
        assert "Mình đã kiểm tra thông tin cho bạn rồi nhé!" not in result.message.content


@pytest.mark.asyncio
async def test_branch_3_tool_execution_error():
    """Branch 3: Tool encounters timeout or exception -> technical error message."""
    user_id = uuid.uuid4()
    mock_db = AsyncMock()

    with patch("app.modules.chat.service.genai.Client") as mock_client_cls, \
         patch("app.modules.chat.service.search_activities_tool", new_callable=AsyncMock) as mock_search:
        
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        func_call = MagicMock()
        func_call.name = "search_activities"
        func_call.args = {"keyword": "test"}
        
        turn1_resp = MagicMock()
        turn1_resp.function_calls = [func_call]
        turn1_resp.candidates = [MagicMock()]
        turn1_resp.text = ""
        
        turn2_resp = MagicMock()
        turn2_resp.function_calls = None
        turn2_resp.text = ""
        
        mock_client.models.generate_content.side_effect = [turn1_resp, turn2_resp]
        # Simulate tool failure
        mock_search.side_effect = RuntimeError("Database connection timeout")

        chat_req = ChatRequest(message="Tìm hoạt động")
        result = await handle_chat(db=mock_db, user_id=user_id, request=chat_req)

        assert result.message.cards is None
        assert "Hiện tại hệ thống tra cứu hoạt động đang gặp sự cố gián đoạn tạm thời" in result.message.content


@pytest.mark.asyncio
async def test_branch_4_conversational_no_tool_called():
    """Branch 4: Conversational query where no tools are invoked and synthesis is empty -> greeting."""
    user_id = uuid.uuid4()
    mock_db = AsyncMock()

    with patch("app.modules.chat.service.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        # Turn 1: No tool calls, empty text returned
        turn1_resp = MagicMock()
        turn1_resp.function_calls = None
        turn1_resp.text = ""
        
        mock_client.models.generate_content.return_value = turn1_resp

        chat_req = ChatRequest(message="Xin chào")
        result = await handle_chat(db=mock_db, user_id=user_id, request=chat_req)

        assert result.message.cards is None
        assert "Chào bạn! Mình là Trợ lý Sinh viên UniConnect" in result.message.content
