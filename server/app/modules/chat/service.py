"""Chat Agent Service with Tool Execution Guards and 3-Level Fallback."""

import uuid
import asyncio
import logging
from datetime import datetime, timezone
from google import genai
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.chat.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatEventCardItem,
)
from app.modules.chat.tools import (
    search_activities_tool,
    get_user_schedule_tool,
    search_groups_tool,
)
from app.modules.chat.fallback import generate_deterministic_fallback
from app.modules.chat.provider import CHAT_TOOLS, SYSTEM_INSTRUCTION, get_model_candidates

logger = logging.getLogger(__name__)

# Tool Execution Guards (LOCK 8)
MAX_TOOL_ROUNDS = 3
MAX_TOOL_CALLS_PER_REQUEST = 6
TOOL_TIMEOUT_SECONDS = 5.0

DEFAULT_SUGGESTIONS = [
    "Cuối tuần này có hoạt động CTXH nào không?",
    "Kiểm tra xem lịch thứ 7 của mình có trống không?",
    "CLB nào đang tuyển thành viên mới?",
]


async def handle_chat(
    db: AsyncSession,
    user_id: uuid.UUID | None,
    request: ChatRequest,
    user_lat: float | None = None,
    user_lng: float | None = None,
) -> ChatResponse:
    """
    Orchestrates user prompt, Gemini function calling with execution guards,
    and automatic 3-level fallback.
    """
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    # Extract latest user message
    latest_user_text = ""
    if request.message:
        latest_user_text = request.message.strip()
    elif request.messages and len(request.messages) > 0:
        latest_user_text = request.messages[-1].content.strip()

    lat = request.user_lat if request.user_lat is not None else user_lat
    lng = request.user_lng if request.user_lng is not None else user_lng

    # If Gemini API key is not configured, directly execute Level 2 Fallback
    if not settings.GEMINI_API_KEY:
        logger.info("GEMINI_API_KEY not set. Using deterministic fallback.")
        return await generate_deterministic_fallback(
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=latest_user_text,
            user_lat=lat,
            user_lng=lng,
        )

    # Initialize Gemini client
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
    except Exception as e:
        logger.warning(f"Failed to initialize Gemini Client: {e}")
        return await generate_deterministic_fallback(
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=latest_user_text,
            user_lat=lat,
            user_lng=lng,
        )

    # Convert request messages to Gemini Content
    gemini_contents: list[types.Content] = []
    if request.messages and len(request.messages) > 0:
        for m in request.messages[-6:]:  # Keep last 6 messages within request session boundary
            role = "user" if m.role in ("user", "human") else "model"
            gemini_contents.append(
                types.Content(role=role, parts=[types.Part.from_text(text=m.content)])
            )
    else:
        gemini_contents.append(
            types.Content(role="user", parts=[types.Part.from_text(text=latest_user_text)])
        )

    model_candidates = get_model_candidates()
    collected_cards: list[ChatEventCardItem] = []
    total_tool_calls = 0
    final_reply_text = ""

    # Attempt Level 1: Gemini Provider Loop
    try:
        used_model = model_candidates[0]
        response = None

        for model_name in model_candidates:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=gemini_contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        tools=[CHAT_TOOLS],
                        temperature=0.7,
                    ),
                )
                used_model = model_name
                break
            except Exception as e:
                logger.warning(f"Model {model_name} invocation failed: {e}")
                continue

        if not response:
            raise RuntimeError("All Gemini model candidates failed.")

        # Tool calling loop with guards
        current_round = 0
        while response and response.function_calls and current_round < MAX_TOOL_ROUNDS:
            current_round += 1
            tool_parts: list[types.Part] = []

            for function_call in response.function_calls:
                total_tool_calls += 1
                if total_tool_calls > MAX_TOOL_CALLS_PER_REQUEST:
                    logger.warning("Exceeded MAX_TOOL_CALLS_PER_REQUEST guard.")
                    break

                func_name = function_call.name
                func_args = function_call.args or {}
                logger.info(f"Executing tool: {func_name} with args: {func_args}")

                try:
                    if func_name == "search_activities":
                        tool_result = await asyncio.wait_for(
                            search_activities_tool(
                                db=db,
                                user_id=user_id,
                                keyword=func_args.get("keyword"),
                                category=func_args.get("category"),
                                is_social_work=func_args.get("is_social_work"),
                                exclude_user_busy_times=func_args.get("exclude_user_busy_times", True),
                                lat=lat,
                                lng=lng,
                                radius_meters=func_args.get("radius_meters", 25000),
                                limit=func_args.get("limit", 4),
                            ),
                            timeout=TOOL_TIMEOUT_SECONDS,
                        )
                        # Extract cards for UI rendering
                        for item in tool_result.items:
                            collected_cards.append(
                                ChatEventCardItem(
                                    activity_id=item.activity_id,
                                    title=item.title,
                                    start_time=item.start_time,
                                    end_time=item.end_time,
                                    meeting_location=getattr(item, "meeting_location", None) or item.location_name,
                                    location_name=getattr(item, "meeting_location", None) or item.location_name,
                                    social_work_days=item.social_work_days,
                                    distance_meters=item.distance_meters,
                                    distance_status=item.distance_status,
                                    conflict_status=item.conflict_status,
                                    registration_status=item.registration_status,
                                    eligibility_status=item.eligibility_status,
                                )
                            )
                        tool_payload = tool_result.model_dump()

                    elif func_name == "get_user_schedule":
                        if user_id:
                            tool_result = await asyncio.wait_for(
                                get_user_schedule_tool(
                                    db=db,
                                    user_id=user_id,
                                    days_ahead=func_args.get("days_ahead", 7),
                                ),
                                timeout=TOOL_TIMEOUT_SECONDS,
                            )
                            tool_payload = tool_result.model_dump()
                        else:
                            tool_payload = {"busy_slots": [], "total_busy_slots": 0}

                    elif func_name == "search_groups":
                        tool_result = await asyncio.wait_for(
                            search_groups_tool(
                                db=db,
                                user_id=user_id,
                                keyword=func_args.get("keyword"),
                                limit=func_args.get("limit", 4),
                            ),
                            timeout=TOOL_TIMEOUT_SECONDS,
                        )
                        tool_payload = tool_result.model_dump()

                    else:
                        tool_payload = {"error": f"Unknown tool name: {func_name}"}

                except asyncio.TimeoutError:
                    logger.warning(f"Tool {func_name} timed out after {TOOL_TIMEOUT_SECONDS}s")
                    tool_payload = {"error": "Tool execution timed out."}
                except Exception as tool_err:
                    logger.warning(f"Tool {func_name} execution error: {tool_err}")
                    tool_payload = {"error": f"Tool execution failed: {str(tool_err)}"}

                tool_parts.append(
                    types.Part.from_function_response(
                        name=func_name,
                        response=tool_payload,
                    )
                )

            # Append model's thought & our tool response to contents
            if response.candidates and response.candidates[0].content:
                gemini_contents.append(response.candidates[0].content)
            gemini_contents.append(types.Content(role="user", parts=tool_parts))

            # Synthesize final natural response
            try:
                response = client.models.generate_content(
                    model=used_model,
                    contents=gemini_contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.7,
                    ),
                )
            except Exception as synth_err:
                logger.warning(f"Synthesis step failed with {used_model}: {synth_err}")
                break

        final_reply_text = (response.text if response and response.text else "").strip()
        if not final_reply_text:
            if collected_cards:
                final_reply_text = f"UniConnect đã tìm thấy {len(collected_cards)} hoạt động phù hợp với bạn bên dưới:"
            else:
                final_reply_text = "Mình đã kiểm tra thông tin cho bạn rồi nhé!"

        chat_msg = ChatMessage(
            role="assistant",
            content=final_reply_text,
            cards=collected_cards if collected_cards else None,
        )

        return ChatResponse(
            conversation_id=conversation_id,
            message=chat_msg,
            reply=chat_msg.content,
            suggestions=DEFAULT_SUGGESTIONS,
        )

    except Exception as gemini_err:
        logger.error(f"Gemini provider error, executing Level 2 fallback: {gemini_err}", exc_info=True)
        return await generate_deterministic_fallback(
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=latest_user_text,
            user_lat=lat,
            user_lng=lng,
        )
