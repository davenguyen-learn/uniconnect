"""Deterministic Fallback Service (Level 2 & Level 3).

Guarantees high-availability when Gemini AI provider is unavailable, rate-limited,
or unconfigured. Never calls Gemini in fallback mode!
"""

import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.chat.schemas import (
    ChatMessage,
    ChatResponse,
    ChatEventCardItem,
)
from app.modules.chat.tools import search_activities_tool, search_groups_tool

logger = logging.getLogger(__name__)


async def generate_deterministic_fallback(
    db: AsyncSession,
    user_id: uuid.UUID | None,
    conversation_id: str,
    user_message: str,
    user_lat: float | None = None,
    user_lng: float | None = None,
) -> ChatResponse:
    """
    Level 2: Deterministic search using UniConnect domain services directly.
    Level 3: Safe generic helpful response if search produces no results or fails.
    """
    msg_lower = user_message.lower().strip()
    is_ctxh = any(kw in msg_lower for kw in ["ctxh", "công tác xã hội", "tình nguyện", "ngày ctxh"])
    is_group = any(kw in msg_lower for kw in ["clb", "câu lạc bộ", "nhóm", "tuyển"])
    
    cards: list[ChatEventCardItem] = []
    suggestions = [
        "Tìm hoạt động CTXH cuối tuần này",
        "Có hoạt động nào gần trường không?",
        "Danh sách các CLB đang tuyển thành viên",
    ]

    try:
        if is_group:
            # Group search intent
            group_res = await search_groups_tool(
                db=db,
                user_id=user_id,
                keyword=user_message if len(user_message) < 50 else None,
                limit=4,
            )
            if group_res.items:
                group_names = ", ".join([f"**{g.name}**" for g in group_res.items[:3]])
                content = (
                    f"Hiện trợ lý AI đang trong giờ cao điểm, nhưng UniConnect đã tìm thấy các câu lạc bộ phù hợp với bạn: "
                    f"{group_names}. Bạn có thể vào mục **Câu Lạc Bộ** để xem thông tin chi tiết và nộp đơn gia nhập nhé!"
                )
            else:
                content = (
                    "Hiện tại chưa tìm thấy câu lạc bộ cụ thể theo từ khóa của bạn. "
                    "Bạn hãy khám phá thêm danh sách đầy đủ tại mục **Câu Lạc Bộ** trên thanh điều hướng nhé!"
                )
        else:
            # Activity search intent
            act_res = await search_activities_tool(
                db=db,
                user_id=user_id,
                keyword=user_message if len(user_message) < 40 else None,
                is_social_work=True if is_ctxh else None,
                exclude_user_busy_times=True,
                lat=user_lat,
                lng=user_lng,
                radius_meters=25000,
                limit=4,
            )

            for act in act_res.items:
                cards.append(
                    ChatEventCardItem(
                        activity_id=act.activity_id,
                        title=act.title,
                        start_time=act.start_time,
                        end_time=act.end_time,
                        location_name=act.location_name,
                        social_work_days=act.social_work_days,
                        distance_meters=act.distance_meters,
                        distance_status=act.distance_status,
                        conflict_status=act.conflict_status,
                        registration_status=act.registration_status,
                        eligibility_status=act.eligibility_status,
                    )
                )

            if cards:
                content = (
                    f"Trợ lý AI tạm thời đạt giới hạn lưu lượng, nhưng hệ thống đã lọc sẵn "
                    f"**{len(cards)} hoạt động** phù hợp nhất với yêu cầu của bạn (đã loại trừ lịch bận cá nhân):"
                )
            else:
                # Level 3: Safe generic response
                content = (
                    "Hệ thống trợ lý AI đang trong giờ cao điểm. Bạn có thể tra cứu nhanh các sự kiện đang diễn ra "
                    "tại trang **Khám Phá Hoạt Động** hoặc xem thời khóa biểu tại mục **Lịch Thông Minh**."
                )

    except Exception as e:
        logger.error(f"Deterministic fallback failed: {e}", exc_info=True)
        # Level 3 generic safe response
        content = (
            "Hệ thống đang bảo trì kết nối trợ lý AI. Vui lòng quay lại sau ít phút hoặc tra cứu trực tiếp "
            "trên trang chủ UniConnect nhé!"
        )

    chat_msg = ChatMessage(
        role="assistant",
        content=content,
        cards=cards if cards else None,
    )

    return ChatResponse(
        conversation_id=conversation_id,
        message=chat_msg,
        reply=chat_msg.content,
        suggestions=suggestions,
    )
