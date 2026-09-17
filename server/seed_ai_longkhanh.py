"""
Seed script sử dụng Gemini AI để tạo dữ liệu thực tế cho TP. Long Khánh, Đồng Nai.

Dữ liệu bao gồm:
- 50 Users (sinh viên / thanh niên Long Khánh)
- 25 Groups (CLB, nhóm học tập, thể thao)
- 50 Activities (hoạt động thực tế với địa điểm có thật)
- 30 Documents (tài liệu học tập, nội quy, kế hoạch)
- User Follows (mạng lưới follow)
- JoinRequests (approved, pending, declined)
- GroupJoinRequests (pending)
- Embeddings cho activities (vector search)

Chạy: python seed_ai_longkhanh.py
"""

import asyncio
import datetime
import random
from pydantic import BaseModel
import os
import sys

# Thêm đường dẫn để có thể import từ app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Fix Vietnamese print on Windows terminal
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from google import genai
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text

from app.core.config import settings
from app.core.security import hash_password
from app.modules.users.models import User, UserRole, UserFollow
from app.modules.activities.models import Activity, ActivityPrivacy
from app.modules.groups.models import Group, GroupMember, GroupRole, GroupPrivacy, GroupJoinRequest
from app.modules.participation.models import JoinRequest, RequestStatus
from app.modules.documents.models import Document
from app.modules.chat.embeddings import generate_embedding

# ============================================================================
# Pydantic Schemas cho Gemini Structured Output
# ============================================================================

class GeneratedUser(BaseModel):
    username: str
    email: str
    full_name: str
    bio: str
    interests: list[str]
    university: str

class UserList(BaseModel):
    users: list[GeneratedUser]

class GeneratedGroup(BaseModel):
    name: str
    description: str
    public_description: str
    private_description: str
    privacy: str
    require_approval: bool
    allow_member_activities: bool
    allow_member_documents: bool

class GroupList(BaseModel):
    groups: list[GeneratedGroup]

class GeneratedActivity(BaseModel):
    title: str
    description: str
    private_description: str
    category: str
    privacy: str
    require_approval: bool
    latitude: float
    longitude: float
    location_name: str
    hours_duration: int
    days_from_now: int
    max_participants: int
    social_work_days: float

class ActivityList(BaseModel):
    activities: list[GeneratedActivity]

class GeneratedDocument(BaseModel):
    title: str
    description: str
    file_name: str
    file_type: str
    file_size_kb: int

class DocumentList(BaseModel):
    documents: list[GeneratedDocument]


# ============================================================================
# Dữ liệu thực tế TP. Long Khánh, Đồng Nai
# ============================================================================

LONG_KHANH_CONTEXT = """
BỐI CẢNH ĐỊA PHƯƠNG - TP. LONG KHÁNH, ĐỒNG NAI:

Trường đại học / cao đẳng trong khu vực:
- Đại học Công nghệ Đồng Nai (DNTU) — Khu phố 7, Phường Xuân Hòa
- Đại học Lâm nghiệp (cơ sở 2) — Phường Xuân An
- Cao đẳng Kỹ thuật Đồng Nai — TP. Biên Hòa (sinh viên đi về Long Khánh)
- Đại học Đồng Nai — TP. Biên Hòa (sinh viên quê Long Khánh)
- Trường CĐ Nghề Đồng Nai

Các địa điểm thực tế tại Long Khánh:
- Quán cà phê: Highland Coffee Long Khánh (Hùng Vương), Phúc Long Nguyễn Trãi, 
  The Coffee House Hùng Vương, Cà phê Mộc (Lê Hồng Phong), Cà phê vườn Trần Phú,
  Passio Coffee Nguyễn Ái Quốc, Cà phê Bụi (KP5 Xuân An), Milano Coffee (CMT8)
- Quán trà sữa: ToCoToCo Long Khánh, Phê La Hùng Vương, Tiger Sugar CMT8,
  Ding Tea Nguyễn Trãi, Gong Cha Long Khánh
- Sân thể thao: Sân bóng đá Mini Long Khánh (đường Nguyễn Ái Quốc), 
  SVĐ Long Khánh (Phường Xuân An), Sân cầu lông Xuân Hòa (KP3),
  Sân bóng chuyền DNTU, Sân bóng rổ Công viên Long Khánh,
  Sân tennis Khu thể thao Xuân Trung, Hồ bơi Phường Xuân Bình
- Rạp phim: Cinestar Long Khánh (Hùng Vương), CGV Long Khánh
- Thư viện: Thư viện Thành phố Long Khánh (Trần Phú), Thư viện DNTU
- Chợ & ăn uống: Chợ Long Khánh, Phố ăn vặt Nguyễn Trãi, Bánh mì chả cá Long Khánh,
  Bún bò Xuân An, Cơm tấm Năm Sài Gòn (CMT8), Phở 24h Hùng Vương
- Công viên: Công viên Long Khánh (trung tâm), Hồ nước trung tâm Long Khánh,
  Quảng trường Long Khánh
- Địa điểm phượt: Thác Giang Điền, Hồ Trị An, Vườn quốc gia Cát Tiên (cách ~60km),
  Đồi chè Long Khánh, Vườn chôm chôm Long Khánh, KDL Suối Mơ
- Nhà sách: Nhà sách Fahasa Long Khánh, Nhà sách Phương Nam

Tọa độ trung tâm TP. Long Khánh: 10.9333° N, 107.2406° E
Phạm vi nội thành: Vĩ độ 10.92 - 10.96, Kinh độ 107.22 - 107.26
"""


# ============================================================================
# Prompt Templates chi tiết
# ============================================================================

USER_PROMPT_TEMPLATE = """
{context}

Hãy tạo {count} người dùng sinh viên Việt Nam sinh sống hoặc học tập tại TP. Long Khánh, Đồng Nai.

YÊU CẦU CHI TIẾT:
1. username: tiếng Việt không dấu, viết liền hoặc gạch dưới (ví dụ: nguyenvana, tran_bich_ngoc).
   KHÔNG trùng nhau trong batch.
2. email: phải hợp lệ, dùng domain @gmail.com hoặc @dntu.edu.vn hoặc @student.dntu.edu.vn.
3. full_name: Họ tên đầy đủ tiếng Việt CÓ DẤU (ví dụ: Nguyễn Văn An, Trần Bích Ngọc).
   Đa dạng họ: Nguyễn, Trần, Lê, Phạm, Hoàng, Huỳnh, Phan, Võ, Đặng, Bùi, Đỗ, Hồ, Ngô, Dương, Lý.
4. bio: 2-4 câu tiếng Việt chân thực, mô tả bản thân như sinh viên thực sự viết.
   Nên nhắc đến ngành học, sở thích, hoặc cuộc sống ở Long Khánh.
   Ví dụ: "Sinh viên năm 3 CNTT tại DNTU. Thích code và chơi cầu lông cuối tuần. 
   Hay cà phê ở Highland trên đường Hùng Vương."
5. interests: danh sách 3-6 sở thích cụ thể bằng tiếng Việt.
   Ví dụ: ["Lập trình", "Cầu lông", "Đọc sách", "Chụp ảnh", "Nấu ăn"]
   KHÔNG BAO GỒM game/trò chơi điện tử.
6. university: phải là một trong các trường thực tế đã liệt kê ở trên.

Đa dạng: có nam lẫn nữ, nhiều ngành khác nhau (CNTT, Kế toán, Cơ khí, Quản trị kinh doanh,
Ngôn ngữ Anh, Điện tử, Xây dựng, Du lịch...).
Batch hiện tại: {batch_label}
"""

GROUP_PROMPT_TEMPLATE = """
{context}

Hãy tạo {count} nhóm / câu lạc bộ thực tế hoạt động tại TP. Long Khánh, Đồng Nai.

YÊU CẦU CHI TIẾT:
1. name: Tên CLB / nhóm bằng tiếng Việt, rõ ràng, chuyên nghiệp.
   Ví dụ: "CLB Cầu lông DNTU", "Nhóm học TOEIC Long Khánh", "Đội bóng đá FC Xuân An".
   MỖI TÊN PHẢI DUY NHẤT, không trùng nhau.
2. description: Mô tả chung 3-5 câu, giới thiệu nhóm cho người quản trị.
3. public_description: Mô tả ngắn 2-3 câu cho người ngoài xem (khi nhóm public).
4. private_description: Thông tin nội bộ như lịch sinh hoạt, quy tắc riêng, phí sinh hoạt.
   Ví dụ: "Sinh hoạt thứ 4 và thứ 7 hàng tuần. Phí 50k/tháng cho thuê sân. Nhóm trưởng: anh Tuấn."
5. privacy: "public" hoặc "private". Nhóm học tập thường public, nhóm thể thao private.
6. require_approval: true nếu nhóm chọn lọc thành viên, false nếu ai cũng có thể tham gia.
7. allow_member_activities: true nếu thành viên có thể tự tạo hoạt động, false nếu chỉ admin.
8. allow_member_documents: true nếu thành viên có thể upload tài liệu, false nếu chỉ admin.

CHỦ ĐỀ ĐA DẠNG (phân bổ đều):
- Học nhóm / Ôn thi: TOEIC, IELTS, Tin học, Toán cao cấp, Kế toán...
- Thể thao: Đá banh, Cầu lông, Bóng chuyền, Bóng rổ, Chạy bộ, Bơi lội
- Tình nguyện / Công tác xã hội: Hiến máu, Mùa hè xanh, Dọn rác môi trường
- Sở thích: Chụp ảnh, Nấu ăn, Đọc sách, Đi phượt
TUYỆT ĐỐI KHÔNG có game/trò chơi điện tử.

Batch hiện tại: {batch_label}
"""

ACTIVITY_PROMPT_TEMPLATE = """
{context}

Hãy tạo {count} hoạt động / sự kiện thực tế diễn ra tại TP. Long Khánh, Đồng Nai.
Mỗi hoạt động phải được viết CHI TIẾT, CHUYÊN NGHIỆP như một bài đăng thật trên ứng dụng sinh viên.

YÊU CẦU CHI TIẾT:
1. title: Tiêu đề sự kiện rõ ràng, hấp dẫn, cụ thể, bằng tiếng Việt.
   Ví dụ: "Đá banh giao hữu 5v5 — Chiều thứ 7 tại sân mini Nguyễn Ái Quốc"
   Ví dụ: "Workshop Git & GitHub cho người mới bắt đầu — Thư viện DNTU"

2. description: MÔ TẢ DÀI 8-15 CÂU, viết như một bài đăng thật sự trên app. BẮT BUỘC bao gồm TẤT CẢ các phần sau:

   📌 GIỚI THIỆU (2-3 câu): Mục đích, ý nghĩa của hoạt động. Tại sao nên tham gia? Hoạt động này giúp gì cho bản thân?
   
   📋 YÊU CẦU NGƯỜI THAM GIA:
   - Đối tượng: Ai có thể tham gia? (sinh viên năm mấy, có cần kinh nghiệm không, giới tính)
   - Kỹ năng cần có: (nếu có) Ví dụ: "Biết chơi cầu lông cơ bản", "Không yêu cầu kinh nghiệm"
   - Trang phục: Mặc gì? (đồ thể thao, thoải mái, có đồng phục không)
   - Dụng cụ/đồ mang theo: Laptop, vợt, giày sân cỏ, bút vở, nước uống...
   
   ⏰ LỊCH TRÌNH CHI TIẾT:
   - Giờ tập trung: Ví dụ "13:30 tập trung trước cổng sân"
   - Giờ bắt đầu — kết thúc: Ví dụ "14:00 - 17:00"
   - Agenda/lộ trình từng phần. Ví dụ:
     "14:00-14:15: Điểm danh, khởi động | 14:15-15:30: Thi đấu vòng bảng | 15:30-15:45: Giải lao | 15:45-16:45: Bán kết & Chung kết | 16:45-17:00: Trao giải"
   
   💰 CHI PHÍ: Miễn phí hay có phí? Bao nhiêu? Phí bao gồm những gì?
   Ví dụ: "Phí sân 30k/người, tự lo nước uống" hoặc "Hoàn toàn miễn phí, BTC tài trợ nước suối"
   
   📍 ĐỊA ĐIỂM: Nhắc lại địa điểm cụ thể, cách đi, mốc nhận diện.
   Ví dụ: "Sân mini Nguyễn Ái Quốc (đối diện cây xăng, cổng màu xanh). Gửi xe miễn phí trong sân."

   Ví dụ MẪU cho description hoàn chỉnh:
   "🏸 Giải cầu lông giao hữu dành cho sinh viên DNTU và các bạn trẻ Long Khánh! Đây là dịp để các bạn yêu cầu lông giao lưu, thi đấu và kết bạn.

   📋 Yêu cầu: Biết chơi cầu lông cơ bản (không nhận người chưa biết chơi). Mang theo vợt cá nhân, giày trong sân, khăn và nước uống. Mặc đồ thể thao gọn gàng.

   ⏰ Lịch trình:
   • 13:30: Tập trung tại sân, đăng ký bảng đấu
   • 14:00 - 14:15: Khởi động chung
   • 14:15 - 15:45: Thi đấu vòng bảng (đánh đôi nam/nữ)
   • 15:45 - 16:00: Giải lao, bốc thăm bán kết
   • 16:00 - 16:45: Bán kết & Chung kết
   • 16:45 - 17:00: Trao giải, chụp ảnh lưu niệm

   💰 Phí tham gia: 25.000đ/người (bao gồm cầu, nước suối). Giải thưởng: Cúp + 500k cho đội vô địch.
   📍 Sân cầu lông Xuân Hòa (KP3, cạnh trường tiểu học Xuân Hòa). Gửi xe miễn phí."

3. private_description: Thông tin NỘI BỘ chi tiết chỉ người tham gia thấy, 4-8 câu, bao gồm:
   - Link nhóm chat Zalo/Facebook: Ví dụ "Nhóm Zalo: https://zalo.me/g/abc123"
   - SĐT liên hệ người phụ trách: Ví dụ "Liên hệ anh Tuấn (0901234567) nếu có vấn đề"
   - Điểm tập trung chi tiết: "Tập trung lúc 13:30 trước cổng chính, ai đến muộn gọi SĐT trên"
   - Hướng dẫn gửi xe / đi đường
   - Link tài liệu (nếu có): "Slide bài giảng: https://drive.google.com/..."
   - Phương án dự phòng: "Nếu mưa sẽ dời sang Chủ nhật, thông báo trong nhóm Zalo trước 10h sáng"

4. category: CHỈ ĐƯỢC CHỌN MỘT TRONG: 'Study', 'Sports', 'Social', 'Entertainment'.
   - Study: học nhóm, ôn thi, workshop, seminar
   - Sports: đá banh, cầu lông, bóng chuyền, chạy bộ, bơi, gym
   - Social: tình nguyện, giao lưu, họp mặt, networking, hiến máu, dọn rác
   - Entertainment: xem phim, picnic, đi phượt, karaoke, BBQ
5. privacy: "public" hoặc "private".
6. require_approval: true hoặc false.
7. latitude: trong khoảng 10.92 đến 10.96 (nội thành Long Khánh).
8. longitude: trong khoảng 107.22 đến 107.26 (nội thành Long Khánh).
9. location_name: ĐỊA CHỈ CỤ THỂ CÓ THẬT tại Long Khánh.
   Ví dụ: "Sân cầu lông Xuân Hòa, KP3, P. Xuân Hòa, TP. Long Khánh"
10. hours_duration: 1 đến 5 giờ.
11. days_from_now: từ -7 đến 20.
    - Số âm = sự kiện đã diễn ra (quá khứ)
    - Số dương = sự kiện sắp tới (tương lai)
    - 0 = hôm nay
12. max_participants: 2 đến 50 tùy loại sự kiện.
13. social_work_days: 0 nếu không tính công tác xã hội.
    0.5 hoặc 1.0 nếu là hoạt động tình nguyện / công ích.

PHÂN BỔ CHỦ ĐỀ ĐỀU:
- 3 Study (học nhóm, ôn thi TOEIC, workshop lập trình...)
- 3 Sports (đá banh, cầu lông, bóng chuyền...)
- 2 Social (cà phê giao lưu, tình nguyện dọn rác, hiến máu...)
- 2 Entertainment (xem phim Cinestar, picnic Hồ Trị An, phượt...)

QUAN TRỌNG: Mỗi hoạt động phải THỰC SỰ CHI TIẾT như một bài đăng chính thức. KHÔNG được viết mô tả chung chung, sơ sài.

Batch hiện tại: {batch_label}
"""

DOCUMENT_PROMPT_TEMPLATE = """
{context}

Hãy tạo {count} tài liệu thực tế liên quan đến sinh hoạt sinh viên tại TP. Long Khánh.
Mỗi tài liệu phải có mô tả chi tiết, chuyên nghiệp.

YÊU CẦU CHI TIẾT:
1. title: Tiêu đề tài liệu rõ ràng, chuyên nghiệp, cụ thể.
   Ví dụ: "Đề cương ôn thi TOEIC Reading Part 5-6 — Tháng 8/2026"
   Ví dụ: "Nội quy CLB Cầu lông DNTU — Năm học 2025-2026"
   Ví dụ: "Kế hoạch chi tiết chuyến phượt Hồ Trị An — 15/09/2026"

2. description: MÔ TẢ 4-6 CÂU chi tiết, bao gồm:
   - Nội dung tài liệu gồm những gì (liệt kê cụ thể)
   - Ai soạn / biên soạn (cá nhân hay nhóm nào)
   - Dùng cho đối tượng nào, mục đích gì
   - Cách sử dụng / lưu ý khi dùng tài liệu
   Ví dụ: "Tổng hợp 200 câu hỏi Part 5-6 thường gặp trong kỳ thi TOEIC, kèm đáp án chi tiết 
   và giải thích ngữ pháp cho từng câu. Soạn bởi nhóm TOEIC Long Khánh dựa trên đề thi thật 
   từ 2023-2026. Phù hợp cho bạn đang ôn thi mục tiêu 600-750. Nên làm mỗi ngày 20 câu và 
   ghi chú lại các lỗi sai."

3. file_name: Tên file thực tế, KHÔNG CÓ DẤU TIẾNG VIỆT, chỉ dùng a-z, 0-9 và gạch dưới.
   BẮT BUỘC kết thúc bằng đuôi file phù hợp (.pdf, .jpg, .png, .docx, .xlsx).
   Ví dụ: "de_cuong_toeic_part5_6_thang8.pdf", "noi_quy_clb_cau_long_dntu.pdf"

4. file_type: Chỉ được chọn MỘT TRONG các giá trị sau (copy chính xác):
   - "application/pdf"
   - "image/jpeg"
   - "image/png"
   ƯU TIÊN dùng "application/pdf" cho hầu hết tài liệu. Chỉ dùng image/jpeg hoặc image/png cho poster và ảnh.

5. file_size_kb: Kích thước file hợp lý (đơn vị KB). Số nguyên dương từ 100 đến 5000.

CHỦ ĐỀ TÀI LIỆU ĐA DẠNG:
- Đề cương ôn thi / Tài liệu học tập (TOEIC, IELTS, Tin học, Toán cao cấp, Kế toán)
- Nội quy câu lạc bộ (thể thao, học nhóm) — bao gồm quy tắc, phí sinh hoạt, lịch sinh hoạt
- Kế hoạch sự kiện (đi phượt, tình nguyện, giải đấu) — bao gồm lộ trình, phân công, budget
- Biên bản họp nhóm — tóm tắt nội dung họp, quyết định, phân công
- Poster sự kiện / Ảnh hoạt động
- Danh sách thành viên / Bảng điểm / Bảng xếp hạng

TUYỆT ĐỐI KHÔNG có game/trò chơi điện tử.

Batch hiện tại: {batch_label}
"""


# ============================================================================
# Helper functions
# ============================================================================

def make_unique_username(base: str, existing: set[str]) -> str:
    """Tạo username duy nhất bằng cách thêm số random nếu bị trùng."""
    candidate = base.lower().replace(" ", "_").replace("-", "_")
    # Loại bỏ ký tự đặc biệt
    candidate = "".join(c for c in candidate if c.isalnum() or c == "_")
    if len(candidate) < 3:
        candidate = f"user_{candidate}"
    
    original = candidate
    while candidate in existing:
        candidate = f"{original}_{random.randint(100, 9999)}"
    existing.add(candidate)
    return candidate


def make_unique_email(base: str, existing: set[str]) -> str:
    """Tạo email duy nhất."""
    candidate = base.lower().strip()
    original = candidate
    while candidate in existing:
        name, domain = original.split("@", 1)
        candidate = f"{name}_{random.randint(100, 9999)}@{domain}"
    existing.add(candidate)
    return candidate


def make_unique_group_name(base: str, existing: set[str]) -> str:
    """Tạo tên nhóm duy nhất."""
    candidate = base.strip()
    original = candidate
    counter = 2
    while candidate.lower() in existing:
        candidate = f"{original} {counter}"
        counter += 1
    existing.add(candidate.lower())
    return candidate


async def safe_generate(client, model_name: str, prompt: str, schema, retries: int = 3):
    """Gọi Gemini API với retry logic."""
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": schema,
                },
            )
            if response and response.parsed:
                return response.parsed
            print(f"   ⚠ Response rỗng, thử lại ({attempt + 1}/{retries})...")
        except Exception as e:
            print(f"   ⚠ Lỗi API: {e}")
            if attempt < retries - 1:
                wait = (attempt + 1) * 5
                print(f"   Đợi {wait}s rồi thử lại...")
                await asyncio.sleep(wait)
    return None


# ============================================================================
# Main Seed Function
# ============================================================================

async def seed():
    if not settings.GEMINI_API_KEY:
        print("❌ Lỗi: GEMINI_API_KEY chưa được cấu hình trong .env!")
        return

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    model_name = "gemini-2.5-flash"

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    # Tracking sets for uniqueness
    used_usernames: set[str] = set()
    used_emails: set[str] = set()
    used_group_names: set[str] = set()

    async with async_session() as db:
        # ====================================================================
        # BƯỚC 0: Dọn dẹp dữ liệu cũ
        # ====================================================================
        print("=" * 60)
        print("🗑️  BƯỚC 0: Dọn dẹp dữ liệu cũ (TRUNCATE CASCADE)...")
        print("=" * 60)
        await db.execute(text(
            "TRUNCATE TABLE join_requests, documents, group_join_requests, "
            "group_members, activities, groups, user_follows, users CASCADE"
        ))
        await db.commit()
        print("✅ Đã dọn dẹp xong.\n")

        # ====================================================================
        # BƯỚC 1: Tạo Users (50 người)
        # ====================================================================
        print("=" * 60)
        print("👤 BƯỚC 1: Tạo Users (50 sinh viên Long Khánh)...")
        print("=" * 60)

        users_db: list[User] = []
        batch_labels_user = [
            "1/5 — Sinh viên CNTT & Kỹ thuật",
            "2/5 — Sinh viên Kinh tế & Quản trị",
            "3/5 — Sinh viên Ngôn ngữ & Du lịch",
            "4/5 — Sinh viên Cơ khí & Xây dựng",
            "5/5 — Sinh viên đa ngành (hỗn hợp)",
        ]

        hashed_password = hash_password("password123")

        for i, label in enumerate(batch_labels_user):
            print(f"   📦 Batch {label}...")
            prompt = USER_PROMPT_TEMPLATE.format(
                context=LONG_KHANH_CONTEXT,
                count=10,
                batch_label=label,
            )
            data = await safe_generate(client, model_name, prompt, UserList)
            if data and hasattr(data, 'users'):
                for u in data.users:
                    username = make_unique_username(u.username, used_usernames)
                    email = make_unique_email(u.email, used_emails)
                    user = User(
                        username=username,
                        email=email,
                        full_name=u.full_name,
                        bio=u.bio,
                        interests=u.interests,
                        university=u.university,
                        password_hash=hashed_password,
                        role=UserRole.student,
                        is_active=True,
                        is_verified=random.choice([True, True, True, False]),  # 75% đã xác minh
                    )
                    db.add(user)
                    users_db.append(user)
                print(f"   ✅ Batch {i+1}: +{len(data.users)} users")
            else:
                print(f"   ❌ Batch {i+1}: Không nhận được dữ liệu!")
            await asyncio.sleep(3)

        await db.commit()
        for u in users_db:
            await db.refresh(u)
        print(f"\n=> Tổng cộng: {len(users_db)} users đã tạo.\n")

        if len(users_db) < 5:
            print("❌ Không đủ users để tiếp tục seeding. Dừng lại.")
            return

        # ====================================================================
        # BƯỚC 2: Tạo User Follows (mạng lưới follow)
        # ====================================================================
        print("=" * 60)
        print("🔗 BƯỚC 2: Tạo User Follows...")
        print("=" * 60)

        follow_pairs: set[tuple] = set()
        total_follows = 0
        for user in users_db:
            # Mỗi user follow 3-10 người khác (ngẫu nhiên)
            num_follows = random.randint(3, min(10, len(users_db) - 1))
            candidates = [u for u in users_db if u.id != user.id]
            to_follow = random.sample(candidates, num_follows)
            for target in to_follow:
                pair = (user.id, target.id)
                if pair not in follow_pairs:
                    follow_pairs.add(pair)
                    db.add(UserFollow(follower_id=user.id, following_id=target.id))
                    total_follows += 1

        await db.commit()
        print(f"=> Tổng cộng: {total_follows} follow relationships.\n")

        # ====================================================================
        # BƯỚC 3: Tạo Groups (25 nhóm)
        # ====================================================================
        print("=" * 60)
        print("👥 BƯỚC 3: Tạo Groups (25 nhóm / CLB)...")
        print("=" * 60)

        groups_db: list[Group] = []
        batch_labels_group = [
            "1/3 — CLB Thể thao & Sức khỏe (8 nhóm)",
            "2/3 — Nhóm Học tập & Kỹ năng (9 nhóm)",
            "3/3 — CLB Tình nguyện & Sở thích (8 nhóm)",
        ]
        group_counts = [8, 9, 8]

        for i, (label, count) in enumerate(zip(batch_labels_group, group_counts)):
            print(f"   📦 Batch {label}...")
            prompt = GROUP_PROMPT_TEMPLATE.format(
                context=LONG_KHANH_CONTEXT,
                count=count,
                batch_label=label,
            )
            data = await safe_generate(client, model_name, prompt, GroupList)
            if data and hasattr(data, 'groups'):
                for g in data.groups:
                    group_name = make_unique_group_name(g.name, used_group_names)
                    owner = random.choice(users_db)
                    group = Group(
                        name=group_name,
                        description=g.description,
                        public_description=g.public_description,
                        private_description=g.private_description,
                        privacy=(GroupPrivacy.private if g.privacy.lower() == "private"
                                 else GroupPrivacy.public),
                        require_approval=g.require_approval,
                        allow_member_activities=g.allow_member_activities,
                        allow_member_documents=g.allow_member_documents,
                        owner_id=owner.id,
                    )
                    db.add(group)
                    groups_db.append(group)
                print(f"   ✅ Batch {i+1}: +{len(data.groups)} groups")
            else:
                print(f"   ❌ Batch {i+1}: Không nhận được dữ liệu!")
            await asyncio.sleep(3)

        await db.commit()
        for g in groups_db:
            await db.refresh(g)
        print(f"\n=> Tổng cộng: {len(groups_db)} groups đã tạo.\n")

        # ====================================================================
        # BƯỚC 3b: Gán thành viên vào Groups
        # ====================================================================
        print("   🧑‍🤝‍🧑 Đang gán thành viên vào groups...")
        total_memberships = 0
        for g in groups_db:
            # Owner luôn là admin
            db.add(GroupMember(group_id=g.id, user_id=g.owner_id, role=GroupRole.admin))
            total_memberships += 1

            # Random 5-20 thành viên khác
            num_members = random.randint(5, min(20, len(users_db) - 1))
            candidates = [u for u in users_db if u.id != g.owner_id]
            members = random.sample(candidates, min(num_members, len(candidates)))

            for m in members:
                # 10% chance là admin phụ
                role = GroupRole.admin if random.random() < 0.10 else GroupRole.member
                db.add(GroupMember(group_id=g.id, user_id=m.id, role=role))
                total_memberships += 1

        await db.commit()
        print(f"   => {total_memberships} group memberships.\n")

        # ====================================================================
        # BƯỚC 3c: Tạo GroupJoinRequests (pending) cho nhóm require_approval
        # ====================================================================
        print("   📝 Đang tạo Group Join Requests (pending)...")
        total_group_requests = 0
        approval_groups = [g for g in groups_db if g.require_approval]

        for g in approval_groups:
            # 1-3 người xin vào nhóm đang chờ duyệt
            num_requests = random.randint(1, 3)
            # Lấy danh sách user chưa phải member
            existing_member_ids = set()
            # Lấy member_ids bằng cách query — nhưng do vừa add chưa flush, ta dùng logic trước đó
            # Đơn giản: random vài user, nếu trùng owner thì bỏ qua
            candidates = random.sample(users_db, min(num_requests + 5, len(users_db)))
            count_added = 0
            for u in candidates:
                if count_added >= num_requests:
                    break
                if u.id != g.owner_id:
                    db.add(GroupJoinRequest(
                        group_id=g.id,
                        user_id=u.id,
                        status="pending",
                    ))
                    count_added += 1
                    total_group_requests += 1

        await db.commit()
        print(f"   => {total_group_requests} group join requests (pending).\n")

        # ====================================================================
        # BƯỚC 4: Tạo Activities (50 hoạt động)
        # ====================================================================
        print("=" * 60)
        print("📅 BƯỚC 4: Tạo Activities (50 hoạt động)...")
        print("=" * 60)

        activities_db: list[Activity] = []
        batch_labels_activity = [
            "1/5 — Hoạt động học tập (Study)",
            "2/5 — Hoạt động thể thao (Sports)",
            "3/5 — Hoạt động giao lưu (Social)",
            "4/5 — Hoạt động giải trí (Entertainment)",
            "5/5 — Hoạt động hỗn hợp (Mixed)",
        ]

        for i, label in enumerate(batch_labels_activity):
            print(f"   📦 Batch {label}...")
            prompt = ACTIVITY_PROMPT_TEMPLATE.format(
                context=LONG_KHANH_CONTEXT,
                count=10,
                batch_label=label,
            )
            data = await safe_generate(client, model_name, prompt, ActivityList)
            if data and hasattr(data, 'activities'):
                for a in data.activities:
                    # Clamp tọa độ trong phạm vi Long Khánh
                    lat = max(10.92, min(10.96, a.latitude))
                    lng = max(107.22, min(107.26, a.longitude))

                    act_start = (datetime.datetime.now(datetime.timezone.utc)
                                 + datetime.timedelta(days=a.days_from_now))
                    # Đặt giờ bắt đầu hợp lý (7h-19h)
                    start_hour = random.choice([7, 8, 9, 13, 14, 15, 16, 17, 18, 19])
                    act_start = act_start.replace(
                        hour=start_hour,
                        minute=random.choice([0, 15, 30]),
                        second=0, microsecond=0,
                    )
                    act_end = act_start + datetime.timedelta(hours=max(1, a.hours_duration))

                    # Gán vào group ngẫu nhiên (50% chance)
                    group_id = random.choice(groups_db).id if (groups_db and random.random() > 0.5) else None

                    # Validate category
                    valid_categories = ['Study', 'Sports', 'Social', 'Entertainment']
                    category = a.category if a.category in valid_categories else random.choice(valid_categories)

                    # Validate privacy
                    privacy = (ActivityPrivacy.private if a.privacy.lower() == "private"
                               else ActivityPrivacy.public)

                    act = Activity(
                        title=a.title,
                        description=a.description,
                        private_description=a.private_description,
                        category=category,
                        location=f"POINT({lng} {lat})",
                        location_name=a.location_name,
                        start_time=act_start,
                        end_time=act_end,
                        host_id=random.choice(users_db).id,
                        group_id=group_id,
                        max_participants=max(2, a.max_participants),
                        current_participants=1,  # Host = 1, sẽ cập nhật sau
                        privacy=privacy,
                        require_approval=a.require_approval,
                        social_work_days=a.social_work_days if a.social_work_days > 0 else None,
                    )
                    db.add(act)
                    activities_db.append(act)
                print(f"   ✅ Batch {i+1}: +{len(data.activities)} activities")
            else:
                print(f"   ❌ Batch {i+1}: Không nhận được dữ liệu!")
            await asyncio.sleep(3)

        await db.commit()
        for a in activities_db:
            await db.refresh(a)
        print(f"\n=> Tổng cộng: {len(activities_db)} activities đã tạo.\n")

        # ====================================================================
        # BƯỚC 4b: Tạo JoinRequests & cập nhật current_participants
        # ====================================================================
        print("   🎟️  Đang tạo Join Requests & đồng bộ current_participants...")
        total_approved = 0
        total_pending = 0
        total_declined = 0

        for a in activities_db:
            # Host luôn approved
            db.add(JoinRequest(
                activity_id=a.id,
                user_id=a.host_id,
                status=RequestStatus.approved,
                attendance_confirmed=True if a.start_time < datetime.datetime.now(datetime.timezone.utc) else False,
            ))

            # Tính số người tham gia (không quá max_participants - 1 vì host đã tính)
            max_extra = min(a.max_participants - 1, len(users_db) - 1, 15)
            if max_extra <= 0:
                a.current_participants = 1
                continue

            num_approved = random.randint(1, max_extra)
            candidates = [u for u in users_db if u.id != a.host_id]
            random.shuffle(candidates)

            approved_count = 0
            idx = 0

            # Tạo approved requests
            while approved_count < num_approved and idx < len(candidates):
                user = candidates[idx]
                idx += 1
                is_past = a.start_time < datetime.datetime.now(datetime.timezone.utc)
                db.add(JoinRequest(
                    activity_id=a.id,
                    user_id=user.id,
                    status=RequestStatus.approved,
                    responded_at=a.start_time - datetime.timedelta(hours=random.randint(1, 48)),
                    attendance_confirmed=is_past and random.random() > 0.2,
                ))
                approved_count += 1
                total_approved += 1

            # Cập nhật current_participants = host + approved
            a.current_participants = 1 + approved_count

            # Thêm 0-3 pending requests (chỉ cho sự kiện tương lai)
            if a.start_time > datetime.datetime.now(datetime.timezone.utc):
                num_pending = random.randint(0, 3)
                pending_added = 0
                while pending_added < num_pending and idx < len(candidates):
                    user = candidates[idx]
                    idx += 1
                    db.add(JoinRequest(
                        activity_id=a.id,
                        user_id=user.id,
                        status=RequestStatus.pending,
                        message=random.choice([
                            "Cho mình tham gia với nha!",
                            "Mình muốn đăng ký tham gia ạ.",
                            "Mình có thể tham gia được không?",
                            "Xin chào, mình xin đăng ký.",
                            None, None,  # Một số không để lời nhắn
                        ]),
                    ))
                    pending_added += 1
                    total_pending += 1

            # Thêm 0-2 declined requests
            num_declined = random.randint(0, 2)
            declined_added = 0
            while declined_added < num_declined and idx < len(candidates):
                user = candidates[idx]
                idx += 1
                db.add(JoinRequest(
                    activity_id=a.id,
                    user_id=user.id,
                    status=RequestStatus.declined,
                    responded_at=a.start_time - datetime.timedelta(hours=random.randint(1, 72)),
                ))
                declined_added += 1
                total_declined += 1

        await db.commit()
        print(f"   => Approved: {total_approved} | Pending: {total_pending} | Declined: {total_declined}")
        print(f"   => current_participants đã đồng bộ với JoinRequests.\n")

        # ====================================================================
        # BƯỚC 4c: Tạo Embeddings cho Activities
        # ====================================================================
        print("   🧠 Đang tạo Embeddings cho activities...")
        embed_success = 0
        embed_fail = 0
        for idx, a in enumerate(activities_db):
            try:
                text_to_embed = f"{a.title}\n{a.description}"
                embedding = generate_embedding(text_to_embed)
                if embedding:
                    a.embedding = embedding
                    embed_success += 1
                else:
                    embed_fail += 1
            except Exception as e:
                embed_fail += 1
                print(f"   ⚠ Embedding lỗi cho '{a.title}': {e}")

            # Rate limiting: nghỉ mỗi 10 embeddings
            if (idx + 1) % 10 == 0:
                print(f"   ... đã xử lý {idx + 1}/{len(activities_db)} embeddings")
                await asyncio.sleep(2)

        await db.commit()
        print(f"   => Embedding: ✅ {embed_success} thành công | ❌ {embed_fail} thất bại.\n")

        # ====================================================================
        # BƯỚC 5: Tạo Documents (30 tài liệu)
        # ====================================================================
        print("=" * 60)
        print("📄 BƯỚC 5: Tạo Documents (30 tài liệu)...")
        print("=" * 60)

        docs_db: list[Document] = []
        batch_labels_doc = [
            "1/3 — Tài liệu học tập & Đề cương",
            "2/3 — Nội quy CLB & Kế hoạch sự kiện",
            "3/3 — Poster, Biên bản & Danh sách",
        ]

        for i, label in enumerate(batch_labels_doc):
            print(f"   📦 Batch {label}...")
            prompt = DOCUMENT_PROMPT_TEMPLATE.format(
                context=LONG_KHANH_CONTEXT,
                count=10,
                batch_label=label,
            )
            data = await safe_generate(client, model_name, prompt, DocumentList)
            if data and hasattr(data, 'documents'):
                for d in data.documents:
                    try:
                        file_name = d.file_name.replace(' ', '_')
                        # Đảm bảo file_name có extension phù hợp
                        if not any(file_name.endswith(ext) for ext in ['.pdf', '.jpg', '.jpeg', '.png', '.docx', '.xlsx']):
                            ext_map = {
                                "application/pdf": ".pdf",
                                "image/jpeg": ".jpg",
                                "image/png": ".png",
                                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
                            }
                            file_name += ext_map.get(d.file_type, ".pdf")

                        file_size = max(1024, d.file_size_kb * 1024)  # Convert KB to bytes
                        author = random.choice(users_db)
                        # 70% tài liệu thuộc về một group
                        group_id = random.choice(groups_db).id if (groups_db and random.random() > 0.3) else None

                        # R2_PUBLIC_URL đã chứa full URL, không cần thêm https://
                        base_url = settings.R2_PUBLIC_URL or "https://storage.uniconnect.vn"
                        if not base_url.startswith("http"):
                            base_url = f"https://{base_url}"

                        doc = Document(
                            title=d.title,
                            description=d.description,
                            file_name=file_name,
                            file_type=d.file_type,
                            file_size=file_size,
                            file_url=f"{base_url}/documents/{file_name}",
                            author_id=author.id,
                            group_id=group_id,
                        )
                        db.add(doc)
                        docs_db.append(doc)
                    except Exception as e:
                        print(f"   ⚠ Lỗi tạo document '{d.title}': {e}")
                print(f"   ✅ Batch {i+1}: +{len(data.documents)} documents")
            else:
                print(f"   ❌ Batch {i+1}: Không nhận được dữ liệu!")
            await asyncio.sleep(3)

        await db.commit()
        print(f"\n=> Tổng cộng: {len(docs_db)} documents đã tạo.\n")

        # ====================================================================
        # TỔNG KẾT
        # ====================================================================
        print("=" * 60)
        print("🎉 HOÀN TẤT SEEDING!")
        print("=" * 60)
        print(f"   👤 Users:        {len(users_db)}")
        print(f"   🔗 Follows:      {total_follows}")
        print(f"   👥 Groups:       {len(groups_db)}")
        print(f"   🧑‍🤝‍🧑 Memberships: {total_memberships}")
        print(f"   📅 Activities:   {len(activities_db)}")
        print(f"   🎟️  Join Requests: {total_approved} approved + {total_pending} pending + {total_declined} declined")
        print(f"   🧠 Embeddings:   {embed_success}/{len(activities_db)}")
        print(f"   📄 Documents:    {len(docs_db)}")
        print(f"\n   🔑 Password chung: password123")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())
