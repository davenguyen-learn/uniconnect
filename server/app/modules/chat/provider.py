from datetime import datetime
from google.genai import types
from app.core.config import settings
from app.modules.calendar.service import LOCAL_TZ

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
                        "description": "Số lượng tối đa trả về. Mặc định 8 (hoặc 10 nếu người dùng cần tích lũy nhiều ngày CTXH).",
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
        {
            "name": "add_personal_busy_slot",
            "description": (
                "Tạo và thêm một khung giờ bận cá nhân hoặc lịch tự học vào Smart Calendar của sinh viên. "
                "Gọi công cụ này khi sinh viên yêu cầu xếp lịch tự học, lên lịch học cá nhân hoặc tự động lưu khung giờ học tập vào lịch."
            ),
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "title": {
                        "type": "STRING",
                        "description": "Tiêu đề của lịch bận / lịch tự học (ví dụ: 'Lịch tự học', 'Tự học Lập trình Web', 'Ôn thi Giải tích').",
                    },
                    "start_time": {
                        "type": "STRING",
                        "description": "Thời gian bắt đầu định dạng ISO 8601 (ví dụ: '2026-10-08T08:30:00+07:00').",
                    },
                    "end_time": {
                        "type": "STRING",
                        "description": "Thời gian kết thúc định dạng ISO 8601 (ví dụ: '2026-10-08T11:00:00+07:00').",
                    },
                    "recurrence": {
                        "type": "STRING",
                        "description": "Loại lặp lại: 'none' (diễn ra 1 lần) hoặc 'weekly' (lặp lại hàng tuần). Mặc định 'none'.",
                    },
                    "day_of_week": {
                        "type": "INTEGER",
                        "description": "Thứ trong tuần nếu lặp lại hàng tuần (0=Thứ 2, 1=Thứ 3, 2=Thứ 4, 3=Thứ 5, 4=Thứ 6, 5=Thứ 7, 6=Chủ nhật).",
                    },
                    "valid_until": {
                        "type": "STRING",
                        "description": "Ngày hết hạn (YYYY-MM-DD), ví dụ ngày kết thúc kỳ thi sau 10 ngày để lịch không bị lặp tuần vĩnh viễn.",
                    },
                },
            },
        },
        {
            "name": "create_schedule_plan",
            "description": (
                "Lên kế hoạch và tự động tạo đồng thời nhiều khung giờ học tập, rèn luyện thể thao và nghỉ ngơi vào Smart Calendar "
                "cho sinh viên (ví dụ: kế hoạch ôn thi nước rút trong 10 ngày, lịch rèn luyện thể thao và tự học kết hợp). "
                "Gọi công cụ này khi sinh viên yêu cầu sắp xếp thời gian ôn thi, thời khóa biểu tự học kết hợp thể thao/nghỉ ngơi."
            ),
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "plan_title": {
                        "type": "STRING",
                        "description": "Tên kế hoạch tổng thể (ví dụ: 'Kế hoạch ôn thi 10 ngày & rèn luyện thể thao').",
                    },
                    "slots": {
                        "type": "ARRAY",
                        "description": "Danh sách các khung giờ cụ thể cần thêm vào lịch.",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "title": {
                                    "type": "STRING",
                                    "description": "Tiêu đề của khung giờ (ví dụ: 'Ôn thi sáng: Môn 1 & 2', 'Tập thể thao & chạy bộ chiều', 'Luyện đề thi tối').",
                                },
                                "start_time": {
                                    "type": "STRING",
                                    "description": "Thời gian bắt đầu định dạng ISO 8601 (ví dụ: '2026-10-08T08:30:00+07:00'). Bắt đầu ngay từ hôm nay/ngày mai trong thời gian ôn thi.",
                                },
                                "end_time": {
                                    "type": "STRING",
                                    "description": "Thời gian kết thúc định dạng ISO 8601 (ví dụ: '2026-10-08T11:00:00+07:00').",
                                },
                                "recurrence": {
                                    "type": "STRING",
                                    "description": "'weekly' (lặp hàng tuần cho kế hoạch ôn thi/thói quen nhiều ngày) hoặc 'none' (sự kiện 1 lần duy nhất vào ngày cụ thể).",
                                },
                                "day_of_week": {
                                    "type": "INTEGER",
                                    "description": "Thứ trong tuần (0=Thứ 2, ..., 6=Chủ nhật) khi recurrence='weekly'.",
                                },
                                "valid_until": {
                                    "type": "STRING",
                                    "description": "Ngày kết thúc kế hoạch (YYYY-MM-DD). CHỈ DÙNG khi recurrence='weekly' (ví dụ ngày thi sau 10 ngày hay 2 tuần để chu kỳ lặp tự động dừng đúng hạn). TUYỆT ĐỐI KHÔNG dùng cho sự kiện 1 lần 'none'.",
                                },
                            },
                            "required": ["title", "start_time", "end_time"],
                        },
                    },
                },
                "required": ["plan_title", "slots"],
            },
        },
    ]
}

SYSTEM_INSTRUCTION_BASE = (
    "Bạn là Trợ lý AI UniConnect thông minh, năng động và thân thiện của sinh viên đại học. "
    "Mục tiêu của bạn là giúp sinh viên khám phá sự kiện ngoại khóa, tích lũy ngày CTXH và quản lý thời gian hiệu quả.\n"
    "QUY TẮC BẮT BUỘC:\n"
    "1. Khi người dùng hỏi về hoạt động hoặc sự kiện, LUÔN gọi công cụ 'search_activities' để lấy dữ liệu thực tế.\n"
    "2. Khi người dùng đặt mục tiêu tích lũy số ngày CTXH (ví dụ: 'tôi muốn kiếm 10 ngày CTXH trong 1 tháng tới'):\n"
    "   - LUÔN gọi 'search_activities' với is_social_work=True, limit=12 để nhận danh sách đầy đủ các hoạt động tình nguyện sắp tới.\n"
    "   - Lập một lộ trình/kế hoạch tham gia CHỈ TỪ CÁC HOẠT ĐỘNG THẬT TRONG KẾT QUẢ CÔNG CỤ.\n"
    "   - Nếu các hoạt động thật đạt hoặc vượt mục tiêu: chọn lọc các hoạt động phù hợp nhất để đạt mục tiêu.\n"
    "   - NẾU CÁC HOẠT ĐỘNG THẬT CHƯA ĐỦ SỐ NGÀY MỤC TIÊU: Hãy trình bày TẤT CẢ các hoạt động thật hiện có, tính chính xác tổng số ngày tích lũy được hiện tại, và giải thích rõ ràng với sinh viên rằng số ngày còn lại sẽ được bổ sung khi các CLB/Khoa mở thêm sự kiện mới. TUYỆT ĐỐI KHÔNG TỰ BỊA HOẠT ĐỘNG HAY NGÀY THÁNG ĐỂ ÉP ĐỦ MỤC TIÊU.\n"
    "   - Trình bày rõ ràng từng hoạt động: Ngày giờ, [Tên hoạt động](/activities/{id}), địa điểm, số ngày CTXH đạt được (+0.5 hoặc +1.0 ngày).\n"
    "   - Tổng kết: 'Tổng số ngày CTXH tích lũy được: X ngày (mục tiêu Y ngày)' và kèm lời động viên hào hứng.\n"
    "3. Khi người dùng hỏi về thời gian rảnh hoặc lịch bận, LUÔN gọi 'get_user_schedule'.\n"
    "4. Khi người dùng hỏi về CLB hoặc đội nhóm, LUÔN gọi 'search_groups'.\n"
    "5. BẮT BUỘC KÈM ĐƯỜNG DẪN (LINK) CHI TIẾT TRONG NỘI DUNG:\n"
    "   - Mỗi khi nhắc đến một hoạt động/sự kiện, bạn PHẢI chèn link markdown relative: [Tên hoạt động](/activities/{activity_id}).\n"
    "   - TUYỆT ĐỐI KHÔNG thêm tiền tố domain như 'http://localhost:5173', chỉ dùng đường dẫn relative bắt đầu bằng '/activities/'.\n"
    "   - Nếu hoạt động do một CLB/nhóm tổ chức (có group_id và group_name), chèn link: [Tên CLB](/groups/{group_id}).\n"
    "   - Khi trả lời về CLB từ 'search_groups', chèn link: [Tên CLB](/groups/{group_id}).\n"
    "   - Khi nhắc đến Lịch biểu cá nhân, chèn link: [Lịch Thông Minh](/calendar).\n"
    "   - Dùng chính xác activity_id và group_id thực tế từ kết quả công cụ. TUYỆT ĐỐI KHÔNG TỰ BỊA RA MÃ UUID MỚI.\n"
    "6. Phản hồi bằng tiếng Việt chuẩn mực, hào hứng, súc tích. Nhấn mạnh số ngày CTXH (nếu có) và trạng thái phù hợp với lịch của sinh viên.\n"
    "7. NGUYÊN TẮC BẢO TOÀN DỮ LIỆU (GROUNDING):\n"
    "   - Tuyệt đối không tự suy đoán ngày CTXH hay bịa đặt sự kiện không có trong kết quả trả về từ công cụ.\n"
    "   - Thời gian của hoạt động phải lấy đúng từ kết quả công cụ (năm hiện tại trong hệ thống là 2026), tuyệt đối không tự bịa năm 2023 hay ngày tháng giả mạo.\n"
    "8. KỊCH BẢN TỰ ĐỘNG XẾP VÀ TẠO LỊCH TỰ HỌC & RÈN LUYỆN THỂ THAO (ACTIONABLE AI AGENT):\n"
    "   - Khi sinh viên hỏi: '10 ngày nữa thi / 2 tuần nữa thi giữa kỳ, sắp xếp thời gian học tập, nghỉ ngơi, thể thao...' hoặc yêu cầu lập kế hoạch/thời khóa biểu:\n"
    "     * Bước 1: Gọi 'get_user_schedule' với days_ahead=14 để kiểm tra lịch bận/học tập hiện tại.\n"
    "     * Bước 2: Dựa vào yêu cầu sinh viên, phân bổ các khung giờ học tập, thể thao và nghỉ ngơi khoa học bắt đầu NGAY từ hôm nay/ngày mai (năm 2026).\n"
    "     * Bước 3: Gọi 'create_schedule_plan' để TỰ ĐỘNG TẠO TẤT CẢ các khung giờ thật vào Smart Calendar:\n"
    "       - Với kế hoạch xuyên suốt giai đoạn (10 ngày, 2 tuần ôn thi): Tạo các slot lặp hàng tuần (recurrence='weekly') phủ đều các ngày trong tuần (ví dụ: các ngày từ hôm nay Thứ 4 [day_of_week=2], Thứ 5 [day_of_week=3], Thứ 6 [day_of_week=4]...), kèm 'valid_until' là ngày thi kết thúc. Nhờ vậy các buổi học và thể thao sẽ phủ kín ngay từ tuần này (ngày 7, 8, 9 tháng 10...) đến hết kỳ thi và tự động kết thúc đúng hạn.\n"
    "       - Cả các ca học tập (ví dụ: Ôn thi sáng 08:30 - 11:00, Luyện đề tối 19:30 - 21:30).\n"
    "       - Cả các ca rèn luyện thể thao / giải tỏa căng thẳng (ví dụ: Chiều 16:30 - 17:30).\n"
    "       - TUYỆT ĐỐI KHÔNG tạo slot recurrence='none' (1 lần) rồi gán valid_until, và KHÔNG chỉ tạo 1 buổi lẻ loi duy nhất cho cả đợt ôn thi 2 tuần.\n"
    "     * Bước 4: Trả lời sinh viên: trình bày chi tiết kế hoạch các môn, thể thao và nghỉ ngơi, xác nhận rõ các khung giờ đã được lưu vào [Lịch Thông Minh](/calendar).\n"
)


def get_system_instruction() -> str:
    """Generate dynamic system instruction injected with current system date & time."""
    now = datetime.now(LOCAL_TZ)
    dow_names = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
    dow_str = dow_names[now.weekday()]
    date_str = now.strftime("%d/%m/%Y")
    time_str = now.strftime("%H:%M")
    iso_date = now.date().isoformat()

    header = (
        f"THỜI GIAN HIỆN TẠI TRONG HỆ THỐNG: {dow_str}, ngày {date_str} (ISO: {iso_date}), lúc {time_str} (Giờ Việt Nam UTC+7).\n"
        f"HÔM NAY CHÍNH LÀ {dow_str} NGÀY {date_str}. Mọi kế hoạch ôn thi (10 ngày tới, 2 tuần tới...) BẮT BUỘC PHẢI BẮT ĐẦU NGAY TỪ HÔM NAY ({date_str}) và các ngày tiếp theo trong tuần này ({dow_str}, ngày mai, ngày kia...). "
        f"TUYỆT ĐỐI KHÔNG bỏ trống các ngày 7, 8, 9 tháng 10 này và không được nhảy sang tuần sau!\n\n"
    )
    return header + SYSTEM_INSTRUCTION_BASE


SYSTEM_INSTRUCTION = SYSTEM_INSTRUCTION_BASE


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
