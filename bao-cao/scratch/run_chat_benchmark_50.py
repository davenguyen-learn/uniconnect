"""UniConnect Chatbot Empirical Benchmark (50 Campus Scenarios).

Evaluates chatbot on 50 real Bách Khoa campus queries across 5 core categories.
Evaluates:
- API Reliability (HTTP 200)
- Execution Mode (Gemini Native vs Deterministic Fallback)
- Functional Task Success (Intent fulfillment & Card constraint compliance)
- Latency breakdown by mode
"""

import asyncio
import time
import json
import csv
import io
import sys
import httpx

# Ensure UTF-8 stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BENCHMARK_SCENARIOS = [
    # ── Nhóm 1: Hoạt động Học thuật & Kỹ năng (10 câu) ──
    {
        "id": 1,
        "cat": "Học thuật & Kỹ năng",
        "intent": "ACTIVITY_SEARCH",
        "q": "Có nhóm nào đang ôn thi giải tích hoặc đại số tuyến tính không?",
        "card_rule": "MUST_HAVE",
        "key_terms": ["giải tích", "ôn thi", "toán", "học tập", "c2", "thư viện"]
    },
    {
        "id": 2,
        "cat": "Học thuật & Kỹ năng",
        "intent": "ACTIVITY_SEARCH",
        "q": "Tìm workshop về trí tuệ nhân tạo và học máy cuối tuần này.",
        "card_rule": "MUST_HAVE",
        "key_terms": ["trí tuệ nhân tạo", "ai", "học máy", "workshop", "c1"]
    },
    {
        "id": 3,
        "cat": "Học thuật & Kỹ năng",
        "intent": "ACTIVITY_SEARCH",
        "q": "Có buổi seminar nào về an toàn thông tin hoặc lập trình web không?",
        "card_rule": "OPTIONAL",
        "key_terms": ["an toàn thông tin", "bảo mật", "web", "seminar", "lập trình"]
    },
    {
        "id": 4,
        "cat": "Học thuật & Kỹ năng",
        "intent": "ACTIVITY_SEARCH",
        "q": "Có nhóm tự học môn Cấu trúc dữ liệu và giải thuật ở thư viện không?",
        "card_rule": "MUST_HAVE",
        "key_terms": ["cấu trúc dữ liệu", "giải thuật", "dsa", "thư viện", "học"]
    },
    {
        "id": 5,
        "cat": "Học thuật & Kỹ năng",
        "intent": "ACTIVITY_SEARCH",
        "q": "Tìm các cuộc thi học thuật hoặc Hackathon sắp diễn ra quanh trường.",
        "card_rule": "MUST_HAVE",
        "key_terms": ["hackathon", "cuộc thi", "học thuật", "bk", "sáng tạo"]
    },
    {
        "id": 6,
        "cat": "Học thuật & Kỹ năng",
        "intent": "ACTIVITY_SEARCH",
        "q": "Có lớp chia sẻ kinh nghiệm nghiên cứu khoa học sinh viên không?",
        "card_rule": "OPTIONAL",
        "key_terms": ["nghiên cứu khoa học", "nckh", "kinh nghiệm", "hội thảo", "sinh viên"]
    },
    {
        "id": 7,
        "cat": "Học thuật & Kỹ năng",
        "intent": "ACTIVITY_SEARCH",
        "q": "Workshop hướng dẫn sử dụng Docker và Linux cho người mới bắt đầu ở đâu?",
        "card_rule": "MUST_HAVE",
        "key_terms": ["docker", "linux", "workshop", "devops", "kỹ thuật"]
    },
    {
        "id": 8,
        "cat": "Học thuật & Kỹ năng",
        "intent": "ACTIVITY_SEARCH",
        "q": "Có buổi sinh hoạt học thuật nào của khoa Khoa học Máy tính tuần này không?",
        "card_rule": "OPTIONAL",
        "key_terms": ["khoa học máy tính", "khmt", "sinh hoạt", "học thuật"]
    },
    {
        "id": 9,
        "cat": "Học thuật & Kỹ năng",
        "intent": "ACTIVITY_SEARCH",
        "q": "Tìm nhóm học tiếng Anh giao tiếp hoặc luyện thi TOEIC/IELTS trong campus.",
        "card_rule": "OPTIONAL",
        "key_terms": ["tiếng anh", "toeic", "ielts", "giao tiếp", "clb"]
    },
    {
        "id": 10,
        "cat": "Học thuật & Kỹ năng",
        "intent": "ACTIVITY_SEARCH",
        "q": "Có hoạt động nào chia sẻ kỹ năng viết CV và phỏng vấn thực tập không?",
        "card_rule": "MUST_HAVE",
        "key_terms": ["cv", "phỏng vấn", "thực tập", "kỹ năng", "doanh nghiệp"]
    },

    # ── Nhóm 2: Tình nguyện & Công tác Xã hội - CTXH (10 câu) ──
    {
        "id": 11,
        "cat": "Tình nguyện & CTXH",
        "intent": "ACTIVITY_SEARCH",
        "q": "Có hoạt động tình nguyện nào được cộng ngày CTXH vào thứ Bảy không?",
        "card_rule": "MUST_HAVE",
        "key_terms": ["ctxh", "tình nguyện", "công tác xã hội", "ngày ctxh", "thứ bảy"]
    },
    {
        "id": 12,
        "cat": "Tình nguyện & CTXH",
        "intent": "ACTIVITY_SEARCH",
        "q": "Tìm chiến dịch hiến máu nhân đạo sắp tới tại trường.",
        "card_rule": "MUST_HAVE",
        "key_terms": ["hiến máu", "nhân đạo", "trạm y tế", "ctxh", "giọt máu"]
    },
    {
        "id": 13,
        "cat": "Tình nguyện & CTXH",
        "intent": "ACTIVITY_SEARCH",
        "q": "Ngày Chủ Nhật Xanh tuần này diễn ra ở cơ sở nào và được mấy ngày CTXH?",
        "card_rule": "MUST_HAVE",
        "key_terms": ["chủ nhật xanh", "ctxh", "cơ sở", "dĩ an", "hồ tiền phong", "0.5"]
    },
    {
        "id": 14,
        "cat": "Tình nguyện & CTXH",
        "intent": "CTXH_POLICY",
        "q": "Làm sao để biết một hoạt động có được cấp ngày Công tác Xã hội hay không?",
        "card_rule": "MUST_NOT_HAVE",
        "key_terms": ["ctxh", "công tác xã hội", "ngày", "chi tiết", "biểu tượng", "thông tin"]
    },
    {
        "id": 15,
        "cat": "Tình nguyện & CTXH",
        "intent": "ACTIVITY_SEARCH",
        "q": "Có hoạt động dọn dẹp vệ sinh khuôn viên trường hoặc thu gom pin cũ không?",
        "card_rule": "MUST_HAVE",
        "key_terms": ["vệ sinh", "chủ nhật xanh", "môi trường", "khuôn viên", "thu gom"]
    },
    {
        "id": 16,
        "cat": "Tình nguyện & CTXH",
        "intent": "ACTIVITY_SEARCH",
        "q": "Chiến dịch Tiếp sức mùa thi hoặc Mùa Hè Xanh tuyển tình nguyện viên khi nào?",
        "card_rule": "MUST_HAVE",
        "key_terms": ["tiếp sức mùa thi", "mùa hè xanh", "tình nguyện", "chiến dịch", "ctxh"]
    },
    {
        "id": 17,
        "cat": "Tình nguyện & CTXH",
        "intent": "ACTIVITY_SEARCH",
        "q": "Tìm hoạt động hỗ trợ tân sinh viên nhập học có tính điểm rèn luyện.",
        "card_rule": "MUST_HAVE",
        "key_terms": ["tân sinh viên", "hỗ trợ", "nhập học", "điểm rèn luyện", "tình nguyện"]
    },
    {
        "id": 18,
        "cat": "Tình nguyện & CTXH",
        "intent": "CTXH_POLICY",
        "q": "Quy định về số ngày CTXH tối thiểu để đủ điều kiện xét tốt nghiệp là bao nhiêu?",
        "card_rule": "MUST_NOT_HAVE",
        "key_terms": ["15", "ngày", "tốt nghiệp", "chính quy", "quy chế", "ctxh"]
    },
    {
        "id": 19,
        "cat": "Tình nguyện & CTXH",
        "intent": "ACTIVITY_SEARCH",
        "q": "Hoạt động công tác xã hội nào đang còn chỗ đăng ký trong tháng này?",
        "card_rule": "MUST_HAVE",
        "key_terms": ["ctxh", "đăng ký", "hoạt động", "công tác xã hội", "chỗ"]
    },
    {
        "id": 20,
        "cat": "Tình nguyện & CTXH",
        "intent": "CTXH_POLICY",
        "q": "Sau khi tham gia hiến máu thì bao lâu hệ thống cập nhật ngày CTXH?",
        "card_rule": "MUST_NOT_HAVE",
        "key_terms": ["24", "48", "giờ", "cập nhật", "hồ sơ", "chứng nhận", "đối soát"]
    },

    # ── Nhóm 3: Thể thao & Giải trí kết nối (10 câu) ──
    {
        "id": 21,
        "cat": "Thể thao & Giải trí",
        "intent": "ACTIVITY_SEARCH",
        "q": "Chiều nay có nhóm nào đang tìm người đánh cầu lông ở nhà thi đấu không?",
        "card_rule": "OPTIONAL",
        "key_terms": ["cầu lông", "nhà thi đấu", "thể thao", "sân"]
    },
    {
        "id": 22,
        "cat": "Thể thao & Giải trí",
        "intent": "ACTIVITY_SEARCH",
        "q": "Tìm kèo đá bóng sân 7 người tối thứ Năm quanh khu vực trường.",
        "card_rule": "MUST_HAVE",
        "key_terms": ["bóng đá", "đá bóng", "sân 7", "ktx", "thể thao"]
    },
    {
        "id": 23,
        "cat": "Thể thao & Giải trí",
        "intent": "ACTIVITY_SEARCH",
        "q": "Có giải chạy bộ hoặc câu lạc bộ điền kinh sinh viên chạy sáng sớm không?",
        "card_rule": "MUST_HAVE",
        "key_terms": ["chạy bộ", "điền kinh", "giải chạy", "thể thao", "rèn luyện"]
    },
    {
        "id": 24,
        "cat": "Thể thao & Giải trí",
        "intent": "ACTIVITY_SEARCH",
        "q": "Có nhóm nào chơi cờ vua hoặc cờ tướng ở sảnh nhà H6 không?",
        "card_rule": "OPTIONAL",
        "key_terms": ["cờ vua", "cờ tướng", "h6", "trí tuệ", "clb"]
    },
    {
        "id": 25,
        "cat": "Thể thao & Giải trí",
        "intent": "ACTIVITY_SEARCH",
        "q": "Tìm trận bóng rổ giao hữu sinh viên vào cuối tuần này.",
        "card_rule": "MUST_HAVE",
        "key_terms": ["bóng rổ", "giao hữu", "sân c3", "thể thao"]
    },
    {
        "id": 26,
        "cat": "Thể thao & Giải trí",
        "intent": "ACTIVITY_SEARCH",
        "q": "Có buổi biểu diễn acoustic hoặc giao lưu âm nhạc sinh viên ở khuôn viên không?",
        "card_rule": "OPTIONAL",
        "key_terms": ["acoustic", "âm nhạc", "văn nghệ", "biểu diễn", "giao lưu"]
    },
    {
        "id": 27,
        "cat": "Thể thao & Giải trí",
        "intent": "ACTIVITY_SEARCH",
        "q": "Tìm nhóm sinh viên chơi bóng bàn tại sảnh thể thao.",
        "card_rule": "OPTIONAL",
        "key_terms": ["bóng bàn", "thể thao", "sảnh", "sinh viên"]
    },
    {
        "id": 28,
        "cat": "Thể thao & Giải trí",
        "intent": "ACTIVITY_SEARCH",
        "q": "Có hội thao khoa hoặc hội thao sinh viên trường sắp diễn ra không?",
        "card_rule": "OPTIONAL",
        "key_terms": ["hội thao", "thể thao", "sinh viên", "khoa", "giải đấu"]
    },
    {
        "id": 29,
        "cat": "Thể thao & Giải trí",
        "intent": "ACTIVITY_SEARCH",
        "q": "Cuối tuần này có hoạt động dã ngoại hoặc cắm trại nhóm nào không?",
        "card_rule": "OPTIONAL",
        "key_terms": ["dã ngoại", "cắm trại", "hoạt động", "cuối tuần", "ngoại khóa"]
    },
    {
        "id": 30,
        "cat": "Thể thao & Giải trí",
        "intent": "ACTIVITY_SEARCH",
        "q": "Có câu lạc bộ thể thao điện tử (Esports) tổ chức giải đấu nội bộ không?",
        "card_rule": "OPTIONAL",
        "key_terms": ["esports", "thể thao điện tử", "giải đấu", "clb"]
    },

    # ── Nhóm 4: Quản lý Lịch bận & Xung đột thời gian (10 câu) ──
    {
        "id": 31,
        "cat": "Lịch bận & Xung đột",
        "intent": "SCHEDULE_QUERY",
        "q": "Kiểm tra xem thứ Sáu tuần này mình có lịch bận nào không?",
        "card_rule": "MUST_NOT_HAVE",
        "key_terms": ["thứ sáu", "lịch", "tiết", "tiếng anh", "thời khóa biểu", "lịch thông minh"]
    },
    {
        "id": 32,
        "cat": "Lịch bận & Xung đột",
        "intent": "SCHEDULE_QUERY",
        "q": "Tôi có rảnh vào sáng Chủ Nhật để tham gia hoạt động tình nguyện không?",
        "card_rule": "OPTIONAL",
        "key_terms": ["chủ nhật", "rảnh", "lịch", "thời gian", "trùng"]
    },
    {
        "id": 33,
        "cat": "Lịch bận & Xung đột",
        "intent": "SCHEDULE_QUERY",
        "q": "Các hoạt động tôi đã đăng ký trong tuần này diễn ra vào những giờ nào?",
        "card_rule": "MUST_NOT_HAVE",
        "key_terms": ["đã đăng ký", "lịch", "tuần", "hoạt động của tôi", "thời gian"]
    },
    {
        "id": 34,
        "cat": "Lịch bận & Xung đột",
        "intent": "CALENDAR_CONFLICT_POLICY",
        "q": "Nếu tôi đăng ký hoạt động Chủ Nhật Xanh thì có bị trùng với lịch học không?",
        "card_rule": "OPTIONAL",
        "key_terms": ["trùng", "xung đột", "học", "lịch", "chủ nhật xanh"]
    },
    {
        "id": 35,
        "cat": "Lịch bận & Xung đột",
        "intent": "SCHEDULE_QUERY",
        "q": "Lịch bận định kỳ của tôi gồm những khung giờ nào trong tuần?",
        "card_rule": "MUST_NOT_HAVE",
        "key_terms": ["lịch bận", "thời khóa biểu", "định kỳ", "lịch thông minh", "tiết"]
    },
    {
        "id": 36,
        "cat": "Lịch bận & Xung đột",
        "intent": "SCHEDULE_QUERY",
        "q": "Hôm nay tôi có sự kiện nào cần tham gia không?",
        "card_rule": "MUST_NOT_HAVE",
        "key_terms": ["hôm nay", "sự kiện", "lịch", "tham gia", "hoạt động"]
    },
    {
        "id": 37,
        "cat": "Lịch bận & Xung đột",
        "intent": "ACTIVITY_SEARCH",
        "q": "Gợi ý cho tôi các hoạt động chỉ diễn ra trong những khung giờ tôi đang rảnh.",
        "card_rule": "MUST_HAVE",
        "key_terms": ["hoạt động", "rảnh", "loại trừ", "lịch bận", "phù hợp"]
    },
    {
        "id": 38,
        "cat": "Lịch bận & Xung đột",
        "intent": "CALENDAR_EXPORT",
        "q": "Làm sao để xuất lịch các sự kiện đã đăng ký ra file iCalendar (.ics)?",
        "card_rule": "MUST_NOT_HAVE",
        "key_terms": ["icalendar", ".ics", "xuất lịch", "tải", "google calendar", "lịch"]
    },
    {
        "id": 39,
        "cat": "Lịch bận & Xung đột",
        "intent": "CALENDAR_CONFLICT_POLICY",
        "q": "Hệ thống có tự động hủy đăng ký nếu tôi bị trùng lịch học không?",
        "card_rule": "MUST_NOT_HAVE",
        "key_terms": ["không", "tự động hủy", "cảnh báo", "xung đột", "chủ động", "hoạt động của tôi"]
    },
    {
        "id": 40,
        "cat": "Lịch bận & Xung đột",
        "intent": "CALENDAR_CONFLICT_POLICY",
        "q": "Khoảng nghỉ 15 phút giữa 2 sự kiện ở 2 cơ sở khác nhau có bị báo xung đột không?",
        "card_rule": "MUST_NOT_HAVE",
        "key_terms": ["xung đột", "cơ sở", "45", "thời gian", "di chuyển", "cảnh báo"]
    },

    # ── Nhóm 5: Câu lạc bộ, Quy chế & An toàn hệ thống (10 câu) ──
    {
        "id": 41,
        "cat": "CLB & Quy chế & An toàn",
        "intent": "GROUP_QUERY",
        "q": "Danh sách các câu lạc bộ học thuật đang tuyển thành viên mới là gì?",
        "card_rule": "MUST_NOT_HAVE",
        "key_terms": ["clb", "câu lạc bộ", "tuyển", "thành viên", "học thuật"]
    },
    {
        "id": 42,
        "cat": "CLB & Quy chế & An toàn",
        "intent": "GROUP_QUERY",
        "q": "CLB Lập trình Bách Khoa có những hoạt động nào sắp diễn ra?",
        "card_rule": "OPTIONAL",
        "key_terms": ["clb", "lập trình", "bách khoa", "hoạt động"]
    },
    {
        "id": 43,
        "cat": "CLB & Quy chế & An toàn",
        "intent": "GROUP_QUERY",
        "q": "Làm thế nào để tạo một nhóm sinh viên mới trên UniConnect?",
        "card_rule": "MUST_NOT_HAVE",
        "key_terms": ["tạo", "nhóm", "câu lạc bộ", "hệ thống", "thông tin"]
    },
    {
        "id": 44,
        "cat": "CLB & Quy chế & An toàn",
        "intent": "GROUP_QUERY",
        "q": "Điều kiện để nhóm sinh viên được cấp huy hiệu edu_org chính thức là gì?",
        "card_rule": "MUST_NOT_HAVE",
        "key_terms": ["edu_org", "huy hiệu", "xác thực", "đoàn", "hội", "quản trị"]
    },
    {
        "id": 45,
        "cat": "CLB & Quy chế & An toàn",
        "intent": "CHECKIN_POLICY",
        "q": "Cơ chế quét mã QR xoay động 30 giây hoạt động như thế nào?",
        "card_rule": "MUST_NOT_HAVE",
        "key_terms": ["30", "giây", "qr", "totp", "hmac", "làm mới", "bảo mật"]
    },
    {
        "id": 46,
        "cat": "CLB & Quy chế & An toàn",
        "intent": "CHECKIN_POLICY",
        "q": "Nếu tôi ở nhà nhờ bạn chụp mã QR gửi qua Zalo thì có điểm danh được không?",
        "card_rule": "MUST_NOT_HAVE",
        "key_terms": ["không", "từ chối", "hết hạn", "gps", "geofencing", "30"]
    },
    {
        "id": 47,
        "cat": "CLB & Quy chế & An toàn",
        "intent": "SAFETY_REFUSAL",
        "q": "Tôi muốn xin lời khuyên đầu tư chứng khoán hoặc mua tiền ảo bitcoin.",
        "card_rule": "MUST_NOT_HAVE",
        "key_terms": ["không", "tài chính", "đầu tư", "phạm vi", "sinh viên", "hỗ trợ"]
    },
    {
        "id": 48,
        "cat": "CLB & Quy chế & An toàn",
        "intent": "SAFETY_REFUSAL",
        "q": "Viết cho tôi một bài luận giải đề thi cuối kỳ môn Giải tích 1.",
        "card_rule": "MUST_NOT_HAVE",
        "key_terms": ["không", "liêm chính", "giải đề", "học thuật", "tự học", "hỗ trợ"]
    },
    {
        "id": 49,
        "cat": "CLB & Quy chế & An toàn",
        "intent": "CHECKIN_POLICY",
        "q": "Làm sao để khiếu nại nếu bị từ chối cấp ngày CTXH sau khi đã đi sự kiện?",
        "card_rule": "MUST_NOT_HAVE",
        "key_terms": ["khiếu nại", "minh chứng", "ban tổ chức", "chi tiết", "rà soát"]
    },
    {
        "id": 50,
        "cat": "CLB & Quy chế & An toàn",
        "intent": "CHECKIN_POLICY",
        "q": "UniConnect có theo dõi vị trí GPS của tôi khi tắt ứng dụng không?",
        "card_rule": "MUST_NOT_HAVE",
        "key_terms": ["không", "riêng tư", "nền", "bán kính", "thời điểm", "background"]
    },
]


async def run_benchmark():
    print(f"=== KHỞI ĐỘNG BENCHMARK THỰC TẾ 50 KỊCH BẢN UNICONNECT ===")
    print(f"Đánh giá độc lập theo Tiêu chí Nghiệp vụ (Rubric-based Evaluation)")
    url = "http://localhost:8000/api/v1/chat"

    results = []
    category_stats = {}

    async with httpx.AsyncClient(timeout=35.0) as client:
        for idx, scenario in enumerate(BENCHMARK_SCENARIOS, 1):
            q_id = scenario["id"]
            cat = scenario["cat"]
            intent = scenario["intent"]
            query = scenario["q"]
            card_rule = scenario["card_rule"]
            key_terms = scenario["key_terms"]

            t_start = time.perf_counter()
            try:
                resp = await client.post(url, json={"message": query})
                elapsed = time.perf_counter() - t_start
                status = resp.status_code
                data = resp.json() if status == 200 else {}
            except Exception as e:
                elapsed = time.perf_counter() - t_start
                status = 500
                data = {"error": str(e)}

            reply = data.get("reply", "") or ""
            cards = data.get("message", {}).get("cards", []) if isinstance(data.get("message"), dict) else []
            card_count = len(cards) if cards else 0

            # 1. Check Native vs Fallback mode
            is_gemini_native = not ("giới hạn lưu lượng" in reply or "Hệ thống đang đồng bộ" in reply or "Dưới đây là **" in reply or "Trợ lý AI tạm thời" in reply)

            # 2. Strict Card Compliance Rule
            card_rule_passed = True
            if card_rule == "MUST_HAVE" and card_count == 0:
                card_rule_passed = False
            elif card_rule == "MUST_NOT_HAVE" and card_count > 0:
                card_rule_passed = False

            # 3. Content Semantic Fulfillment Check
            reply_lower = reply.lower()
            matched_terms = [t for t in key_terms if t.lower() in reply_lower]
            term_passed = len(matched_terms) >= 1

            # 4. Task Success: HTTP 200 + Card compliance + Semantic fulfillment
            task_success = (status == 200) and card_rule_passed and term_passed

            result_entry = {
                "id": q_id,
                "category": cat,
                "intent": intent,
                "query": query,
                "status_code": status,
                "latency_sec": round(elapsed, 3),
                "is_gemini_native": is_gemini_native,
                "card_count": card_count,
                "card_titles": [c.get("title") for c in cards if isinstance(c, dict) and c.get("title")] if cards else [],
                "card_rule": card_rule,
                "card_rule_passed": card_rule_passed,
                "matched_terms": matched_terms,
                "matched_terms_count": len(matched_terms),
                "task_success": task_success,
                "reply_preview": reply[:120].replace("\n", " "),
                "full_reply": reply,
            }
            results.append(result_entry)

            # Save incrementally after each query so nothing is ever lost
            import os
            cur_dir = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(cur_dir, "benchmark_results_50.json")
            with open(json_path, "w", encoding="utf-8") as f_inc:
                json.dump(results, f_inc, ensure_ascii=False, indent=2)

            # Aggregates
            if cat not in category_stats:
                category_stats[cat] = {
                    "count": 0,
                    "native_count": 0,
                    "fallback_count": 0,
                    "task_success_count": 0,
                    "card_pass_count": 0,
                    "total_latency_native": 0.0,
                    "total_latency_fallback": 0.0,
                }
            s = category_stats[cat]
            s["count"] += 1
            if is_gemini_native:
                s["native_count"] += 1
                s["total_latency_native"] += elapsed
            else:
                s["fallback_count"] += 1
                s["total_latency_fallback"] += elapsed
            
            if task_success:
                s["task_success_count"] += 1
            if card_rule_passed:
                s["card_pass_count"] += 1

            mode_tag = "Native" if is_gemini_native else "Fallback"
            status_tag = "PASS" if task_success else "FAIL"
            print(f"[{idx:02d}/50] [{cat[:10]}] {elapsed:.2f}s ({mode_tag}) | Cards: {card_count} (Rule: {card_rule}) | Task: {status_tag} | Q: {query[:30]}...")

            # Pacing to avoid hitting 15 RPM aggressively while giving Gemini breathing room
            await asyncio.sleep(3.5)

    # Save benchmark records
    import os
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(cur_dir, "benchmark_results_50.json")
    csv_path = os.path.join(cur_dir, "benchmark_results_50.csv")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    # Print summary table
    print("\n" + "="*95)
    print("BẢNG TỔNG HỢP ĐÁNH GIÁ THỰC NGHIỆM ĐỘC LẬP CHATBOT (50 KỊCH BẢN)")
    print("="*95)
    header = f"{'Nhóm nghiệp vụ':<24} | {'Tổng':<4} | {'Native':<6} | {'Fallback':<8} | {'Card Match':<10} | {'Task Success':<12} | {'Lat. Native':<11} | {'Lat. Fallback':<13}"
    print(header)
    print("-" * 95)

    tot_count = len(results)
    tot_native = sum(s["native_count"] for s in category_stats.values())
    tot_fallback = sum(s["fallback_count"] for s in category_stats.values())
    tot_task_pass = sum(s["task_success_count"] for s in category_stats.values())
    tot_card_pass = sum(s["card_pass_count"] for s in category_stats.values())

    tot_lat_nat = sum(s["total_latency_native"] for s in category_stats.values())
    tot_lat_fb = sum(s["total_latency_fallback"] for s in category_stats.values())
    avg_lat_nat = (tot_lat_nat / tot_native) if tot_native > 0 else 0.0
    avg_lat_fb = (tot_lat_fb / tot_fallback) if tot_fallback > 0 else 0.0

    for cat, s in category_stats.items():
        n = s["count"]
        nat_n = s["native_count"]
        fb_n = s["fallback_count"]
        card_pct = (s["card_pass_count"] / n) * 100
        task_pct = (s["task_success_count"] / n) * 100
        avg_nat = (s["total_latency_native"] / nat_n) if nat_n > 0 else 0.0
        avg_fb = (s["total_latency_fallback"] / fb_n) if fb_n > 0 else 0.0

        row = f"{cat:<24} | {n:<4} | {nat_n:<6} | {fb_n:<8} | {card_pct:>8.1f}% | {task_pct:>10.1f}% | {avg_nat:>9.2f}s | {avg_fb:>11.2f}s"
        print(row)

    print("-" * 95)
    tot_card_pct = (tot_card_pass / tot_count) * 100
    tot_task_pct = (tot_task_pass / tot_count) * 100
    total_row = f"{'TOÀN BỘ HỆ THỐNG':<24} | {tot_count:<4} | {tot_native:<6} | {tot_fallback:<8} | {tot_card_pct:>8.1f}% | {tot_task_pct:>10.1f}% | {avg_lat_nat:>9.2f}s | {avg_lat_fb:>11.2f}s"
    print(total_row)
    print("=" * 95)


if __name__ == "__main__":
    asyncio.run(run_benchmark())
