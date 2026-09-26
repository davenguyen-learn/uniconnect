"""Seed sample activities in TP. Long Khánh (Đồng Nai) for UniConnect.
"""
import asyncio
from datetime import datetime, timedelta, timezone
import uuid
from sqlalchemy import select

from app.core.database import async_session_factory
from app.modules.activities.models import Activity
from app.modules.users.models import User, UserRole
from app.modules.trophies.models import Trophy
from app.modules.chat.embeddings import generate_embedding

LONG_KHANH_ACTIVITIES = [
    {
        "title": "Chiến dịch Mùa Hè Xanh: Phụ đạo Tin học & Tiếng Anh cho Học sinh Long Khánh",
        "description": "Chiến dịch tình nguyện thường niên phối hợp cùng Thành đoàn Long Khánh. Đội hình sinh viên tình nguyện Bách Khoa hướng dẫn tin học văn phòng, lập trình cơ bản và tiếng Anh giao tiếp cho học sinh THCS - THPT trên địa bàn.",
        "category": "Social",
        "lat": 10.9425,
        "lng": 107.2388,
        "meeting_location": "Trường THPT Long Khánh, 21 Tháng 4, P. Xuân Bình, TP. Long Khánh",
        "days_from_now": 3,
        "duration_hours": 4,
        "max_participants": 35,
        "social_work_days": 2.0,
        "trophy_name": "Chiến sĩ Mùa hè xanh Long Khánh 2026",
        "trophy_desc": "Trao tặng tình nguyện viên tham gia tích cực chiến dịch Mùa hè xanh tại TP. Long Khánh.",
        "host_email": "doan@hcmut.edu.vn",
    },
    {
        "title": "Giải Chạy Việt dã 'Thanh niên Khỏe vì Đất nước' TP. Long Khánh 2026",
        "description": "Giải chạy cự ly 5km và 10km quanh công viên trung tâm và các tuyến phố rợp bóng cây xanh của thành phố Long Khánh nhằm lan tỏa phong trào rèn luyện sức khỏe trong sinh viên và thanh niên địa phương.",
        "category": "Sports",
        "lat": 10.9392,
        "lng": 107.2405,
        "meeting_location": "Công viên Bia Chiến Thắng Long Khánh, Đường Hùng Vương, P. Xuân An, TP. Long Khánh",
        "days_from_now": 5,
        "duration_hours": 3,
        "max_participants": 100,
        "social_work_days": 1.0,
        "trophy_name": "Kiện tướng Điền kinh Long Khánh",
        "trophy_desc": "Hoàn thành xuất sắc cự ly chạy phong trào tại TP. Long Khánh.",
        "host_email": "ctxh@hcmut.edu.vn",
    },
    {
        "title": "Ngày hội Chuyển đổi số: Hỗ trợ Người dân Cài đặt VNeID & Dịch vụ công",
        "description": "Đội hình tình nguyện số hỗ trợ bà con nhân dân tại TP. Long Khánh kích hoạt định danh điện tử mức 2, phổ cập kỹ năng an toàn thông tin trên điện thoại và phòng chống lừa đảo trực tuyến.",
        "category": "Social",
        "lat": 10.9435,
        "lng": 107.2415,
        "meeting_location": "Trung tâm Văn hóa Thể thao TP. Long Khánh, Cách Mạng Tháng 8, P. Xuân Bình",
        "days_from_now": 7,
        "duration_hours": 5,
        "max_participants": 20,
        "social_work_days": 1.5,
        "host_email": "admin@hcmut.edu.vn",
    },
    {
        "title": "CLB Tiếng Anh Sinh viên Đồng Nai: Coffee Talk & Board Game Luyện IELTS",
        "description": "Buổi sinh hoạt giao lưu phản xạ nói tiếng Anh theo chủ đề công nghệ và đời sống đại học, kết hợp chơi board game Avalon, Ma Sói, Catan bằng tiếng Anh.",
        "category": "Study",
        "lat": 10.9405,
        "lng": 107.2435,
        "meeting_location": "Green Space Coffee, Đường Khổng Tử, P. Xuân Trung, TP. Long Khánh",
        "days_from_now": 2,
        "duration_hours": 3,
        "max_participants": 25,
        "social_work_days": None,
        "host_email": "đạt_1@hcmut.edu.vn",
    },
    {
        "title": "Giao hữu Cầu lông Phong trào CLB Bách Khoa & Thanh niên Xuân Hòa",
        "description": "Kèo giao lưu cầu lông đôi nam và đôi nam nữ cuối tuần. Đánh giao lưu rèn luyện phản xạ và giao lưu thể thao kết nối sinh viên đang sinh sống tại Long Khánh.",
        "category": "Sports",
        "lat": 10.9450,
        "lng": 107.2450,
        "meeting_location": "Nhà Thi đấu Thể thao TP. Long Khánh, 21 Tháng 4, P. Xuân Hòa",
        "days_from_now": 4,
        "duration_hours": 2,
        "max_participants": 16,
        "social_work_days": None,
        "host_email": "hương_2@hcmut.edu.vn",
    },
    {
        "title": "Ngày Chủ Nhật Xanh: Dọn dẹp Vệ sinh và Tôn tạo Cảnh quan Hồ Cầu Dầu",
        "description": "Hoạt động bảo vệ môi trường, thu gom rác thải nhựa và trồng cây hoa ven hồ sinh thái Cầu Dầu, góp phần xây dựng cảnh quan xanh - sạch - đẹp cho thành phố Long Khánh.",
        "category": "Social",
        "lat": 10.9250,
        "lng": 107.2550,
        "meeting_location": "Khuôn viên Hồ sinh thái Cầu Dầu, P. Xuân Tân, TP. Long Khánh",
        "days_from_now": 8,
        "duration_hours": 4,
        "max_participants": 40,
        "social_work_days": 1.0,
        "host_email": "ctxh@hcmut.edu.vn",
    },
]

async def seed_long_khanh():
    now = datetime.now(timezone.utc)
    async with async_session_factory() as db:
        print("Checking users...")
        for data in LONG_KHANH_ACTIVITIES:
            # Check if already exists
            exist_q = select(Activity).where(Activity.title == data["title"])
            exist = (await db.execute(exist_q)).scalar_one_or_none()
            if exist:
                print(f"Skipping already existing activity: {data['title']}")
                continue

            # Find host
            host_q = select(User).where(User.email == data["host_email"])
            host = (await db.execute(host_q)).scalar_one_or_none()
            if not host:
                admin_q = select(User).where(User.role == UserRole.admin).limit(1)
                host = (await db.execute(admin_q)).scalar_one()

            start_t = now + timedelta(days=data["days_from_now"], hours=2)
            end_t = start_t + timedelta(hours=data["duration_hours"])
            emb_text = f"{data['title']}\n{data['description']}"
            point_wkt = f"SRID=4326;POINT({data['lng']} {data['lat']})"

            import secrets
            check_in_code = secrets.token_hex(4).upper()

            act = Activity(
                host_id=host.id,
                title=data["title"],
                description=data["description"],
                category=data["category"],
                marker_location=point_wkt,
                meeting_location=data["meeting_location"],
                start_time=start_t,
                end_time=end_t,
                max_participants=data["max_participants"],
                current_participants=1,
                privacy="public",
                require_approval=False,
                social_work_days=data["social_work_days"],
                attendance_mode="manual",
                check_in_radius=300,
                check_in_code=check_in_code,
                embedding=generate_embedding(emb_text),
            )
            db.add(act)
            await db.flush()

            # Optional Trophy
            if "trophy_name" in data:
                # Check if trophy already exists
                tr_q = select(Trophy).where(Trophy.name == data["trophy_name"])
                existing_tr = (await db.execute(tr_q)).scalar_one_or_none()
                if not existing_tr:
                    trophy = Trophy(
                        activity_id=act.id,
                        name=data["trophy_name"],
                        description=data.get("trophy_desc", ""),
                    )
                    db.add(trophy)
                    await db.flush()

            print(f"Created activity: '{data['title']}' at ({data['lat']}, {data['lng']})")

        await db.commit()
        print("Successfully seeded Long Khanh activities!")

if __name__ == "__main__":
    asyncio.run(seed_long_khanh())
