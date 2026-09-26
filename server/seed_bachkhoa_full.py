"""
Seed script: Nạp đầy đủ dữ liệu thực tế khuôn viên Trường ĐH Bách Khoa TP.HCM (Cơ sở 1 & Cơ sở 2)
Bao gồm: Users, Groups, Trophies, Busy Slots, Activities (CTXH, Thể thao, Học thuật) kèm Vector Embedding (pgvector).
"""

import asyncio
import datetime
import uuid
import io
import sys
from datetime import timezone, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.modules.users.models import User, UserRole
from app.modules.groups.models import Group, GroupMember, GroupRole
from app.modules.activities.models import Activity, ActivityPrivacy
from app.modules.trophies.models import Trophy, UserTrophy
from app.modules.calendar.models import UserBusySlot, RecurrenceType
from app.modules.chat.embeddings import generate_embedding

# Tọa độ Bách Khoa CS1 (268 Lý Thường Kiệt, Q.10) & CS2 (Dĩ An, Bình Dương)
BK_CS1_LAT, BK_CS1_LNG = 10.7725, 106.6578
BK_CS2_LAT, BK_CS2_LNG = 10.8800, 106.8057

async def seed_bachkhoa():
    print("🚀 BẮT ĐẦU SEED DỮ LIỆU ĐẠI HỌC BÁCH KHOA...")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    now = datetime.datetime.now(timezone.utc)

    async with async_session() as db:
        # 1. Clear existing activities, trophies, busy slots to ensure fresh consistent data
        print("🧹 Làm sạch dữ liệu hoạt động cũ...")
        for tbl in ["join_requests", "activity_cohosts", "user_trophies", "trophies", "activities", "user_busy_slots"]:
            try:
                await db.execute(text(f"DELETE FROM {tbl}"))
                await db.commit()
            except Exception as e:
                await db.rollback()

        # 2. Tạo hoặc lấy Users
        print("👤 Kiểm tra và khởi tạo người dùng Bách Khoa...")
        admin = User(
            id=uuid.uuid4(),
            email="admin@hcmut.edu.vn",
            username="admin_bk",
            full_name="Ban Quản trị UniConnect HCMUT",
            password_hash=hash_password("admin123"),
            role=UserRole.admin,
            university="Đại học Bách khoa TP.HCM",
            is_active=True,
            is_verified=True,
        )
        org_ctxh = User(
            id=uuid.uuid4(),
            email="ctxh@hcmut.edu.vn",
            username="ban_ctxh_bk",
            full_name="Ban Công tác Xã hội ĐH Bách Khoa",
            password_hash=hash_password("ctxh123"),
            role=UserRole.edu_org,
            university="Đại học Bách khoa TP.HCM",
            is_active=True,
            is_verified=True,
        )
        student_dat = User(
            id=uuid.uuid4(),
            email="dat.nguyen@hcmut.edu.vn",
            username="dat_nguyen",
            full_name="Nguyễn Đức Đạt",
            password_hash=hash_password("dat123"),
            role=UserRole.student,
            university="Đại học Bách khoa TP.HCM",
            interests=["machine learning", "web development", "cầu lông", "tình nguyện"],
            is_active=True,
            is_verified=True,
        )
        db.add_all([admin, org_ctxh, student_dat])
        await db.commit()
        await db.refresh(admin)
        await db.refresh(org_ctxh)
        await db.refresh(student_dat)

        # 3. Tạo Groups
        print("👥 Khởi tạo các Đội / Nhóm Bách Khoa...")
        grp_doan = Group(
            id=uuid.uuid4(),
            owner_id=admin.id,
            name="Đoàn Khoa Khoa học và Kỹ thuật Máy tính",
            description="Kênh thông tin chính thức của Đoàn - Hội Khoa KH&KT Máy tính ĐH Bách Khoa",
            privacy="public",
            allow_member_activities=True,
        )
        grp_bec = Group(
            id=uuid.uuid4(),
            owner_id=student_dat.id,
            name="CLB Tiếng Anh Bách Khoa (BEC HCMUT)",
            description="Câu lạc bộ Tiếng Anh giao tiếp và học thuật sinh viên Bách Khoa",
            privacy="public",
            allow_member_activities=True,
        )
        grp_sports = Group(
            id=uuid.uuid4(),
            owner_id=student_dat.id,
            name="CLB Thể thao & Cầu lông Bách Khoa",
            description="Nơi giao lưu cầu lông, bóng đá, bóng rổ cho sinh viên sau giờ học",
            privacy="public",
            allow_member_activities=True,
        )
        db.add_all([grp_doan, grp_bec, grp_sports])
        await db.commit()
        await db.refresh(grp_doan)
        await db.refresh(grp_bec)
        await db.refresh(grp_sports)

        # 4. Tạo Trophies
        print("🏆 Khởi tạo Huy hiệu danh dự (Trophies)...")
        t_green = Trophy(
            id=uuid.uuid4(),
            name="Hiệp sĩ Ngày Chủ Nhật Xanh",
            description="Hoàn thành xuất sắc hoạt động dọn dẹp và cải tạo cảnh quan campus",
        )
        t_hack = Trophy(
            id=uuid.uuid4(),
            name="Quán quân Hackathon Bách Khoa",
            description="Đạt giải thưởng tại cuộc thi lập trình đổi mới sáng tạo",
        )
        t_blood = Trophy(
            id=uuid.uuid4(),
            name="Giọt Hồng Bách Khoa",
            description="Tham gia hiến máu tình nguyện cứu người",
        )
        db.add_all([t_green, t_hack, t_blood])
        await db.commit()

        # 5. Tạo Thời khóa biểu / Lịch bận sinh viên
        print("📅 Khởi tạo Lịch bận sinh viên (Smart Calendar)...")
        busy_slots = [
            UserBusySlot(
                id=uuid.uuid4(),
                user_id=student_dat.id,
                title="Lịch học Giải tích 1 (A4-201)",
                recurrence=RecurrenceType.weekly.value,
                day_of_week=0,  # Thứ 2
                start_time_of_day=datetime.time(7, 30),
                end_time_of_day=datetime.time(11, 30),
            ),
            UserBusySlot(
                id=uuid.uuid4(),
                user_id=student_dat.id,
                title="Thực hành Cấu trúc dữ liệu (H6-402)",
                recurrence=RecurrenceType.weekly.value,
                day_of_week=2,  # Thứ 4
                start_time_of_day=datetime.time(13, 0),
                end_time_of_day=datetime.time(17, 0),
            ),
            UserBusySlot(
                id=uuid.uuid4(),
                user_id=student_dat.id,
                title="Lịch học Tiếng Anh B4-301",
                recurrence=RecurrenceType.weekly.value,
                day_of_week=4,  # Thứ 6
                start_time_of_day=datetime.time(8, 0),
                end_time_of_day=datetime.time(11, 0),
            ),
        ]
        db.add_all(busy_slots)
        await db.commit()

        # 6. Danh sách 20 Hoạt động chuẩn thực tế Bách Khoa
        print("🎯 Khởi tạo và Vector hóa các Hoạt động Bách Khoa...")
        raw_activities = [
            # Tình nguyện & CTXH
            {
                "title": "Chiến dịch Tình nguyện Ngày Chủ Nhật Xanh - Dọn dẹp cảnh quan Cơ sở 2",
                "desc": "Tham gia quét dọn vệ sinh, trồng cây xanh và phân loại rác thải tại khuôn viên Ký túc xá và Tòa nhà H6 Bách Khoa Cơ sở 2. Được cấp 1 ngày CTXH và cấp chứng nhận.",
                "cat": "Volunteer",
                "days": 1.0,
                "lat": BK_CS2_LAT, "lng": BK_CS2_LNG,
                "loc": "Tòa nhà H6 - ĐH Bách Khoa Cơ sở 2 (Dĩ An)",
                "delta_days": 2, "duration_hours": 4,
            },
            {
                "title": "Ngày hội Hiến Máu Tình Nguyện - Giọt Hồng Bách Khoa đợt 1",
                "desc": "Chương trình hiến máu nhân đạo do Hội Chữ thập đỏ và Ban CTXH phối hợp tổ chức tại Sảnh A4 Cơ sở 1. Được cộng 1 ngày CTXH, nhận quà và giấy khen hiến máu.",
                "cat": "Volunteer",
                "days": 1.0,
                "lat": BK_CS1_LAT, "lng": BK_CS1_LNG,
                "loc": "Sảnh A4 - ĐH Bách Khoa Cơ sở 1 (Lý Thường Kiệt)",
                "delta_days": 4, "duration_hours": 5,
            },
            {
                "title": "Chiến dịch Tiếp sức Mùa thi 2026 - Hướng dẫn phụ huynh và thí sinh",
                "desc": "Hỗ trợ thí sinh thi đánh giá năng lực ĐHQG tại cổng trường Bách Khoa, phát nước và hướng dẫn sơ đồ phòng thi. Cấp 1.5 ngày CTXH.",
                "cat": "Volunteer",
                "days": 1.5,
                "lat": BK_CS1_LAT, "lng": BK_CS1_LNG,
                "loc": "Cổng 1 - 268 Lý Thường Kiệt, Q.10",
                "delta_days": 6, "duration_hours": 8,
            },
            {
                "title": "Thu gom và Tái chế Rác thải Điện tử & Pin cũ bảo vệ môi trường",
                "desc": "Điểm thu gom pin hỏng, thiết bị điện tử cũ tại sảnh nhà C5. Sinh viên tham gia phân loại và tuyên truyền môi trường được cấp 0.5 ngày CTXH.",
                "cat": "Volunteer",
                "days": 0.5,
                "lat": BK_CS1_LAT, "lng": BK_CS1_LNG,
                "loc": "Sảnh C5 - ĐH Bách Khoa Cơ sở 1",
                "delta_days": 3, "duration_hours": 3,
            },
            {
                "title": "Tình nguyện viên hỗ trợ Ngày hội Khởi nghiệp Bách Khoa BK-Innovation",
                "desc": "Điều phối hội trường, đón tiếp đại biểu và hỗ trợ các đội thi thuyết trình khởi nghiệp tại Hội trường A5. Cấp 1.0 ngày CTXH.",
                "cat": "Volunteer",
                "days": 1.0,
                "lat": BK_CS1_LAT, "lng": BK_CS1_LNG,
                "loc": "Hội trường A5 - ĐH Bách Khoa Cơ sở 1",
                "delta_days": 5, "duration_hours": 6,
            },
            # Học thuật & Kỹ năng
            {
                "title": "Học nhóm môn Cấu trúc dữ liệu và giải thuật (DSA) tại Thư viện",
                "desc": "Cùng nhau ôn tập cây nhị phân, đồ thị Dijkstra và giải bài tập trên LeetCode/VNOI. Nhóm chào đón sinh viên Khoa Máy tính.",
                "cat": "Study",
                "days": None,
                "lat": BK_CS1_LAT, "lng": BK_CS1_LNG,
                "loc": "Thư viện Bách Khoa A2 - Phòng tự học tầng 2",
                "delta_days": 1, "duration_hours": 3,
            },
            {
                "title": "Cuộc thi Bách Khoa Hackathon 2026: AI for Smart Campus",
                "desc": "Thử thách 24 giờ lập trình xây dựng giải pháp AI ứng dụng trong khuôn viên học đường. Tổng giải thưởng 50 triệu đồng và cúp vinh danh.",
                "cat": "Study",
                "days": None,
                "lat": BK_CS1_LAT, "lng": BK_CS1_LNG,
                "loc": "Hội trường A5 - ĐH Bách Khoa CS1",
                "delta_days": 7, "duration_hours": 24,
            },
            {
                "title": "Workshop Thực chiến Docker, Linux và CI/CD cho sinh viên CNTT",
                "desc": "Hướng dẫn cài đặt Docker container, viết Dockerfile, docker-compose và triển khai ứng dụng lên máy chủ đám mây.",
                "cat": "Study",
                "days": None,
                "lat": BK_CS2_LAT, "lng": BK_CS2_LNG,
                "loc": "Phòng Lab H6-402 - ĐH Bách Khoa Cơ sở 2",
                "delta_days": 3, "duration_hours": 3,
            },
            {
                "title": "Seminar Trí tuệ Nhân tạo: Khám phá LLM và Kiến trúc RAG",
                "desc": "Giới thiệu nguyên lý Retrieval-Augmented Generation, vector embedding với pgvector và xây dựng Chatbot trợ lý học đường.",
                "cat": "Study",
                "days": None,
                "lat": BK_CS2_LAT, "lng": BK_CS2_LNG,
                "loc": "Hội trường H6-501 - ĐH Bách Khoa Cơ sở 2",
                "delta_days": 5, "duration_hours": 2,
            },
            {
                "title": "Ôn tập thi giữa kỳ môn Giải tích 1 và Đại số tuyến tính",
                "desc": "Giải đề thi các năm trước, ôn tập vi phân tích phân nhiều biến và ma trận chéo hóa. Có tài liệu phát miễn phí.",
                "cat": "Study",
                "days": None,
                "lat": BK_CS1_LAT, "lng": BK_CS1_LNG,
                "loc": "Phòng C5-102 - ĐH Bách Khoa CS1",
                "delta_days": 2, "duration_hours": 3,
            },
            {
                "title": "CLB Tiếng Anh BEC: Giao lưu Speaking chủ đề Tech Careers",
                "desc": "Buổi sinh hoạt tiếng Anh định kỳ, luyện phản xạ phỏng vấn và thảo luận xu hướng công nghệ trong môi trường quốc tế.",
                "cat": "Study",
                "days": None,
                "lat": BK_CS1_LAT, "lng": BK_CS1_LNG,
                "loc": "Cà phê Sách Bách Khoa - Cổng 1 Lý Thường Kiệt",
                "delta_days": 4, "duration_hours": 2,
            },
            {
                "title": "Workshop Kỹ năng viết CV chuyên nghiệp và Phỏng vấn IT",
                "desc": "Được hướng dẫn bởi cựu sinh viên Bách Khoa hiện làm Tech Lead tại VNG và FPT. Review CV trực tiếp cho người tham gia.",
                "cat": "Study",
                "days": None,
                "lat": BK_CS1_LAT, "lng": BK_CS1_LNG,
                "loc": "Hội trường B4 - ĐH Bách Khoa CS1",
                "delta_days": 8, "duration_hours": 3,
            },
            # Thể thao & Giải trí
            {
                "title": "Giao hữu Cầu lông Sinh viên Bách Khoa chiều thứ Bảy",
                "desc": "Tìm bạn giao lưu cầu lông đôi nam và đôi nam nữ. Trình độ trung bình khá, sân có máy lạnh và thảm chuyên dụng.",
                "cat": "Sports",
                "days": None,
                "lat": BK_CS1_LAT, "lng": BK_CS1_LNG,
                "loc": "Nhà thi đấu Đa năng Bách Khoa CS1",
                "delta_days": 3, "duration_hours": 2,
            },
            {
                "title": "Giải bóng đá Cup Tứ hùng Sinh viên Khoa Máy tính",
                "desc": "Giải đấu bóng đá sân 7 người giữa các khóa K21, K22, K23 và K24. Cổ vũ nhiệt tình, có nước uống miễn phí.",
                "cat": "Sports",
                "days": None,
                "lat": BK_CS2_LAT, "lng": BK_CS2_LNG,
                "loc": "Sân bóng đá Bách Khoa Cơ sở 2 (Dĩ An)",
                "delta_days": 6, "duration_hours": 4,
            },
            {
                "title": "Kèo bóng rổ 3x3 buổi chiều tại Sân bóng rổ Bách Khoa",
                "desc": "Tìm đội bóng rổ giao lưu thể lực sau giờ học căng thẳng. Sân miễn phí, bóng có sẵn.",
                "cat": "Sports",
                "days": None,
                "lat": BK_CS1_LAT, "lng": BK_CS1_LNG,
                "loc": "Sân bóng rổ ngoài trời - ĐH Bách Khoa CS1",
                "delta_days": 1, "duration_hours": 2,
            },
            {
                "title": "Giao lưu Cờ vua & Cờ tướng sinh viên giờ nghỉ trưa",
                "desc": "Thi đấu cờ chớp 5 phút và cờ tiêu chuẩn. Rèn luyện tư duy logic và thư giãn giữa các ca học.",
                "cat": "Sports",
                "days": None,
                "lat": BK_CS2_LAT, "lng": BK_CS2_LNG,
                "loc": "Sảnh tầng trệt Tòa nhà H6 - Bách Khoa CS2",
                "delta_days": 2, "duration_hours": 2,
            },
            {
                "title": "Chạy bộ rèn luyện thể lực sáng sớm quanh Hồ Ký túc xá ĐHQG",
                "desc": "CLB Điền kinh rủ nhau chạy bộ cự ly 5km - 10km quanh hồ đá và ký túc xá khu B. Bắt đầu lúc 5h30 sáng.",
                "cat": "Sports",
                "days": None,
                "lat": BK_CS2_LAT, "lng": BK_CS2_LNG,
                "loc": "Hồ Ký túc xá ĐHQG - Gần Bách Khoa CS2",
                "delta_days": 4, "duration_hours": 1,
            },
            {
                "title": "Giao hữu Bóng bàn Sinh viên tại Nhà thi đấu",
                "desc": "Tìm đối tác đánh bóng bàn đơn và đôi. Có 4 bàn thi đấu tiêu chuẩn, vợt và bóng tự trang bị.",
                "cat": "Sports",
                "days": None,
                "lat": BK_CS1_LAT, "lng": BK_CS1_LNG,
                "loc": "Tầng 2 Nhà thi đấu Đa năng Bách Khoa CS1",
                "delta_days": 5, "duration_hours": 2,
            },
            {
                "title": "Đêm nhạc Acoustic Sinh viên 'Giai điệu Bách Khoa'",
                "desc": "Giao lưu âm nhạc mộc acoustic, guitar, cajon và hát tự do. Không gian ngoài trời thoáng đãng, trà sữa tự chọn.",
                "cat": "Social",
                "days": None,
                "lat": BK_CS1_LAT, "lng": BK_CS1_LNG,
                "loc": "Quảng trường A1 - ĐH Bách Khoa CS1",
                "delta_days": 4, "duration_hours": 3,
            },
            {
                "title": "Giải đấu Thể thao Điện tử Esports BK Cup môn Valorant",
                "desc": "Giải đấu thể thao điện tử dành riêng cho sinh viên Bách Khoa. Đăng ký theo đội 5 người, có bình luận trực tiếp.",
                "cat": "Entertainment",
                "days": None,
                "lat": BK_CS2_LAT, "lng": BK_CS2_LNG,
                "loc": "Hội trường H1 - ĐH Bách Khoa Cơ sở 2",
                "delta_days": 7, "duration_hours": 6,
            },
        ]

        count = 0
        for item in raw_activities:
            st = now + timedelta(days=item["delta_days"])
            et = st + timedelta(hours=item["duration_hours"])
            
            # Tính embedding
            full_text = f"{item['title']} {item['desc']} {item['cat']} {item['loc']}"
            emb = generate_embedding(full_text)
            
            act = Activity(
                id=uuid.uuid4(),
                host_id=org_ctxh.id if item["days"] else student_dat.id,
                title=item["title"],
                description=item["desc"],
                category=item["cat"],
                meeting_location=item["loc"],
                start_time=st,
                end_time=et,
                max_participants=50,
                social_work_days=item["days"],
                privacy=ActivityPrivacy.public,
                require_approval=False,
                is_deleted=False,
                embedding=emb,
            )
            # Set PostGIS point
            point_wkt = f"POINT({item['lng']} {item['lat']})"
            act.marker_location = point_wkt
            
            db.add(act)
            count += 1
            print(f"  [{count:02d}/20] Đã tạo & nhúng vector: {item['title'][:40]}... (CTXH: {item['days']})")

        await db.commit()
        print(f"\n🎉 HOÀN TẤT SEED {count} HOẠT ĐỘNG THỰC TẾ BÁCH KHOA VÀO DATABASE!")

if __name__ == "__main__":
    asyncio.run(seed_bachkhoa())
