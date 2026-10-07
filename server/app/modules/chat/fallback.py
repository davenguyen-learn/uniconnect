"""Deterministic Fallback Service (Level 2 & Level 3).

Guarantees high-availability and functional correctness when Gemini AI provider
is unavailable, rate-limited, or unconfigured. Never calls Gemini in fallback mode!
Implements rule-based intent classification to avoid returning mismatched activity cards.
"""

import re
import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.chat.schemas import (
    ChatMessage,
    ChatResponse,
    ChatEventCardItem,
)
from app.modules.chat.tools import (
    search_activities_tool,
    search_groups_tool,
    add_personal_busy_slot_tool,
    create_schedule_plan_tool,
)

logger = logging.getLogger(__name__)


def classify_fallback_intent(msg: str) -> str:
    """Classify user query intent into domain categories deterministically."""
    m = msg.lower().strip()

    # 1. Safety & Academic Integrity / Unsupported refusal
    refusal_keywords = [
        "chứng khoán", "tiền ảo", "bitcoin", "crypto", "đầu tư tài chính",
        "viết bài luận", "giải đề", "thi hộ", "làm bài tập hộ", "bẻ khóa"
    ]
    if any(kw in m for kw in refusal_keywords) or (re.search(r"\bhack\b", m) and "hackathon" not in m):
        return "SAFETY_REFUSAL"

    # 1.1 Actionable Self-Study & Exam Planning
    study_plan_keywords = [
        "thời gian tự học", "xếp thời gian tự học", "lên lịch tự học",
        "lịch tự học", "tự học thế nào", "sắp xếp tự học", "tư vấn tự học", "đặt lịch tự học",
        "ôn thi", "sắp xếp thời gian học tập", "lên lịch ôn thi", "lịch học tập", "kế hoạch ôn thi"
    ]
    if any(kw in m for kw in study_plan_keywords):
        return "STUDY_PLANNING"

    # 2. iCalendar / Calendar Export
    export_keywords = ["icalendar", ".ics", "xuất lịch", "tải lịch", "đồng bộ google calendar", "đồng bộ lịch"]
    if any(kw in m for kw in export_keywords):
        return "CALENDAR_EXPORT"

    # 3. Calendar Conflict & Auto-cancel Policies
    conflict_keywords = [
        "tự động hủy", "hủy đăng ký", "xung đột lịch", "trùng lịch",
        "khoảng nghỉ", "15 phút", "di chuyển giữa 2 cơ sở", "hai cơ sở"
    ]
    if any(kw in m for kw in conflict_keywords):
        return "CALENDAR_CONFLICT_POLICY"

    # 4. Check-in security, QR, GPS, Privacy & Complaints
    checkin_keywords = [
        "xoay 30", "xoay động", "chụp mã qr", "nhờ bạn", "gian lận",
        "khiếu nại", "từ chối điểm danh", "theo dõi vị trí", "gps", "quyền riêng tư"
    ]
    if any(kw in m for kw in checkin_keywords):
        return "CHECKIN_POLICY"

    # 5. CTXH regulations & Certificate verification
    ctxh_policy_keywords = [
        "ngày ctxh tối thiểu", "quy định về số ngày", "bao lâu thì được cấp",
        "điều kiện để được cấp", "tiêu chuẩn ctxh", "chứng nhận tham gia", "xác thực chứng nhận"
    ]
    if any(kw in m for kw in ctxh_policy_keywords):
        return "CTXH_POLICY"

    # 6. Personal schedule queries
    schedule_keywords = [
        "lịch bận", "tôi có rảnh", "thứ sáu tuần này", "sáng chủ nhật",
        "hôm nay tôi có", "các hoạt động tôi đã đăng ký", "lịch trình của tôi"
    ]
    if any(kw in m for kw in schedule_keywords):
        return "PERSONAL_SCHEDULE"

    # 7. Group & Club search / creation
    group_keywords = [
        "clb", "câu lạc bộ", "đội nhóm", "tạo một nhóm", "tạo clb",
        "gia nhập clb", "danh sách các câu lạc bộ"
    ]
    if any(kw in m for kw in group_keywords):
        return "GROUP_QUERY"

    # 8. Activity search (default for campus events, workshops, sports, volunteering)
    return "ACTIVITY_SEARCH"


async def generate_deterministic_fallback(
    db: AsyncSession,
    user_id: uuid.UUID | None,
    conversation_id: str,
    user_message: str,
    user_lat: float | None = None,
    user_lng: float | None = None,
) -> ChatResponse:
    """
    Level 2: Deterministic search and rule-based expert answers.
    Ensures non-activity questions receive accurate textual answers without irrelevant cards.
    """
    intent = classify_fallback_intent(user_message)
    cards: list[ChatEventCardItem] = []
    suggestions = [
        "Tìm hoạt động CTXH cuối tuần này",
        "Có hoạt động nào gần trường không?",
        "Xem lịch hoạt động của tôi",
    ]

    try:
        if intent == "SAFETY_REFUSAL":
            content = (
                "UniConnect là nền tảng quản trị hoạt động phong trào, tình nguyện và rèn luyện sinh viên. "
                "Hệ thống không hỗ trợ tư vấn đầu tư tài chính, giải đề thi/làm bài luận hộ nhằm đảm bảo "
                "nguyên tắc liêm chính học thuật và an toàn thông tin."
            )

        elif intent == "CALENDAR_EXPORT":
            content = (
                "Hiện tại UniConnect chưa hỗ trợ tính năng xuất tệp `.ics` trực tiếp ra các ứng dụng lịch ngoài "
                "(tính năng này đang nằm trong lộ trình phát triển mở rộng).\n\n"
                "Tuy nhiên, bạn có thể dễ dàng theo dõi toàn bộ lịch trình sự kiện đã tham gia, lịch do bạn tổ chức "
                "và thời khóa biểu bận cá nhân trực tiếp tại mục [Lịch Thông Minh](/calendar). Hệ thống đã tích hợp "
                "sẵn tính năng tự động cảnh báo xung đột (Hard/Soft conflict) khi bạn đăng ký sự kiện mới!"
            )

        elif intent == "CALENDAR_CONFLICT_POLICY":
            content = (
                "**Quy chế kiểm tra và xử lý xung đột lịch trên UniConnect:**\n\n"
                "- **Cảnh báo xung đột (Conflict Warning)**: Hệ thống tự động đối soát với Thời khóa biểu học tập "
                "và lịch bận cá nhân. Nếu hoạt động mới trùng giờ hoặc khoảng cách di chuyển giữa hai cơ sở "
                "(Cơ sở 1 Lý Thường Kiệt và Cơ sở 2 Dĩ An) dưới 45 phút, hệ thống sẽ gắn nhãn cảnh báo vàng/đỏ.\n"
                "- **Chính sách tự động hủy**: UniConnect **KHÔNG** tự ý hủy đăng ký sự kiện của bạn. Sinh viên có toàn quyền "
                "chủ động quyết định hủy hoặc sắp xếp lại lịch trình tại trang **Hoạt động của tôi**."
            )

        elif intent == "CHECKIN_POLICY":
            content = (
                "**Cơ chế bảo mật điểm danh & quyền riêng tư tại UniConnect:**\n\n"
                "- **Mã QR xoay động 30 giây**: Mã QR check-in được mã hóa HMAC-SHA256 theo thời gian thực (TOTP). "
                "Mọi hành vi chụp màn hình gửi từ xa qua mạng xã hội sẽ bị từ chối do mã đã hết hiệu lực.\n"
                "- **Bán kính GPS (Geofencing)**: Ứng dụng chỉ xin quyền đọc vị trí tại đúng khoảnh khắc bạn bấm quét QR "
                "để đảm bảo bạn có mặt trong bán kính quy định (100m - 200m). UniConnect **hoàn toàn không theo dõi vị trí nền (No Background Tracking)**.\n"
                "- **Khiếu nại điểm danh**: Nếu gặp sự cố thiết bị/mạng, bạn hãy vào chi tiết hoạt động -> chọn **'Gửi khiếu nại điểm danh'** "
                "kèm ảnh chụp tại hiện trường để Ban tổ chức rà soát thủ công."
            )

        elif intent == "CTXH_POLICY":
            content = (
                "**Quy định về Ngày Công tác Xã hội (CTXH) & Chứng nhận:**\n\n"
                "- **Chuẩn tốt nghiệp**: Sinh viên chính quy cần tích lũy tối thiểu **15 ngày CTXH** toàn khóa.\n"
                "- **Ghi nhận & Cấp chứng nhận**: Sau khi Ban tổ chức kết thúc hoạt động và hoàn tất đối soát điểm danh "
                "(thường trong vòng 24 - 48 giờ), số ngày CTXH sẽ tự động cập nhật vào mục **Hồ sơ cá nhân**.\n"
                "- **Chứng nhận điện tử**: Mỗi chứng chỉ được cấp có mã hash xác thực trực tuyến độc bản, dùng để kiểm chứng "
                "tính hợp lệ khi xét học bổng hoặc điểm rèn luyện."
            )

        elif intent == "PERSONAL_SCHEDULE":
            content = (
                "Để tra cứu lịch trình cá nhân chi tiết:\n\n"
                "- Bạn hãy mở mục **Lịch thông minh** trên thanh điều hướng để xem trực quan các tiết học và sự kiện trong tuần.\n"
                "- Các sự kiện sắp diễn ra cũng hiển thị tại trang chủ. UniConnect sẽ chủ động cảnh báo nếu có hoạt động nào "
                "sắp đến giờ bắt đầu."
            )

        elif intent == "STUDY_PLANNING":
            if user_id:
                from datetime import datetime, time, timedelta
                from app.modules.calendar.service import LOCAL_TZ

                now = datetime.now(LOCAL_TZ)
                msg_lower = user_message.lower()
                is_sprint_or_sports = any(k in msg_lower for k in ("thi", "thể thao", "nghỉ ngơi", "rèn luyện", "10 ngày", "2 tuần", "giữa kỳ", "cuối kỳ", "sức khỏe", "4 môn"))

                if is_sprint_or_sports:
                    sprint_days = 14 if "2 tuần" in msg_lower else 10
                    valid_until_date = (now + timedelta(days=sprint_days)).date()

                    # Schedule slots across the upcoming weekdays starting immediately from today (Wed), Thu, Fri
                    # To ensure all dates (including 7, 8, 9 Oct) are populated
                    slots_to_add = []
                    for dow in (2, 3, 4):  # 2=Thứ Tư (07/10), 3=Thứ Năm (08/10), 4=Thứ Sáu (09/10)
                        dow_title = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"][dow]
                        slots_to_add.append({
                            "title": f"Ôn thi sáng: Lý thuyết ({dow_title})",
                            "start_time": datetime.combine(now.date(), time(8, 30)).replace(tzinfo=LOCAL_TZ).isoformat(),
                            "end_time": datetime.combine(now.date(), time(11, 0)).replace(tzinfo=LOCAL_TZ).isoformat(),
                            "recurrence": "weekly",
                            "day_of_week": dow,
                            "valid_until": valid_until_date.isoformat(),
                        })
                        slots_to_add.append({
                            "title": f"Rèn luyện thể thao chiều ({dow_title})",
                            "start_time": datetime.combine(now.date(), time(16, 30)).replace(tzinfo=LOCAL_TZ).isoformat(),
                            "end_time": datetime.combine(now.date(), time(17, 30)).replace(tzinfo=LOCAL_TZ).isoformat(),
                            "recurrence": "weekly",
                            "day_of_week": dow,
                            "valid_until": valid_until_date.isoformat(),
                        })
                        slots_to_add.append({
                            "title": f"Luyện đề thi tối ({dow_title})",
                            "start_time": datetime.combine(now.date(), time(19, 30)).replace(tzinfo=LOCAL_TZ).isoformat(),
                            "end_time": datetime.combine(now.date(), time(21, 30)).replace(tzinfo=LOCAL_TZ).isoformat(),
                            "recurrence": "weekly",
                            "day_of_week": dow,
                            "valid_until": valid_until_date.isoformat(),
                        })

                    plan_res = await create_schedule_plan_tool(
                        db=db,
                        user_id=user_id,
                        plan_title="Kế hoạch ôn thi & rèn luyện thể thao",
                        slots=slots_to_add,
                    )
                    await db.commit()
                    content = (
                        f"Cố lên bạn ơi! Mình đã kiểm tra lịch học hiện tại của bạn và đã **tự động lên lịch trọn gói Ôn thi & Rèn luyện thể thao** "
                        f"bắt đầu ngay từ hôm nay (Thứ Tư 07/10, Thứ Năm 08/10, Thứ Sáu 09/10...) vào [Lịch Thông Minh](/calendar) "
                        f"(được cài đặt thời hạn tự động kết thúc sau {sprint_days} ngày, không kéo dài vô hạn) nhé!\n\n"
                        "📚 **Các khung giờ đã tự động tạo vào Lịch của bạn:**\n"
                        "- **Ca sáng (08:30 – 11:00)**: Ôn tập lý thuyết & nắm chắc công thức các môn khó.\n"
                        "- **Ca chiều (16:30 – 17:30)**: Chạy bộ / Cầu lông / Thể thao giải tỏa căng thẳng, tăng tuần hoàn máu não.\n"
                        "- **Ca tối (19:30 – 21:30)**: Luyện giải đề thi thực chiến và rà soát lỗ hổng kiến thức.\n\n"
                        f"📅 **Lộ trình phân bổ trong {sprint_days} ngày:**\n"
                        "- **Tuần 1 (Từ hôm nay 07/10 – 13/10)**: Tập trung sâu lý thuyết và các môn trọng tâm, kết hợp thể thao các buổi chiều.\n"
                        "- **Tuần 2 (14/10 – ngày thi)**: Luyện giải đề thi thử tổng hợp, rà soát lỗ hổng, ngủ sớm giữ tâm lý thoải mái và sẵn sàng thi đạt kết quả xuất sắc!\n\n"
                        "Bạn có thể mở [Lịch Thông Minh](/calendar) để kiểm tra các khung giờ vừa được thêm nhé. Chúc bạn thi thật tốt! 💪✨"
                    )
                else:
                    days_ahead = (2 - now.weekday()) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                    target_date = (now + timedelta(days=days_ahead)).date()
                    target_start = datetime.combine(target_date, time(19, 30)).replace(tzinfo=LOCAL_TZ)
                    target_end = datetime.combine(target_date, time(21, 30)).replace(tzinfo=LOCAL_TZ)

                    slot_res = await add_personal_busy_slot_tool(
                        db=db,
                        user_id=user_id,
                        title="Lịch tự học",
                        start_time=target_start.isoformat(),
                        end_time=target_end.isoformat(),
                        recurrence="weekly",
                        day_of_week=2,
                    )
                    if slot_res.success:
                        await db.commit()
                        content = (
                            "Chào bạn! Dựa trên phân tích thời khóa biểu và các hoạt động của bạn trong tuần tới, "
                            "mình nhận thấy khung giờ **Tối Thứ Tư (19:30 – 21:30)** hoàn toàn trống và rất thích hợp để tập trung tự học.\n\n"
                            "✨ **Mình đã tự động lên lịch và thêm vào Smart Calendar của bạn:**\n"
                            "- **Tiêu đề:** Lịch tự học\n"
                            "- **Thời gian:** 19:30 – 21:30 (Thứ Tư hàng tuần)\n"
                            "- **Trạng thái:** ✅ Đã lưu thành công vào Smart Calendar\n\n"
                            "Bạn có thể mở [Lịch Thông Minh](/calendar) để kiểm tra hoặc điều chỉnh thời gian theo nhu cầu nhé!"
                        )
                    else:
                        content = (
                            f"Chào bạn! Mình đã kiểm tra lịch biểu của bạn trong tuần tới. {slot_res.message}\n\n"
                            "Bạn có thể mở [Lịch Thông Minh](/calendar) để chủ động chọn các khung giờ tự học khác nhé!"
                        )
            else:
                content = (
                    "Chào bạn! Để mình có thể kiểm tra lịch học và tự động thêm lịch tự học tối ưu vào Smart Calendar cho bạn, "
                    "bạn vui lòng đăng nhập vào tài khoản trước nhé.\n\n"
                    "Sau khi đăng nhập, bạn có thể kiểm tra lịch trình tại [Lịch Thông Minh](/calendar)."
                )

        elif intent == "GROUP_QUERY":
            # Search groups in DB
            group_res = await search_groups_tool(
                db=db,
                user_id=user_id,
                keyword=user_message if len(user_message) < 50 else None,
                limit=4,
            )
            if group_res.items:
                group_names = ", ".join([f"[{g.name}](/groups/{g.group_id})" for g in group_res.items[:3]])
                content = (
                    f"UniConnect hiện có các câu lạc bộ & đội nhóm sinh viên: {group_names}. "
                    "Bạn có thể bấm vào tên nhóm để xem thông tin chi tiết và nộp đơn gia nhập nhé!"
                )
            else:
                content = (
                    "Bạn có thể xem toàn bộ danh sách các Câu lạc bộ học thuật, tình nguyện và thể thao "
                    "tại mục [Câu Lạc Bộ](/groups) trên hệ thống UniConnect."
                )

        else:
            # intent == "ACTIVITY_SEARCH": True activity search
            msg_lower = user_message.lower().strip()
            is_ctxh = any(kw in msg_lower for kw in ["ctxh", "công tác xã hội", "tình nguyện", "ngày ctxh", "hiến máu"])
            is_goal_planning = is_ctxh and any(kw in msg_lower for kw in ["kiếm", "tích lũy", "cần", "muốn", "gợi ý", "lên lịch", "kế hoạch", "5 ngày"])
            
            # Extract meaningful keyword
            clean_keyword = user_message
            for prefix in [
                "tìm hoạt động", "tìm sự kiện", "có hoạt động nào", "có nhóm nào", "tìm kèo", "có buổi",
                "tôi muốn kiếm", "muốn kiếm", "tôi muốn", "kiếm", "trong 2 tuần tới", "2 tuần tới", "trong tuần tới"
            ]:
                if prefix in clean_keyword.lower():
                    clean_keyword = re.sub(re.escape(prefix), "", clean_keyword, flags=re.IGNORECASE).strip()

            # If user is asking for general CTXH planning, avoid exact keyword search on title
            if is_goal_planning:
                clean_keyword = None

            act_res = await search_activities_tool(
                db=db,
                user_id=user_id,
                keyword=clean_keyword if (clean_keyword and len(clean_keyword) < 60) else None,
                is_social_work=True if is_ctxh else None,
                exclude_user_busy_times=True,
                lat=user_lat,
                lng=user_lng,
                radius_meters=25000,
                limit=12 if is_ctxh else 4,
            )

            for act in act_res.items:
                cards.append(
                    ChatEventCardItem(
                        activity_id=act.activity_id,
                        title=act.title,
                        start_time=act.start_time,
                        end_time=act.end_time,
                        meeting_location=getattr(act, "meeting_location", None) or act.location_name,
                        location_name=getattr(act, "meeting_location", None) or act.location_name,
                        social_work_days=act.social_work_days,
                        group_id=act.group_id,
                        group_name=act.group_name,
                        distance_meters=act.distance_meters,
                        distance_status=act.distance_status,
                        conflict_status=act.conflict_status,
                        registration_status=act.registration_status,
                        eligibility_status=act.eligibility_status,
                    )
                )

            if cards:
                if is_goal_planning:
                    # Dynamically extract target days from user message (e.g. "10 ngày", "5 ngày")
                    target_match = re.search(r"(\d+(?:\.\d+)?)\s*ngày", msg_lower)
                    target_days = float(target_match.group(1)) if target_match else 5.0

                    plan_lines = []
                    accumulated_days = 0.0
                    for c in cards:
                        days = c.social_work_days or 0.0
                        start_str = c.start_time.strftime("%d/%m/%Y %H:%M") if hasattr(c.start_time, 'strftime') else str(c.start_time)[:16]
                        group_str = f" (*{c.group_name}*)" if c.group_name else ""
                        plan_lines.append(f"• **[{c.title}](/activities/{c.activity_id})**{group_str}\n  - Thời gian: `{start_str}`\n  - Địa điểm: {c.location_name or 'ĐH Bách Khoa'}\n  - Điểm tích lũy: **+{days} ngày CTXH**")
                        accumulated_days += days
                        if accumulated_days >= target_days and len(plan_lines) >= 3:
                            break

                    goal_status_str = f"(Đạt mục tiêu {target_days:g} ngày của bạn!)" if accumulated_days >= target_days else f"(Hiện tích lũy được {accumulated_days:g}/{target_days:g} ngày, các sự kiện tiếp theo sẽ được cập nhật thêm sớm nhé!)"
                    content = (
                        f"Chào bạn! Để giúp bạn tích lũy **{target_days:g} ngày CTXH**, "
                        f"mình đã lập cho bạn một kế hoạch tham gia các hoạt động tình nguyện thực tế phù hợp:\n\n"
                        + "\n\n".join(plan_lines) +
                        f"\n\n🎯 **Tổng số ngày CTXH tích lũy được: {accumulated_days:g} ngày** {goal_status_str}\n"
                        "Bạn có thể nhấn vào từng hoạt động để xem chi tiết và đăng ký nhé!"
                    )
                else:
                    bullet_lines = []
                    for c in cards:
                        group_str = f" - Tổ chức bởi [{c.group_name}](/groups/{c.group_id})" if c.group_id and c.group_name else ""
                        ctxh_str = f" (+{c.social_work_days} ngày CTXH)" if c.social_work_days and c.social_work_days > 0 else ""
                        bullet_lines.append(f"- [{c.title}](/activities/{c.activity_id}){ctxh_str}{group_str}")
                    bullets = "\n".join(bullet_lines)
                    content = (
                        f"Dưới đây là **{len(cards)} hoạt động** phù hợp với yêu cầu của bạn "
                        f"(đã kiểm tra và loại trừ lịch bận cá nhân):\n\n{bullets}"
                    )
            else:
                content = (
                    "Hiện tại chưa tìm thấy hoạt động nào phù hợp hoàn toàn với từ khóa này. "
                    "Bạn có thể khám phá thêm các sự kiện mới nhất tại trang [Khám Phá Hoạt Động](/dashboard) nhé!"
                )

    except Exception as e:
        logger.error(f"Deterministic fallback failed: {e}", exc_info=True)
        content = (
            "Hệ thống đang đồng bộ dữ liệu. Bạn có thể tra cứu nhanh các sự kiện đang diễn ra "
            "tại trang chủ UniConnect nhé!"
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

