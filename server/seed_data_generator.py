"""
AI Data Generator — Sinh dữ liệu quy mô lớn cho Long Khánh và lưu ra file CSV / JSON
để tái sử dụng vĩnh viễn mà không cần gọi lại Gemini API mỗi lần seed.

Chạy:
  python seed_data_generator.py
"""

import asyncio
import csv
import json
import os
import sys

# Đảm bảo UTF-8 trên Windows console
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from google import genai
from pydantic import BaseModel
from app.core.config import settings

# Thư mục lưu dữ liệu CSV
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed_data")
os.makedirs(DATA_DIR, exist_ok=True)


# ============================================================================
# Schemas
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
# Bối cảnh Long Khánh
# ============================================================================

LONG_KHANH_CONTEXT = """
BỐI CẢNH ĐỊA PHƯƠNG - TP. LONG KHÁNH, ĐỒNG NAI:

Trường đại học / cao đẳng trong khu vực:
- Đại học Công nghệ Đồng Nai (DNTU) — Phường Xuân Hòa
- Đại học Lâm nghiệp (cơ sở 2) — Phường Xuân An
- Cao đẳng Kỹ thuật Đồng Nai
- Đại học Đồng Nai
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
- Địa điểm phượt: Thác Giang Điền, Hồ Trị An, Vườn quốc gia Cát Tiên,
  Đồi chè Long Khánh, Vườn chôm chôm Long Khánh, KDL Suối Mơ
- Nhà sách: Nhà sách Fahasa Long Khánh, Nhà sách Phương Nam

Tọa độ trung tâm TP. Long Khánh: 10.9333° N, 107.2406° E
Phạm vi nội thành: Vĩ độ 10.92 - 10.96, Kinh độ 107.22 - 107.26
"""

USER_PROMPT = """{context}
Hãy tạo {count} người dùng sinh viên sinh sống / học tập tại TP. Long Khánh.
Yêu cầu:
1. username: tiếng Việt không dấu viết liền hoặc gạch dưới.
2. email: hợp lệ @gmail.com hoặc @student.dntu.edu.vn.
3. full_name: họ tên tiếng Việt đầy đủ có dấu.
4. bio: 2-3 câu chân thực về bản thân, ngành học và thói quen ở Long Khánh.
5. interests: danh sách 3-5 sở thích tiếng Việt (KHÔNG game).
6. university: trường đại học/cao đẳng cụ thể trong khu vực.
Batch: {batch_label}
"""

GROUP_PROMPT = """{context}
Hãy tạo {count} nhóm / câu lạc bộ sinh viên tại TP. Long Khánh.
Yêu cầu:
1. name: tên CLB / nhóm cụ thể (VD: CLB Guitar DNTU, Nhóm Chạy bộ Công viên Long Khánh).
2. description: mô tả 3-4 câu mục đích sinh hoạt.
3. public_description: giới thiệu ngắn gọn.
4. private_description: nội quy hoặc lịch sinh hoạt.
5. privacy: 'public' hoặc 'private'.
6. require_approval: true / false.
7. allow_member_activities: true.
8. allow_member_documents: true.
Batch: {batch_label}
"""

ACTIVITY_PROMPT = """{context}
Hãy tạo {count} hoạt động / sự kiện sinh viên thực tế tại TP. Long Khánh.
Yêu cầu:
1. title: tên hoạt động lôi cuốn, cụ thể (VD: Giao lưu Cầu lông cuối tuần tại Sân Xuân Hòa).
2. description: mô tả nội dung chi tiết.
3. private_description: ghi chú cho người tham gia.
4. category: một trong ['Study', 'Sports', 'Social', 'Entertainment'].
5. privacy: 'public' hoặc 'private'.
6. require_approval: true / false.
7. latitude: từ 10.9200 đến 10.9600.
8. longitude: từ 107.2200 đến 107.2600.
9. location_name: tên địa điểm thực tế tại Long Khánh.
10. hours_duration: 1-6 giờ.
11. days_from_now: từ -10 (quá khứ) đến 30 (tương lai).
12. max_participants: 5-50 người.
13. social_work_days: 0 hoặc từ 0.5-2.0 ngày CTXH.
Batch: {batch_label}
"""

DOCUMENT_PROMPT = """{context}
Hãy tạo {count} tài liệu học tập / kế hoạch / tài liệu sinh hoạt sinh viên tại Long Khánh.
Yêu cầu:
1. title: tên tài liệu rõ ràng.
2. description: mô tả nội dung 2-3 câu.
3. file_name: tên file có đuôi .pdf, .docx, .xlsx, .png.
4. file_type: MIME type chuẩn.
5. file_size_kb: kích thước từ 100 đến 15000 KB.
Batch: {batch_label}
"""


async def safe_generate(client, model_name, prompt, schema, max_retries=5):
    for attempt in range(max_retries):
        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt,
                config=dict(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.75,
                ),
            )
            data = json.loads(response.text)
            return schema(**data)
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                wait_time = 45 + attempt * 10
                print(f"      ⏳ Chạm giới hạn API (429), tạm dừng {wait_time}s rồi thử lại...")
                await asyncio.sleep(wait_time)
            else:
                print(f"      ⚠ Lỗi generate (lần {attempt+1}/{max_retries}): {e}")
                await asyncio.sleep(5)
    return None


async def generate_all():
    if not settings.GEMINI_API_KEY:
        print("❌ Lỗi: Chưa cấu hình GEMINI_API_KEY!")
        return

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    model_name = "gemini-3.5-flash"

    print("=" * 60)
    print("🚀 BẮT ĐẦU TẠO DỮ LIỆU SEED VÀ XUẤT RA CSV (TP. LONG KHÁNH)")
    print("=" * 60)

    # 1. USERS (Tạo 100 Users)
    users_file = os.path.join(DATA_DIR, "users.csv")
    print("\n📦 1. Đang tạo 100 Users...")
    all_users = []
    user_batches = [
        "Batch 1: Sinh viên CNTT & Trí tuệ nhân tạo",
        "Batch 2: Sinh viên Kinh tế, Marketing & Kế toán",
        "Batch 3: Sinh viên Ngôn ngữ, Du lịch & Sư phạm",
        "Batch 4: Sinh viên Cơ khí, Điện tử & Xây dựng",
        "Batch 5: Sinh viên Lâm nghiệp, Nông nghiệp công nghệ cao",
        "Batch 6: Sinh viên Luật, Quản lý & Hành chính",
        "Batch 7: Sinh viên Nghệ thuật, Thiết kế & Nhiếp ảnh",
        "Batch 8: Sinh viên Thể thao & Y khoa",
        "Batch 9: Thanh niên khởi nghiệp địa phương",
        "Batch 10: Sinh viên đa ngành hỗn hợp",
    ]
    for b in user_batches:
        print(f"   ⏳ {b}...")
        prompt = USER_PROMPT.format(context=LONG_KHANH_CONTEXT, count=10, batch_label=b)
        data = await safe_generate(client, model_name, prompt, UserList)
        if data:
            for u in data.users:
                all_users.append({
                    "username": u.username.lower().strip(),
                    "email": u.email.lower().strip(),
                    "full_name": u.full_name.strip(),
                    "bio": u.bio.strip(),
                    "interests": json.dumps(u.interests, ensure_ascii=False),
                    "university": u.university.strip(),
                })
        await asyncio.sleep(2)

    with open(users_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["username", "email", "full_name", "bio", "interests", "university"])
        writer.writeheader()
        writer.writerows(all_users)
    print(f"   ✅ Đã lưu {len(all_users)} users vào {users_file}")

    # 2. GROUPS (Tạo 50 Groups)
    groups_file = os.path.join(DATA_DIR, "groups.csv")
    print("\n📦 2. Đang tạo 50 Groups...")
    all_groups = []
    group_batches = [
        "Batch 1: CLB Thể thao (Bóng đá, Cầu lông, Chạy bộ)",
        "Batch 2: Nhóm Học tập & Luyện thi (TOEIC, Lập trình, Kế toán)",
        "Batch 3: CLB Sở thích & Nghệ thuật (Guitar, Nhiếp ảnh, Boardgame)",
        "Batch 4: CLB Tình nguyện & Hoạt động xã hội Long Khánh",
        "Batch 5: Nhóm Giao lưu văn hoá & Kỹ năng mềm",
    ]
    for b in group_batches:
        print(f"   ⏳ {b}...")
        prompt = GROUP_PROMPT.format(context=LONG_KHANH_CONTEXT, count=10, batch_label=b)
        data = await safe_generate(client, model_name, prompt, GroupList)
        if data:
            for g in data.groups:
                all_groups.append({
                    "name": g.name.strip(),
                    "description": g.description.strip(),
                    "public_description": g.public_description.strip(),
                    "private_description": g.private_description.strip(),
                    "privacy": g.privacy.lower().strip(),
                    "require_approval": g.require_approval,
                    "allow_member_activities": g.allow_member_activities,
                    "allow_member_documents": g.allow_member_documents,
                })
        await asyncio.sleep(2)

    with open(groups_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "name", "description", "public_description", "private_description",
            "privacy", "require_approval", "allow_member_activities", "allow_member_documents"
        ])
        writer.writeheader()
        writer.writerows(all_groups)
    print(f"   ✅ Đã lưu {len(all_groups)} groups vào {groups_file}")

    # 3. ACTIVITIES (Tạo 100 Activities)
    activities_file = os.path.join(DATA_DIR, "activities.csv")
    print("\n📦 3. Đang tạo 100 Activities...")
    all_activities = []
    act_batches = [
        "Batch 1: Hoạt động học tập & Workshop công nghệ",
        "Batch 2: Giải đấu thể thao & Rèn luyện sức khỏe",
        "Batch 3: Giao lưu cà phê, Boardgame & Trà sữa",
        "Batch 4: Hoạt động tình nguyện, CTXH & Bảo vệ môi trường",
        "Batch 5: Phượt dã ngoại, cắm trại Hồ Trị An & Đồi chè",
        "Batch 6: Câu lạc bộ sách, đọc & thảo luận",
        "Batch 7: Âm nhạc acoustic & Nghệ thuật đường phố",
        "Batch 8: Thể thao điện tử & Giao lưu kết nối",
        "Batch 9: Hội thảo hướng nghiệp & Khởi nghiệp trẻ",
        "Batch 10: Hoạt động dã ngoại & Ẩm thực Long Khánh",
    ]
    for b in act_batches:
        print(f"   ⏳ {b}...")
        prompt = ACTIVITY_PROMPT.format(context=LONG_KHANH_CONTEXT, count=10, batch_label=b)
        data = await safe_generate(client, model_name, prompt, ActivityList)
        if data:
            for a in data.activities:
                all_activities.append({
                    "title": a.title.strip(),
                    "description": a.description.strip(),
                    "private_description": a.private_description.strip(),
                    "category": a.category.strip(),
                    "privacy": a.privacy.lower().strip(),
                    "require_approval": a.require_approval,
                    "latitude": a.latitude,
                    "longitude": a.longitude,
                    "location_name": a.location_name.strip(),
                    "hours_duration": a.hours_duration,
                    "days_from_now": a.days_from_now,
                    "max_participants": a.max_participants,
                    "social_work_days": a.social_work_days,
                })
        await asyncio.sleep(2)

    with open(activities_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "title", "description", "private_description", "category",
            "privacy", "require_approval", "latitude", "longitude",
            "location_name", "hours_duration", "days_from_now", "max_participants", "social_work_days"
        ])
        writer.writeheader()
        writer.writerows(all_activities)
    print(f"   ✅ Đã lưu {len(all_activities)} activities vào {activities_file}")

    # 4. DOCUMENTS (Tạo 60 Documents)
    docs_file = os.path.join(DATA_DIR, "documents.csv")
    print("\n📦 4. Đang tạo 60 Documents...")
    all_docs = []
    doc_batches = [
        "Batch 1: Đề cương, giáo trình & bài tập môn học",
        "Batch 2: Nội quy CLB, biên bản họp & biểu mẫu sinh hoạt",
        "Batch 3: Kế hoạch sự kiện, dự trù kinh phí & timeline",
        "Batch 4: Poster, hình ảnh truyền thông & tài liệu hướng dẫn",
        "Batch 5: Tài liệu kỹ năng mềm, slide thuyết trình & báo cáo",
        "Batch 6: Tài liệu chuyên đề khoa học & công nghệ",
    ]
    for b in doc_batches:
        print(f"   ⏳ {b}...")
        prompt = DOCUMENT_PROMPT.format(context=LONG_KHANH_CONTEXT, count=10, batch_label=b)
        data = await safe_generate(client, model_name, prompt, DocumentList)
        if data:
            for d in data.documents:
                all_docs.append({
                    "title": d.title.strip(),
                    "description": d.description.strip(),
                    "file_name": d.file_name.strip(),
                    "file_type": d.file_type.strip(),
                    "file_size_kb": d.file_size_kb,
                })
        await asyncio.sleep(2)

    with open(docs_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "description", "file_name", "file_type", "file_size_kb"])
        writer.writeheader()
        writer.writerows(all_docs)
    print(f"   ✅ Đã lưu {len(all_docs)} documents vào {docs_file}")

    print("\n" + "=" * 60)
    print("🎉 HOÀN TẤT XUẤT DỮ LIỆU RA THƯ MỤC seed_data/")
    print("=" * 60)
    print(f"📁 Thư mục: {DATA_DIR}")
    print(f"   📄 users.csv:      {len(all_users)} dòng")
    print(f"   👥 groups.csv:     {len(all_groups)} dòng")
    print(f"   📅 activities.csv: {len(all_activities)} dòng")
    print(f"   📑 documents.csv:  {len(all_docs)} dòng")
    print("\n👉 Giờ bạn có thể chạy 'python seed_from_csv.py' để nạp vào DB trong vài giây!")


if __name__ == "__main__":
    asyncio.run(generate_all())
