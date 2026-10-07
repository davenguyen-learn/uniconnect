"""
Seed 20 regular upcoming activities from current date (2026-10-07) to 4 days ahead (2026-10-11).
- No CTXH (social_work_days = None).
- Exactly 4 activities with trophies (Hội thảo, Job fair, Diễn đàn...).
- Diverse categories: Career, Workshop, Study, Sports, Social, Gaming, Music.
- Realistic locations around Long Khanh / Campus.
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone, time
from zoneinfo import ZoneInfo
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings
from app.modules.users.models import User
from app.modules.groups.models import Group
from app.modules.activities.models import Activity, ActivityPrivacy
from app.modules.trophies.models import Trophy
from app.modules.chat.embeddings import generate_embedding

try:
    LOCAL_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
except Exception:
    LOCAL_TZ = timezone(timedelta(hours=7))

USER_LAT = 10.929718
USER_LNG = 107.250381

ACTIVITIES_DATA = [
    # ── 4 HOẠT ĐỘNG CÓ DANH HIỆU (JOB FAIR, HỘI THẢO, DIỄN ĐÀN) ──
    {
        "title": "Job Fair 2026: Ngày Hội Việc Làm & Thực Tập Công Nghệ BK Tech Career",
        "description": "Ngày hội việc làm quy mô lớn quy tụ hơn 30 doanh nghiệp công nghệ hàng đầu, mang đến hàng trăm cơ hội thực tập và việc làm chính thức cho sinh viên. Tham gia phỏng vấn trực tiếp tại gian hàng và nhận tư vấn hồ sơ CV miễn phí từ chuyên gia tuyển dụng.",
        "category": "Career",
        "meeting_location": "Sảnh Trung tâm Hội nghị & Triển lãm Long Khánh",
        "start_time": datetime(2026, 10, 9, 8, 0, tzinfo=LOCAL_TZ),
        "end_time": datetime(2026, 10, 9, 16, 30, tzinfo=LOCAL_TZ),
        "max_participants": 250,
        "offset_lat": 0.002,
        "offset_lng": 0.003,
        "trophy_name": "Chứng nhận Tham dự Ngày Hội Việc Làm Tech Career 2026",
        "trophy_desc": "Dành tặng sinh viên tham gia đầy đủ các hoạt động phỏng vấn và kết nối doanh nghiệp tại BK Job Fair 2026.",
    },
    {
        "title": "Hội thảo Xu hướng Trí tuệ Nhân tạo & Định hướng Kỹ sư AI 2026",
        "description": "Hội thảo chuyên sâu cùng các chuyên gia đầu ngành trong lĩnh vực AI & Data Science. Khám phá các công nghệ mô hình ngôn ngữ lớn (LLM), Generative AI và lộ trình phát triển kỹ năng thực chiến cho sinh viên CNTT.",
        "category": "Workshop",
        "meeting_location": "Hội trường A - Khuôn viên Đào tạo Công nghệ",
        "start_time": datetime(2026, 10, 8, 13, 30, tzinfo=LOCAL_TZ),
        "end_time": datetime(2026, 10, 8, 17, 0, tzinfo=LOCAL_TZ),
        "max_participants": 120,
        "offset_lat": -0.001,
        "offset_lng": 0.002,
        "trophy_name": "Chứng chỉ Chuyên đề Trí tuệ Nhân tạo & AI Engineering 2026",
        "trophy_desc": "Chứng nhận hoàn thành chuyên đề học thuật xu hướng công nghệ Trí tuệ Nhân tạo 2026.",
    },
    {
        "title": "Hội thảo Kỹ năng Phỏng vấn & Chinh phục Nhà tuyển dụng Đa quốc gia",
        "description": "Chia sẻ kinh nghiệm thực tế từ Giám đốc Nhân sự (HRD) các tập đoàn đa quốc gia. Hướng dẫn cách xử lý các câu hỏi tình huống hóc búa, kỹ năng đàm phán lương và phong thái tự tin trong các vòng phỏng vấn hành vi (Behavioral Interview).",
        "category": "Workshop",
        "meeting_location": "Phòng Hội thảo Tầng 3 - Tòa nhà Khởi nghiệp",
        "start_time": datetime(2026, 10, 10, 8, 30, tzinfo=LOCAL_TZ),
        "end_time": datetime(2026, 10, 10, 11, 30, tzinfo=LOCAL_TZ),
        "max_participants": 80,
        "offset_lat": 0.003,
        "offset_lng": -0.001,
        "trophy_name": "Chứng nhận Kỹ năng Phỏng vấn Tuyển dụng & Bản lĩnh Ứng viên 2026",
        "trophy_desc": "Vinh danh sinh viên hoàn thành xuất sắc khóa huấn luyện phỏng vấn tuyển dụng chuyên nghiệp.",
    },
    {
        "title": "BK Innovation Forum 2026: Diễn đàn Đổi mới Sáng tạo & Khởi nghiệp Trẻ",
        "description": "Diễn đàn kết nối các dự án khởi nghiệp sáng tạo của sinh viên với các quỹ đầu tư thiên thần và vườn ươm doanh nghiệp. Lắng nghe các bài thuyết trình gọi vốn (Pitching) gay cấn và học hỏi tư duy khởi nghiệp đột phá.",
        "category": "Study",
        "meeting_location": "Hội trường Lớn Đổi mới Sáng tạo Long Khánh",
        "start_time": datetime(2026, 10, 11, 13, 30, tzinfo=LOCAL_TZ),
        "end_time": datetime(2026, 10, 11, 17, 30, tzinfo=LOCAL_TZ),
        "max_participants": 150,
        "offset_lat": -0.002,
        "offset_lng": -0.003,
        "trophy_name": "Chứng nhận Tham dự BK Innovation Forum 2026",
        "trophy_desc": "Chứng nhận tham dự trọn vẹn Diễn đàn Khởi nghiệp & Đổi mới Sáng tạo Sinh viên 2026.",
    },

    # ── 16 HOẠT ĐỘNG THƯỜNG KHÔNG CÓ CTXH RẢI RÁC 07/10 - 11/10 ──
    # Ngày 07/10 (Hôm nay - Thứ 4)
    {
        "title": "Giao lưu Bóng rổ 3x3 Sinh viên Gắn kết Chiều Thứ 4",
        "description": "Giao lưu thi đấu bóng rổ nửa sân 3x3 phong trào. Hoạt động mở cho tất cả sinh viên đam mê trái bóng cam, rèn luyện thể lực và kết nối bạn bè sau giờ lên lớp.",
        "category": "Sports",
        "meeting_location": "Sân Bóng rổ Ngoài trời Trung tâm TDTT Long Khánh",
        "start_time": datetime(2026, 10, 7, 16, 30, tzinfo=LOCAL_TZ),
        "end_time": datetime(2026, 10, 7, 18, 30, tzinfo=LOCAL_TZ),
        "max_participants": 24,
        "offset_lat": 0.001,
        "offset_lng": 0.001,
    },
    {
        "title": "Buổi Ôn tập & Thảo luận Nhóm: Giải tích 1 & Đại số Tuyến tính",
        "description": "Học nhóm hỗ trợ nhau giải đề thi giữa kỳ các năm trước, ôn tập kỹ thuật tính tích phân suy rộng và ma trận nghịch đảo. Cùng nhau vượt qua kỳ thi với điểm số cao!",
        "category": "Study",
        "meeting_location": "Phòng Tự học Không gian Yên tĩnh - Thư viện",
        "start_time": datetime(2026, 10, 7, 19, 30, tzinfo=LOCAL_TZ),
        "end_time": datetime(2026, 10, 7, 21, 30, tzinfo=LOCAL_TZ),
        "max_participants": 18,
        "offset_lat": 0.002,
        "offset_lng": -0.002,
    },
    {
        "title": "Đêm Nhạc Acoustic & Giao lưu Đàn Guitar Sinh viên Bách Khoa",
        "description": "Đêm nhạc mộc ấm cúng cùng những giai điệu acoustic trẻ trung. Không gian mở để các bạn sinh viên thể hiện giọng hát, tài năng đánh đàn guitar và chuyện trò thư giãn.",
        "category": "Music",
        "meeting_location": "Quán Cà phê Sinh viên Giai Điệu Xanh",
        "start_time": datetime(2026, 10, 7, 20, 0, tzinfo=LOCAL_TZ),
        "end_time": datetime(2026, 10, 7, 22, 0, tzinfo=LOCAL_TZ),
        "max_participants": 35,
        "offset_lat": -0.003,
        "offset_lng": 0.001,
    },

    # Ngày 08/10 (Ngày mai - Thứ 5)
    {
        "title": "Buổi Chạy bộ Buổi sáng Rèn luyện Thể lực Quanh Công viên",
        "description": "Thức dậy sớm đón bình minh và khởi động ngày mới tràn đầy năng lượng cùng cự ly chạy bộ nhẹ nhàng 3km - 5km quanh công viên rợp bóng cây xanh.",
        "category": "Sports",
        "meeting_location": "Cổng chính Công viên Cây xanh Long Khánh",
        "start_time": datetime(2026, 10, 8, 6, 0, tzinfo=LOCAL_TZ),
        "end_time": datetime(2026, 10, 8, 7, 30, tzinfo=LOCAL_TZ),
        "max_participants": 30,
        "offset_lat": 0.004,
        "offset_lng": 0.002,
    },
    {
        "title": "Học nhóm & Trao đổi Kỹ năng Lập trình C++ Nâng cao",
        "description": "Thảo luận về con trỏ thông minh (Smart Pointers), cấu trúc dữ liệu Template và lập trình hướng đối tượng chuyên sâu trong C++ phục vụ môn Lập trình Nâng cao.",
        "category": "Study",
        "meeting_location": "Phòng Lab Máy tính 204",
        "start_time": datetime(2026, 10, 8, 9, 0, tzinfo=LOCAL_TZ),
        "end_time": datetime(2026, 10, 8, 11, 30, tzinfo=LOCAL_TZ),
        "max_participants": 25,
        "offset_lat": -0.001,
        "offset_lng": -0.002,
    },
    {
        "title": "Giao lưu Cầu lông Đơn Nam / Đơn Nữ Phong trào Chiều Thứ 5",
        "description": "Sân chơi cầu lông giao hữu thể thao phong trào. Rèn luyện phản xạ, độ dẻo dai và kết nối các bạn có chung niềm đam mê với bộ môn cầu lông.",
        "category": "Sports",
        "meeting_location": "Sân Cầu lông Thể Thao Tuổi Trẻ",
        "start_time": datetime(2026, 10, 8, 17, 0, tzinfo=LOCAL_TZ),
        "end_time": datetime(2026, 10, 8, 19, 0, tzinfo=LOCAL_TZ),
        "max_participants": 20,
        "offset_lat": 0.003,
        "offset_lng": 0.003,
    },
    {
        "title": "Board Game Night: Giao lưu Ma Sói & Catan Xả Stress Giữa Tuần",
        "description": "Buổi tối giải trí hấp dẫn với các tựa game trí tuệ Ma Sói, Catan, Bang, Dixit. Cơ hội tuyệt vời để rèn luyện tư duy logic, kỹ năng thuyết phục và làm quen bạn mới.",
        "category": "Gaming",
        "meeting_location": "Không gian Trải nghiệm Board Game Club",
        "start_time": datetime(2026, 10, 8, 19, 30, tzinfo=LOCAL_TZ),
        "end_time": datetime(2026, 10, 8, 22, 0, tzinfo=LOCAL_TZ),
        "max_participants": 30,
        "offset_lat": -0.002,
        "offset_lng": 0.001,
    },

    # Ngày 09/10 (Thứ 6)
    {
        "title": "Buổi Chia sẻ Kỹ năng Viết Báo cáo & Trình bày Slide Thuyết trình Chuyên nghiệp",
        "description": "Thực hành thiết kế slide thuyết trình ấn tượng trên Canva/PowerPoint và kỹ năng cấu trúc bài báo cáo khoa học mạch lạc, thu hút sự chú ý của giảng viên và hội đồng.",
        "category": "Study",
        "meeting_location": "Phòng Đa năng Tầng 2 - Trung tâm Sinh viên",
        "start_time": datetime(2026, 10, 9, 9, 30, tzinfo=LOCAL_TZ),
        "end_time": datetime(2026, 10, 9, 11, 30, tzinfo=LOCAL_TZ),
        "max_participants": 40,
        "offset_lat": 0.001,
        "offset_lng": -0.003,
    },
    {
        "title": "Trận Bóng đá Giao hữu 7 người: K22 Cơ khí vs K22 Khoa học Máy tính",
        "description": "Trận cầu giao lưu bóng đá sân 7 đầy kịch tính giữa hai khoa. Khuyến khích tinh thần thể thao cao thượng, rèn luyện sức bền và gắn kết tình đồng môn.",
        "category": "Sports",
        "meeting_location": "Sân Bóng đá Cỏ nhân tạo Long Khánh",
        "start_time": datetime(2026, 10, 9, 17, 0, tzinfo=LOCAL_TZ),
        "end_time": datetime(2026, 10, 9, 19, 0, tzinfo=LOCAL_TZ),
        "max_participants": 22,
        "offset_lat": -0.004,
        "offset_lng": 0.002,
    },
    {
        "title": "Coffee Talk: Định hướng Chuyên ngành & Chọn Hướng Đi Năm 3-4",
        "description": "Buổi trò chuyện thân mật bên ly cà phê cùng các anh chị sinh viên khóa trên và cựu sinh viên đi làm. Cùng giải đáp các thắc mắc về hướng chuyên ngành, đồ án và định hướng nghề nghiệp.",
        "category": "Social",
        "meeting_location": "The Coffee House Chi nhánh Long Khánh",
        "start_time": datetime(2026, 10, 9, 19, 0, tzinfo=LOCAL_TZ),
        "end_time": datetime(2026, 10, 9, 21, 0, tzinfo=LOCAL_TZ),
        "max_participants": 25,
        "offset_lat": 0.002,
        "offset_lng": 0.001,
    },
    {
        "title": "Giao lưu Cờ vua & Cờ tướng Phong trào Sinh viên Cuối tuần",
        "description": "Giao lưu thi đấu cờ vua, cờ tướng cọ xát tư duy chiến thuật. Phù hợp cho cả những bạn mới tập chơi lẫn những kỳ thủ muốn tìm bạn so tài.",
        "category": "Gaming",
        "meeting_location": "Khu sinh hoạt chung Nhà văn hóa Thanh niên",
        "start_time": datetime(2026, 10, 9, 19, 30, tzinfo=LOCAL_TZ),
        "end_time": datetime(2026, 10, 9, 21, 30, tzinfo=LOCAL_TZ),
        "max_participants": 20,
        "offset_lat": -0.002,
        "offset_lng": -0.001,
    },

    # Ngày 10/10 (Thứ 7 - Cuối tuần)
    {
        "title": "Hội thảo Chia sẻ Kinh nghiệm Làm Đồ án Tốt nghiệp & Khóa luận Xuất sắc",
        "description": "Phương pháp lựa chọn đề tài nghiên cứu, tìm kiếm tài liệu học thuật uy tín trên IEEE/ScienceDirect và quản lý thời gian để hoàn thành đồ án đúng hạn với kết quả xuất sắc.",
        "category": "Study",
        "meeting_location": "Hội trường B2 - Tòa nhà Công nghệ",
        "start_time": datetime(2026, 10, 10, 8, 30, tzinfo=LOCAL_TZ),
        "end_time": datetime(2026, 10, 10, 11, 30, tzinfo=LOCAL_TZ),
        "max_participants": 70,
        "offset_lat": 0.003,
        "offset_lng": 0.002,
    },
    {
        "title": "Giải Bóng bàn Đơn Nam Giao lưu Mở rộng Sinh viên BK 2026",
        "description": "Giải thi đấu bóng bàn giao hữu phong trào theo thể thức loại trực tiếp. Trao đổi kỹ thuật cầm vợt, giao bóng xoáy và rèn luyện thể lực cuối tuần.",
        "category": "Sports",
        "meeting_location": "Nhà Thi đấu Thể thao Đa năng",
        "start_time": datetime(2026, 10, 10, 14, 0, tzinfo=LOCAL_TZ),
        "end_time": datetime(2026, 10, 10, 17, 0, tzinfo=LOCAL_TZ),
        "max_participants": 24,
        "offset_lat": -0.001,
        "offset_lng": 0.003,
    },
    {
        "title": "Workshop Thực hành Chụp ảnh & Chỉnh sửa Ảnh Bằng Điện thoại Thông minh",
        "description": "Khám phá quy tắc bố cục 1/3, làm chủ ánh sáng và chỉnh sửa màu sắc chuyên nghiệp bằng ứng dụng Lightroom Mobile để tạo nên những bức ảnh ấn tượng.",
        "category": "Social",
        "meeting_location": "Phòng Triển lãm Nghệ thuật Sinh viên",
        "start_time": datetime(2026, 10, 10, 15, 0, tzinfo=LOCAL_TZ),
        "end_time": datetime(2026, 10, 10, 17, 30, tzinfo=LOCAL_TZ),
        "max_participants": 35,
        "offset_lat": 0.002,
        "offset_lng": -0.003,
    },
    {
        "title": "Giải Đấu Thể thao Điện tử Esports Liên Minh Huyền Thoại Phong trào T7",
        "description": "Giải đấu giao hữu LMHT 5v5 dành cho các team sinh viên. Thi đấu giao lưu vui vẻ, rèn luyện tinh thần đồng đội và chiến thuật phối hợp ăn ý.",
        "category": "Gaming",
        "meeting_location": "Cyber Game Stadium Long Khánh",
        "start_time": datetime(2026, 10, 10, 18, 30, tzinfo=LOCAL_TZ),
        "end_time": datetime(2026, 10, 10, 21, 30, tzinfo=LOCAL_TZ),
        "max_participants": 40,
        "offset_lat": -0.003,
        "offset_lng": 0.002,
    },

    # Ngày 11/10 (Chủ nhật - Cuối tuần)
    {
        "title": "Giao lưu Đạp xe Rèn luyện Thể chất & Khám phá Ngoại ô Sáng Chủ nhật",
        "description": "Chuyến đạp xe dã ngoại cự ly 15km khám phá cảnh đẹp ngoại ô Long Khánh. Không khí trong lành, vận động rèn luyện tim mạch và nạp lại năng lượng cho tuần mới.",
        "category": "Sports",
        "meeting_location": "Điểm hẹn Vòng xoay Cổng chào Long Khánh",
        "start_time": datetime(2026, 10, 11, 6, 0, tzinfo=LOCAL_TZ),
        "end_time": datetime(2026, 10, 11, 9, 0, tzinfo=LOCAL_TZ),
        "max_participants": 30,
        "offset_lat": 0.004,
        "offset_lng": -0.001,
    },
]

import sys
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

async def seed_upcoming_activities():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session = async_sessionmaker(engine, expire_on_commit=False)

    async with session() as db:
        print("[INFO] Kiem tra nguoi dung va cau lac bo...")
        users = (await db.execute(select(User))).unique().scalars().all()
        if not users:
            print("[ERROR] Khong tim thay user nao trong co so du lieu!")
            return

        groups = (await db.execute(select(Group))).unique().scalars().all()
        host_pool = [u for u in users if u.role in ("student", "edu_org", "admin")]
        if not host_pool:
            host_pool = users

        print(f"[INFO] Co {len(host_pool)} host hop le va {len(groups)} cau lac bo.")
        print(f"[INFO] Bat dau them {len(ACTIVITIES_DATA)} hoat dong moi (07/10 - 11/10)...")

        created_activities = []
        created_trophies = []

        for idx, item in enumerate(ACTIVITIES_DATA):
            host = host_pool[idx % len(host_pool)]
            grp = groups[idx % len(groups)] if groups and idx % 2 == 0 else None

            act_id = uuid.uuid4()
            lat = USER_LAT + item["offset_lat"]
            lng = USER_LNG + item["offset_lng"]
            point_wkt = f"SRID=4326;POINT({lng} {lat})"

            # Generate embedding for AI semantic search
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
                start_time=item["start_time"],
                end_time=item["end_time"],
                max_participants=item["max_participants"],
                current_participants=1,
                privacy=ActivityPrivacy.public,
                require_approval=False,
                social_work_days=None,  # HOẠT ĐỘNG THƯỜNG - KHÔNG CÓ CTXH
                attendance_mode="qr" if "trophy_name" in item else "manual",
                check_in_radius=300,
            )
            db.add(activity)
            created_activities.append(activity)

            # If activity has a trophy, create Trophy record
            if "trophy_name" in item:
                trophy = Trophy(
                    id=uuid.uuid4(),
                    activity_id=act_id,
                    name=item["trophy_name"],
                    description=item["trophy_desc"],
                )
                db.add(trophy)
                created_trophies.append(trophy)

        await db.commit()
        print(f"[SUCCESS] Da them thanh cong {len(created_activities)} hoat dong moi!")
        print(f"[SUCCESS] Da gan {len(created_trophies)} danh hieu moi vao cac hoat dong hoi thao/job fair!")
        for t in created_trophies:
            print(f"   * Danh hieu: '{t.name}' (Activity ID: {t.activity_id})")

if __name__ == "__main__":
    asyncio.run(seed_upcoming_activities())
