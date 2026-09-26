"""Gemini AI Provider Adapter with Function Calling Declarations."""

from google.genai import types
from app.core.config import settings

# Function declarations schema for Gemini
CHAT_TOOLS = {
    "function_declarations": [
        {
            "name": "search_activities",
            "description": (
                "Tìm kiếm các hoạt động, sự kiện phù hợp cho sinh viên đại học. "
                "Gọi công cụ này khi sinh viên hỏi tìm kiếm sự kiện, hoạt động tình nguyện, thể thao, học tập, "
                "công tác xã hội (CTXH) hoặc hỏi về hoạt động cuối tuần."
            ),
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "keyword": {
                        "type": "STRING",
                        "description": "Từ khóa tìm kiếm trong tiêu đề hoặc nội dung hoạt động.",
                    },
                    "category": {
                        "type": "STRING",
                        "description": "Thể loại hoạt động (Study, Sports, Social, Gaming, Music, Volunteer).",
                    },
                    "is_social_work": {
                        "type": "BOOLEAN",
                        "description": "True nếu người dùng tìm hoạt động cấp ngày Công tác xã hội (CTXH) hoặc tình nguyện.",
                    },
                    "exclude_user_busy_times": {
                        "type": "BOOLEAN",
                        "description": "True để tự động loại trừ các hoạt động trùng với lịch bận cá nhân của sinh viên. Mặc định là True.",
                    },
                    "radius_meters": {
                        "type": "INTEGER",
                        "description": "Bán kính tìm kiếm tính bằng mét. Mặc định 25000 (25km).",
                    },
                    "limit": {
                        "type": "INTEGER",
                        "description": "Số lượng tối đa trả về. Mặc định 4.",
                    },
                },
            },
        },
        {
            "name": "get_user_schedule",
            "description": (
                "Tra cứu các khung giờ bận cá nhân và hoạt động đã đăng ký của sinh viên trong các ngày sắp tới. "
                "Gọi công cụ này khi sinh viên hỏi về thời gian rảnh, kiểm tra lịch học/lịch thi hay muốn biết thứ mấy rảnh."
            ),
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "days_ahead": {
                        "type": "INTEGER",
                        "description": "Số ngày sắp tới cần kiểm tra lịch (mặc định 7 ngày).",
                    }
                },
            },
        },
        {
            "name": "search_groups",
            "description": (
                "Tìm kiếm các câu lạc bộ (CLB), đội nhóm sinh viên theo tên hoặc sở thích. "
                "Gọi công cụ này khi sinh viên hỏi về CLB công nghệ, tình nguyện, văn nghệ hoặc CLB đang tuyển quân."
            ),
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "keyword": {
                        "type": "STRING",
                        "description": "Tên hoặc lĩnh vực câu lạc bộ cần tìm.",
                    },
                    "limit": {
                        "type": "INTEGER",
                        "description": "Số lượng tối đa trả về. Mặc định 4.",
                    },
                },
            },
        },
    ]
}

SYSTEM_INSTRUCTION = (
    "Bạn là Trợ lý AI UniConnect thông minh, năng động và thân thiện của sinh viên đại học. "
    "Mục tiêu của bạn là giúp sinh viên khám phá sự kiện ngoại khóa, tích lũy ngày CTXH và quản lý thời gian hiệu quả.\n"
    "QUY TẮC BẮT BUỘC:\n"
    "1. Khi người dùng hỏi về hoạt động hoặc sự kiện, LUÔN gọi công cụ 'search_activities' để lấy dữ liệu thực tế.\n"
    "2. Khi người dùng hỏi về thời gian rảnh hoặc lịch bận, LUÔN gọi 'get_user_schedule'.\n"
    "3. Khi người dùng hỏi về CLB hoặc đội nhóm, LUÔN gọi 'search_groups'.\n"
    "4. BẮT BUỘC KÈM ĐƯỜNG DẪN (LINK) CHI TIẾT TRONG NỘI DUNG:\n"
    "   - Mỗi khi nhắc đến một hoạt động/sự kiện, bạn PHẢI chèn link markdown: [Tên hoạt động](/activities/{activity_id}).\n"
    "   - Nếu hoạt động do một CLB/nhóm tổ chức (có group_id và group_name), bạn hãy chèn kèm link của nhóm: [Tên CLB](/groups/{group_id}).\n"
    "   - Khi trả lời về CLB từ 'search_groups', PHẢI chèn link markdown: [Tên CLB](/groups/{group_id}).\n"
    "   - Dùng chính xác activity_id và group_id thực tế từ kết quả công cụ (không tự bịa ID).\n"
    "5. Phản hồi bằng tiếng Việt chuẩn mực, hào hứng, súc tích. Nhấn mạnh số ngày CTXH (nếu có) và trạng thái phù hợp với lịch của sinh viên.\n"
    "6. Tuyệt đối không tự suy đoán ngày CTXH hay bịa đặt sự kiện không có trong kết quả trả về từ công cụ."
)


def get_model_candidates() -> list[str]:
    """Get list of configured Gemini models starting with primary model."""
    candidates = []
    if settings.GEMINI_PRIMARY_MODEL:
        candidates.append(settings.GEMINI_PRIMARY_MODEL.strip())
    
    if settings.GEMINI_FALLBACK_MODELS:
        for m in settings.GEMINI_FALLBACK_MODELS.split(","):
            m_clean = m.strip()
            if m_clean and m_clean not in candidates:
                candidates.append(m_clean)
                
    if not candidates:
        candidates = ["gemini-3.5-flash-lite", "gemini-2.5-flash"]
        
    return candidates
