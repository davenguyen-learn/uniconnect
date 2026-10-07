"""Seed service for populating comprehensive production demo & testing data."""

import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.modules.users.models import User, UserRole
from app.modules.groups.models import Group, GroupPrivacy
from app.modules.activities.models import Activity, ActivityPrivacy
from app.modules.trophies.models import Trophy
from app.modules.chat.embeddings import generate_embedding

try:
    LOCAL_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
except Exception:
    LOCAL_TZ = timezone(timedelta(hours=7))

USER_LAT = 10.929718
USER_LNG = 107.250381

DEMO_USERS = [
    {
        "email": "admin@uniconnect.vn",
        "username": "admin",
        "password": "admin123",
        "full_name": "Quản Trị Viên Hệ Thống",
        "role": UserRole.admin,
        "university": "Đại học Bách khoa TP.HCM",
    },
    {
        "email": "student1@uniconnect.vn",
        "username": "student_nguyen",
        "password": "password123",
        "full_name": "Nguyễn Văn An",
        "role": UserRole.student,
        "university": "Đại học Bách khoa TP.HCM",
    },
    {
        "email": "student2@uniconnect.vn",
        "username": "student_tran",
        "password": "password123",
        "full_name": "Trần Thị Mai",
        "role": UserRole.student,
        "university": "Đại học Quốc gia TP.HCM",
    },
    {
        "email": "club_lead@uniconnect.vn",
        "username": "club_lead_bk",
        "password": "password123",
        "full_name": "Lê Hoàng Phúc",
        "role": UserRole.edu_org,
        "university": "Đại học Bách khoa TP.HCM",
    },
]

DEMO_GROUPS = [
    {
        "name": "CLB Lập trình & Trí tuệ Nhân tạo BK",
        "description": "Cộng đồng đam mê lập trình, AI, thuật toán và phát triển phần mềm ứng dụng thực tế.",
        "public_description": "Nơi giao lưu, học tập các công nghệ mới: Python, React, PyTorch, LLM và Data Science.",
        "privacy": GroupPrivacy.public,
    },
    {
        "name": "CLB Tiếng Anh & Kỹ năng Toàn cầu",
        "description": "Luyện nói tiếng Anh, thuyết trình, phỏng vấn ứng tuyển và kỹ năng mềm sinh viên.",
        "public_description": "Không gian luyện phản xạ giao tiếp tiếng Anh 100% tự nhiên mỗi tuần.",
        "privacy": GroupPrivacy.public,
    },
    {
        "name": "Đội Sinh viên Tình nguyện UniConnect",
        "description": "Các chương trình thiện nguyện, công tác xã hội và hoạt động vì cộng đồng.",
        "public_description": "Lan tỏa giá trị nhân văn và tinh thần cống hiến của tuổi trẻ sinh viên.",
        "privacy": GroupPrivacy.public,
    },
    {
        "name": "CLB Thể thao & Cầu lông Sinh viên",
        "description": "Rèn luyện thể lực, giao lưu cầu lông, bóng đá và các giải thi đấu nội bộ.",
        "public_description": "Sân chơi thể thao năng động giúp sinh viên giải tỏa căng thẳng sau giờ học.",
        "privacy": GroupPrivacy.public,
    },
]

DEMO_ACTIVITIES = [
    {
        "title": "Job Fair 2026: Ngày Hội Việc Làm & Thực Tập Công Nghệ BK Career",
        "description": "Ngày hội việc làm quy tụ hơn 30 doanh nghiệp công nghệ hàng đầu, mang đến cơ hội thực tập và việc làm chính thức.",
        "category": "Career",
        "meeting_location": "Sảnh Trung tâm Hội nghị & Triển lãm Long Khánh",
        "offset_days": 2,
        "duration_hours": 8,
        "max_participants": 250,
        "offset_lat": 0.002,
        "offset_lng": 0.003,
        "trophy_name": "Chứng nhận Tham dự Ngày Hội Việc Làm Tech Career 2026",
        "trophy_desc": "Dành tặng sinh viên tham gia đầy đủ phỏng vấn và kết nối doanh nghiệp.",
    },
    {
        "title": "Hội thảo Xu hướng Trí tuệ Nhân tạo & Kỹ sư AI 2026",
        "description": "Hội thảo chuyên sâu cùng chuyên gia đầu ngành trong lĩnh vực AI & Data Science. Khám phá LLM và Generative AI.",
        "category": "Workshop",
        "meeting_location": "Hội trường A - Khuôn viên Đào tạo Công nghệ",
        "offset_days": 1,
        "duration_hours": 3.5,
        "max_participants": 120,
        "offset_lat": -0.001,
        "offset_lng": 0.002,
        "trophy_name": "Chứng chỉ Chuyên đề Trí tuệ Nhân tạo 2026",
        "trophy_desc": "Chứng nhận hoàn thành chuyên đề học thuật xu hướng Trí tuệ Nhân tạo 2026.",
    },
    {
        "title": "Hội thảo Kỹ năng Phỏng vấn & Chinh phục Nhà tuyển dụng Đa quốc gia",
        "description": "Workshop chia sẻ kinh nghiệm viết CV chuẩn ATS và kỹ thuật trả lời phỏng vấn theo phương pháp STAR.",
        "category": "Career",
        "meeting_location": "Phòng Hội thảo B2 - Tòa nhà Khởi nghiệp",
        "offset_days": 3,
        "duration_hours": 3,
        "max_participants": 80,
        "offset_lat": 0.003,
        "offset_lng": -0.001,
        "trophy_name": "Chứng chỉ Kỹ năng Phỏng vấn Tuyển dụng Quốc tế",
        "trophy_desc": "Hoàn thành khóa huấn luyện kỹ năng phỏng vấn chuyên nghiệp.",
    },
    {
        "title": "Hackathon Sinh viên: Phát triển Ứng dụng AI Thông minh",
        "description": "Cuộc thi lập trình marathon 24 giờ sáng tạo giải pháp AI phục vụ đời sống học đường và cộng đồng.",
        "category": "Study",
        "meeting_location": "Không gian Đổi mới Sáng tạo Innovation Hub",
        "offset_days": 4,
        "duration_hours": 12,
        "max_participants": 100,
        "offset_lat": -0.002,
        "offset_lng": -0.003,
        "trophy_name": "Kỷ niệm chương Hackathon AI Innovation 2026",
        "trophy_desc": "Dành tặng các đội thi hoàn thành xuất sắc sản phẩm trong Hackathon.",
    },
    {
        "title": "Workshop Luyện kỹ năng Thuyết trình & Làm chủ Sân khấu",
        "description": "Học cách kiểm soát giọng nói, ngôn ngữ hình thể và xây dựng slide thuyết trình cuốn hút người nghe.",
        "category": "Workshop",
        "meeting_location": "Phòng Đa năng C3",
        "offset_days": 1,
        "duration_hours": 2.5,
        "max_participants": 50,
        "offset_lat": 0.001,
        "offset_lng": -0.002,
    },
    {
        "title": "Giao lưu Tiếng Anh chủ đề: Future Tech & Student Life",
        "description": "English Speaking Club buổi tối, thảo luận cởi mở bằng tiếng Anh về công nghệ tương lai và đời sống sinh viên.",
        "category": "Study",
        "meeting_location": "Cà phê Sách Sinh Viên - Góc Sáng Tạo",
        "offset_days": 2,
        "duration_hours": 2,
        "max_participants": 35,
        "offset_lat": -0.003,
        "offset_lng": 0.001,
    },
    {
        "title": "Giải Giao hữu Cầu lông Sinh viên Mở rộng",
        "description": "Thi đấu giao lưu cầu lông đôi nam và đôi nữ, rèn luyện thể lực và kết nối các khoa.",
        "category": "Sports",
        "meeting_location": "Nhà Thi đấu Đa năng Khu liên hợp Thể thao",
        "offset_days": 2,
        "duration_hours": 4,
        "max_participants": 40,
        "offset_lat": 0.004,
        "offset_lng": 0.004,
    },
    {
        "title": "Buổi Ôn tập & Giải đề Giải tích 2 Cùng Đội trợ giảng",
        "description": "Hệ thống hóa kiến thức chuỗi số, tích phân suy rộng và giải bài tập đề thi các năm trước.",
        "category": "Study",
        "meeting_location": "Giảng đường H1 - Phòng 302",
        "offset_days": 1,
        "duration_hours": 2.5,
        "max_participants": 60,
        "offset_lat": 0.001,
        "offset_lng": 0.001,
    },
    {
        "title": "Đêm Nhạc Acoustic Sinh viên: Giai Điệu Mùa Thu",
        "description": "Đêm nhạc mộc mạc do CLB Guitar biểu diễn, không gian giao lưu âm nhạc ấm cúng và thư giãn.",
        "category": "Social",
        "meeting_location": "Sân khấu Ngoài trời Khuôn viên Trung tâm",
        "offset_days": 3,
        "duration_hours": 3,
        "max_participants": 150,
        "offset_lat": -0.002,
        "offset_lng": 0.003,
    },
    {
        "title": "Buổi Chiều Board Game Chiến Thuật & Kết Nối Bạn Mới",
        "description": "Cùng chơi Catan, Avalon, Exploding Kittens và Ma Sói. Cơ hội tuyệt vời để kết thêm bạn bè mới.",
        "category": "Social",
        "meeting_location": "Không gian Sinh hoạt Chung Tầng 2 Thư viện",
        "offset_days": 4,
        "duration_hours": 3,
        "max_participants": 30,
        "offset_lat": 0.002,
        "offset_lng": -0.003,
    },
]


async def seed_demo_database(db: AsyncSession) -> dict:
    """Populates users, groups, upcoming activities and trophies for production demo."""
    # 1. Seed or update demo users
    user_records = {}
    for u_data in DEMO_USERS:
        stmt = select(User).where(User.email == u_data["email"])
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            user = User(
                id=uuid.uuid4(),
                email=u_data["email"],
                username=u_data["username"],
                full_name=u_data["full_name"],
                password_hash=hash_password(u_data["password"]),
                role=u_data["role"],
                university=u_data["university"],
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            await db.flush()
        else:
            user.password_hash = hash_password(u_data["password"])
            user.role = u_data["role"]
            user.is_active = True
        user_records[u_data["email"]] = user

    # 2. Seed groups
    owner_user = user_records["club_lead@uniconnect.vn"]
    group_records = []
    for g_data in DEMO_GROUPS:
        stmt = select(Group).where(Group.name == g_data["name"])
        res = await db.execute(stmt)
        group = res.scalar_one_or_none()
        if not group:
            group = Group(
                id=uuid.uuid4(),
                name=g_data["name"],
                description=g_data["description"],
                public_description=g_data["public_description"],
                privacy=g_data["privacy"],
                status="active",
                owner_id=owner_user.id,
                allow_member_activities=True,
                require_approval=True,
            )
            db.add(group)
            await db.flush()
        group_records.append(group)

    # 3. Seed activities
    now = datetime.now(LOCAL_TZ)
    created_activities_count = 0
    created_trophies_count = 0

    all_hosts = list(user_records.values())

    for idx, item in enumerate(DEMO_ACTIVITIES):
        host = all_hosts[idx % len(all_hosts)]
        grp = group_records[idx % len(group_records)] if group_records and idx % 2 == 0 else None

        # Calculate dynamic start_time based on now
        start_dt = now.replace(minute=0, second=0, microsecond=0) + timedelta(days=item["offset_days"], hours=idx % 4 + 9)
        end_dt = start_dt + timedelta(hours=item["duration_hours"])

        act_id = uuid.uuid4()
        lat = USER_LAT + item["offset_lat"]
        lng = USER_LNG + item["offset_lng"]
        point_wkt = f"SRID=4326;POINT({lng} {lat})"

        embed_text = f"{item['title']} {item['description']} {item['category']} {item['meeting_location']}"
        embedding_val = generate_embedding(embed_text)

        activity = Activity(
            id=act_id,
            host_id=host.id,
            group_id=grp.id if grp else None,
            title=item["title"],
            description=item["description"],
            category=item["category"],
            meeting_location=item["meeting_location"],
            marker_location=point_wkt,
            embedding=embedding_val,
            start_time=start_dt,
            end_time=end_dt,
            max_participants=item["max_participants"],
            current_participants=1,
            privacy=ActivityPrivacy.public,
            require_approval=False,
            social_work_days=None,
            attendance_mode="qr" if "trophy_name" in item else "manual",
            check_in_radius=300,
        )
        db.add(activity)
        created_activities_count += 1

        if "trophy_name" in item:
            trophy = Trophy(
                id=uuid.uuid4(),
                activity_id=act_id,
                name=item["trophy_name"],
                description=item["trophy_desc"],
            )
            db.add(trophy)
            created_trophies_count += 1

    await db.commit()

    return {
        "status": "success",
        "message": "Demo data successfully seeded for production testing!",
        "seeded_users": len(DEMO_USERS),
        "seeded_groups": len(DEMO_GROUPS),
        "seeded_activities": created_activities_count,
        "seeded_trophies": created_trophies_count,
        "test_accounts": [
            {"email": "admin@uniconnect.vn", "password": "admin123", "role": "admin"},
            {"email": "student1@uniconnect.vn", "password": "password123", "role": "student"},
            {"email": "student2@uniconnect.vn", "password": "password123", "role": "student"},
            {"email": "club_lead@uniconnect.vn", "password": "password123", "role": "edu_org"},
        ],
    }
