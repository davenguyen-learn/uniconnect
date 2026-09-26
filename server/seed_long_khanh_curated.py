"""
Seed curated sample activities and realistic users in TP. Long Khánh (Đồng Nai) for UniConnect.
Strictly conforms to:
- Real locations in TP. Long Khánh (coordinates around Lat 10.92-10.95, Lng 107.23-107.26)
- Diverse users with realistic Instagram/TikTok-style names
- Usernames: strictly text and underscores only (no numbers, no special symbols)
- Specific themes: study group, movies, food/social, sports, volunteer (CTXH), boardgame
- ZERO gaming activities
- Includes overlap/conflict pairs to test calendar conflict detection and red outline on map
"""
import asyncio
from datetime import datetime, timedelta, timezone
import secrets
from sqlalchemy import select
from geoalchemy2.elements import WKTElement

from app.core.database import async_session_factory
from app.core.security import hash_password
from app.modules.activities.models import Activity
from app.modules.users.models import User, UserRole
from app.modules.trophies.models import Trophy
from app.modules.chat.embeddings import generate_embedding


USERS_DATA = [
    {
        "username": "linh_dan",
        "full_name": "Đặng Linh Đan",
        "email": "linh_dan@uniconnect.edu.vn",
        "bio": "Mê cafe sách, board game và thích đi dạo cuối tuần 🌿",
        "university": "Đại học Bách Khoa TP.HCM",
        "interests": ["Boardgame", "Study", "Social"],
    },
    {
        "username": "minh_triet",
        "full_name": "Lê Minh Triết",
        "email": "minh_triet@uniconnect.edu.vn",
        "bio": "Bách Khoa K22 • Nghiện chạy bộ, cầu lông và phong trào thể thao 🏸",
        "university": "Đại học Bách Khoa TP.HCM",
        "interests": ["Sports", "Social"],
    },
    {
        "username": "phuong_thao",
        "full_name": "Nguyễn Phương Thảo",
        "email": "phuong_thao@uniconnect.edu.vn",
        "bio": "IELTS 7.5 hunter • Tìm bạn cùng học tập chăm chỉ 📚",
        "university": "Đại học Bách Khoa TP.HCM",
        "interests": ["Study", "Social"],
    },
    {
        "username": "khanh_vy",
        "full_name": "Trần Khánh Vy",
        "email": "khanh_vy@uniconnect.edu.vn",
        "bio": "Mê điện ảnh, phim rạp cuối tuần và food tour phố đêm 🎬🍜",
        "university": "Đại học Bách Khoa TP.HCM",
        "interests": ["Entertainment", "Food", "Social"],
    },
    {
        "username": "hoang_nam",
        "full_name": "Bùi Hoàng Nam",
        "email": "hoang_nam@uniconnect.edu.vn",
        "bio": "Tình nguyện viên tích cực • Yêu thiên nhiên và trồng cây 🌳",
        "university": "Đại học Bách Khoa TP.HCM",
        "interests": ["Volunteer", "Social"],
    },
    {
        "username": "thanh_truc",
        "full_name": "Vũ Thanh Trúc",
        "email": "thanh_truc@uniconnect.edu.vn",
        "bio": "Coffee lover • Catan & Ma Sói master 🎲",
        "university": "Đại học Bách Khoa TP.HCM",
        "interests": ["Boardgame", "Entertainment"],
    },
    {
        "username": "anh_thu",
        "full_name": "Phạm Anh Thư",
        "email": "anh_thu@uniconnect.edu.vn",
        "bio": "Foodie chính hiệu • Đam mê ăn vặt và làm quen bạn bè mới 🧋",
        "university": "Đại học Kinh tế TP.HCM",
        "interests": ["Food", "Social"],
    },
    {
        "username": "gia_huy",
        "full_name": "Đỗ Gia Huy",
        "email": "gia_huy@uniconnect.edu.vn",
        "bio": "Pickleball & bóng rổ phong trào cuối tuần 🏀",
        "university": "Đại học Bách Khoa TP.HCM",
        "interests": ["Sports", "Entertainment"],
    },
    {
        "username": "bao_ngoc",
        "full_name": "Huỳnh Bảo Ngọc",
        "email": "bao_ngoc@uniconnect.edu.vn",
        "bio": "Học nhóm ôn thi & luyện tiếng Anh giao tiếp phản xạ 📖",
        "university": "Đại học Bách Khoa TP.HCM",
        "interests": ["Study", "Volunteer"],
    },
    {
        "username": "quang_khai",
        "full_name": "Đinh Quang Khải",
        "email": "quang_khai@uniconnect.edu.vn",
        "bio": "Tình nguyện viên Chữ Thập Đỏ Long Khánh ❤️",
        "university": "Đại học Y Dược TP.HCM",
        "interests": ["Volunteer", "Social"],
    },
    {
        "username": "quynh_chi",
        "full_name": "Ngô Quỳnh Chi",
        "email": "quynh_chi@uniconnect.edu.vn",
        "bio": "Thích chụp ảnh film, cà phê acoustic giao lưu bạn mới 📸☕",
        "university": "Đại học Bách Khoa TP.HCM",
        "interests": ["Social", "Entertainment"],
    },
    {
        "username": "tuan_kiet",
        "full_name": "Phan Tuấn Kiệt",
        "email": "tuan_kiet@uniconnect.edu.vn",
        "bio": "Yêu thích khoa học dữ liệu và giải thuật toán 💻",
        "university": "Đại học Bách Khoa TP.HCM",
        "interests": ["Study", "Technology"],
    },
]


ACTIVITIES_DATA = [
    # ── 1. STUDY GROUP ──
    {
        "title": "Study Group: Ôn tập Giải tích & Đại số tuyến tính cuối kỳ",
        "description": "Nhóm học tập cùng giải đề thi mẫu, trao đổi phương pháp giải các dạng bài tập khó môn Giải tích và Đại số tuyến tính. Phù hợp cho sinh viên năm 1, năm 2 chuẩn bị thi cuối kỳ.",
        "category": "Study",
        "lat": 10.9412,
        "lng": 107.2418,
        "meeting_location": "The Coffee House Long Khánh, 126 Hùng Vương, P. Xuân An, TP. Long Khánh",
        "hours_offset": 5,  # 5h from now (urgent / soon badge)
        "duration_hours": 3,
        "max_participants": 12,
        "social_work_days": None,
        "host_username": "tuan_kiet",
    },
    {
        "title": "IELTS Speaking Club: Luyện phản xạ & Mock Test Part 2-3",
        "description": "Buổi sinh hoạt tiếng Anh chuyên đề phản xạ giao tiếp. Thực hành luyện nói 1-1 theo các chủ đề nóng: AI in Education, Sustainable Living, Campus Life. Có tài liệu và từ vựng band 7.5+ chuẩn bị sẵn.",
        "category": "Study",
        "lat": 10.9428,
        "lng": 107.2435,
        "meeting_location": "Phúc Long Coffee & Tea, 48 Khổng Tử, P. Xuân Trung, TP. Long Khánh",
        "hours_offset": 24 + 4,  # ~1d from now
        "duration_hours": 2,
        "max_participants": 15,
        "social_work_days": None,
        "host_username": "phuong_thao",
    },
    {
        "title": "Workshop Python & Xử lý dữ liệu cơ bản cho người mới bắt đầu",
        "description": "Buổi chia sẻ kiến thức nền tảng về lập trình Python, thư viện Pandas, Matplotlib và cách ứng dụng phân tích dữ liệu học tập. Yêu cầu tự trang bị laptop cá nhân.",
        "category": "Study",
        "lat": 10.9436,
        "lng": 107.2392,
        "meeting_location": "Phòng đọc Thư viện TP. Long Khánh, Cách Mạng Tháng 8, P. Xuân Bình",
        "hours_offset": 48 + 3,  # ~2d from now
        "duration_hours": 3,
        "max_participants": 18,
        "social_work_days": None,
        "host_username": "tuan_kiet",
    },

    # ── 2. XEM PHIM (CINEMA) ──
    {
        "title": "Xem phim rạp cuối tuần: Suất chiếu bom tấn & Cafe thảo luận",
        "description": "Rủ hội mê điện ảnh cùng xem suất chiếu tối tại rạp Beta Cinemas. Sau buổi chiếu nhóm sẽ ngồi lại cà phê bàn luận về thông điệp, kỹ xảo điện ảnh và làm quen bạn mới.",
        "category": "Entertainment",
        "lat": 10.9395,
        "lng": 107.2402,
        "meeting_location": "Rạp Beta Cinemas Long Khánh, Đường Hùng Vương, P. Xuân Bình, TP. Long Khánh",
        "hours_offset": 24 + 11,  # 1d from now (suất tối)
        "duration_hours": 3,
        "max_participants": 8,
        "social_work_days": None,
        "host_username": "khanh_vy",
    },
    {
        "title": "Movie Night: Chiếu phim tài liệu 'Hành Tinh Xanh' & Thảo luận mở",
        "description": "Buổi chiếu phim tài liệu môi trường bằng máy chiếu chất lượng cao tại quán cafe sân vườn, kèm thảo luận về thói quen giảm rác thải nhựa của giới trẻ.",
        "category": "Entertainment",
        "lat": 10.9455,
        "lng": 107.2460,
        "meeting_location": "Cỏ May Garden Coffee, 32 Ngô Quyền, P. Xuân Thanh, TP. Long Khánh",
        "hours_offset": 72 + 6,  # 3d from now
        "duration_hours": 2,
        "max_participants": 16,
        "social_work_days": None,
        "host_username": "hoang_nam",
    },

    # ── 3. ĐI ĂN LÀM QUEN (FOOD & SOCIAL) ──
    {
        "title": "Food Tour Phố Đêm: Khám phá ẩm thực đường phố & Kết bạn mới",
        "description": "Cùng nhau oanh tạc các món ăn vặt nức tiếng Long Khánh: bánh tráng nướng, nem nướng, chè bưởi, gỏi cuốn. Vừa ăn ngon vừa chia sẻ kinh nghiệm học tập và đời sống sinh viên.",
        "category": "Food",
        "lat": 10.9408,
        "lng": 107.2425,
        "meeting_location": "Cổng Phố Ẩm Thực Chợ Đêm Long Khánh, Đường Nguyễn Trãi, TP. Long Khánh",
        "hours_offset": 8,  # 8h from now (tối nay)
        "duration_hours": 3,
        "max_participants": 10,
        "social_work_days": None,
        "host_username": "anh_thu",
    },
    {
        "title": "Cà phê Acoustic Cuối Tuần: Giao lưu âm nhạc & Làm quen bạn sinh viên",
        "description": "Không gian âm nhạc mộc acoustic nhẹ nhàng. Mời các bạn yêu ca hát, guitar hoặc đơn giản muốn tìm một góc trò chuyện thư giãn cùng bạn bè sau tuần học căng thẳng.",
        "category": "Social",
        "lat": 10.9419,
        "lng": 107.2442,
        "meeting_location": "Trầm Acoustic Coffee, 18 Khổng Tử, P. Xuân Trung, TP. Long Khánh",
        "hours_offset": 48 + 11,  # 2d from now (tối cuối tuần)
        "duration_hours": 3,
        "max_participants": 14,
        "social_work_days": None,
        "host_username": "quynh_chi",
    },
    {
        "title": "Trà chiều kết nối: Gặp gỡ và chia sẻ kinh nghiệm thích nghi Đại học",
        "description": "Buổi trò chuyện thân mật dành cho các bạn sinh viên quê Long Khánh đang học tập tại các trường ĐH. Trao đổi về cuộc sống xa nhà, phương pháp học hiệu quả và săn học bổng.",
        "category": "Social",
        "lat": 10.9388,
        "lng": 107.2396,
        "meeting_location": "Highlands Coffee Long Khánh, Ngã tư Hùng Vương - Trần Phú, TP. Long Khánh",
        "hours_offset": 24 + 7,  # 1d from now (buổi chiều - Cố tình TRÙNG KHUNG GIỜ với trận cầu lông để test conflict)
        "duration_hours": 2,
        "max_participants": 12,
        "social_work_days": None,
        "host_username": "linh_dan",
    },

    # ── 4. THỂ THAO (SPORTS) ──
    {
        "title": "Chạy bộ rèn luyện sức bền sáng sớm quanh Công viên Bia Chiến Thắng",
        "description": "Kèo chạy bộ cự ly 3km - 5km buổi sáng sớm quanh khuôn viên rợp bóng mát của công viên trung tâm. Phù hợp cho cả người mới bắt đầu chạy bộ lẫn người rèn luyện thể lực.",
        "category": "Sports",
        "lat": 10.9392,
        "lng": 107.2405,
        "meeting_location": "Đài tưởng niệm Công viên Bia Chiến Thắng Long Khánh, Đường Hùng Vương",
        "hours_offset": 24 + 1,  # Sáng mai (~6h sáng)
        "duration_hours": 1,
        "max_participants": 25,
        "social_work_days": None,
        "host_username": "minh_triet",
    },
    {
        "title": "Kèo Cầu lông Phong trào: Đánh đôi giao lưu & Rèn luyện sức khỏe",
        "description": "Giao lưu cầu lông đôi nam và đôi nam nữ cuối tuần. Đã đặt sẵn 2 sân thảm tiêu chuẩn. Mang theo vợt cá nhân và giày thể thao để vào sân thi đấu giao hữu.",
        "category": "Sports",
        "lat": 10.9448,
        "lng": 107.2452,
        "meeting_location": "Sân Cầu lông Thảo Vy, 21 Tháng 4, P. Xuân Hòa, TP. Long Khánh",
        "hours_offset": 24 + 7,  # 1d from now (Cố tình TRÙNG KHUNG GIỜ với Trà chiều để tạo trường hợp conflict test)
        "duration_hours": 2,
        "max_participants": 16,
        "social_work_days": None,
        "host_username": "minh_triet",
    },
    {
        "title": "Giao lưu Pickleball Người mới bắt đầu: Hướng dẫn kỹ thuật & Đánh giao hữu",
        "description": "Môn thể thao đang sốt xình xịch! Nhóm có vợt dự phòng cho người mới. Sẽ có bạn hướng dẫn luật chơi, cách phát bóng và kỹ thuật giao banh cơ bản trước khi vào set đấu.",
        "category": "Sports",
        "lat": 10.9462,
        "lng": 107.2415,
        "meeting_location": "Sân Thể thao Xuân An, Đường Nguyễn Thị Minh Khai, TP. Long Khánh",
        "hours_offset": 48 + 8,  # 2d from now
        "duration_hours": 2,
        "max_participants": 12,
        "social_work_days": None,
        "host_username": "gia_huy",
    },
    {
        "title": "Giao lưu Bóng rổ 3x3 Sinh viên cuối tuần",
        "description": "Đấu bóng rổ nửa sân 3x3 giao lưu thân thiện, vui vẻ. Rèn luyện phản xạ, thể lực và tinh thần đồng đội.",
        "category": "Sports",
        "lat": 10.9431,
        "lng": 107.2408,
        "meeting_location": "Sân Bóng rổ Trung tâm TDTT TP. Long Khánh, Cách Mạng Tháng Tám",
        "hours_offset": 72 + 8,  # 3d from now
        "duration_hours": 2,
        "max_participants": 18,
        "social_work_days": None,
        "host_username": "gia_huy",
    },

    # ── 5. TÌNH NGUYỆN (VOLUNTEER / SOCIAL WORK) ──
    {
        "title": "Ngày Chủ Nhật Xanh: Dọn dẹp vệ sinh và tôn tạo cảnh quan Hồ Cầu Dầu",
        "description": "Chiến dịch tình nguyện bảo vệ môi trường sinh thái. Thu gom rác thải nhựa quanh lòng hồ, trồng cây hoa ven lối đi bộ, góp phần xây dựng lá phổi xanh cho TP. Long Khánh.",
        "category": "Volunteer",
        "lat": 10.9250,
        "lng": 107.2550,
        "meeting_location": "Khuôn viên Hồ sinh thái Cầu Dầu, P. Xuân Tân, TP. Long Khánh",
        "hours_offset": 48 + 1,  # 2d from now (Chủ Nhật)
        "duration_hours": 4,
        "max_participants": 35,
        "social_work_days": 1.0,
        "trophy_name": "Tình nguyện viên Xanh Long Khánh",
        "trophy_desc": "Tham gia tích cực phong trào Ngày Chủ Nhật Xanh làm đẹp thành phố.",
        "host_username": "hoang_nam",
    },
    {
        "title": "Tình nguyện Tiếp Sức: Hướng dẫn an toàn số & Dịch vụ công cho người cao tuổi",
        "description": "Đội hình sinh viên hướng dẫn bà con và người cao tuổi cách sử dụng VNeID, thanh toán không tiền mặt an toàn, nhận diện thủ đoạn lừa đảo qua mạng xã hội.",
        "category": "Volunteer",
        "lat": 10.9435,
        "lng": 107.2415,
        "meeting_location": "Trung tâm Văn hóa Thể thao TP. Long Khánh, Cách Mạng Tháng 8, P. Xuân Bình",
        "hours_offset": 72 + 2,  # 3d from now
        "duration_hours": 4,
        "max_participants": 20,
        "social_work_days": 1.5,
        "trophy_name": "Đại sứ Công nghệ Cộng đồng",
        "trophy_desc": "Hỗ trợ người dân tiếp cận kỹ năng số an toàn tại cơ sở.",
        "host_username": "quang_khai",
    },
    {
        "title": "Chương trình Bát Cháo Tình Thương: Nấu và phát cháo cho bệnh nhân nghèo",
        "description": "Hoạt động thiện nguyện phối hợp cùng bếp ăn tình thương. Các bạn sinh viên phụ giúp sơ chế nguyên liệu, nấu cháo dinh dưỡng và phát tận tay các bệnh nhân điều trị nội trú.",
        "category": "Volunteer",
        "lat": 10.9365,
        "lng": 107.2420,
        "meeting_location": "Cổng Bệnh viện Đa khoa Khu vực Long Khánh, Đường Nguyễn Trãi",
        "hours_offset": 96 + 1,  # 4d from now
        "duration_hours": 3,
        "max_participants": 15,
        "social_work_days": 1.0,
        "host_username": "quang_khai",
    },

    # ── 6. BOARDGAME (NO GAMING) ──
    {
        "title": "Chiều Chủ Nhật Boardgame: Ma Sói, Catan & Avalon gắn kết bạn mới",
        "description": "Một buổi chiều giải trí lành mạnh với các trò chơi cờ bàn tư duy, chiến thuật và suy luận logic. Người chưa từng chơi sẽ được hướng dẫn chi tiết tận tình từ A-Z.",
        "category": "Boardgame",
        "lat": 10.9442,
        "lng": 107.2458,
        "meeting_location": "Cỏ May Coffee & Boardgame, 32 Ngô Quyền, P. Xuân Thanh, TP. Long Khánh",
        "hours_offset": 48 + 6,  # 2d from now (chiều CN)
        "duration_hours": 3,
        "max_participants": 16,
        "social_work_days": None,
        "host_username": "thanh_truc",
    },
    {
        "title": "Boardgame Cafe: Trí tuệ Catan, Splendor & Uno xả stress sau giờ học",
        "description": "Giao lưu boardgame nhẹ nhàng, xả stress cho các bạn sinh viên. Cùng nhau thi tài xây đường trong Catan, tích đá quý Splendor và cười thả ga cùng Uno Flip.",
        "category": "Boardgame",
        "lat": 10.9405,
        "lng": 107.2435,
        "meeting_location": "Green Space Coffee, 88 Khổng Tử, P. Xuân Trung, TP. Long Khánh",
        "hours_offset": 72 + 6,  # 3d from now
        "duration_hours": 3,
        "max_participants": 14,
        "social_work_days": None,
        "host_username": "linh_dan",
    },
]


async def run_seed():
    now = datetime.now(timezone.utc)
    hashed_pwd = hash_password("uniconnect123")

    async with async_session_factory() as db:
        print("=== BẮT ĐẦU SEED DỮ LIỆU TP. LONG KHÁNH ===")

        # 1. Tạo các user sinh viên nếu chưa có
        user_cache = {}
        for u_data in USERS_DATA:
            u_query = select(User).where(User.username == u_data["username"])
            user = (await db.execute(u_query)).scalar_one_or_none()

            if not user:
                user = User(
                    username=u_data["username"],
                    email=u_data["email"],
                    password_hash=hashed_pwd,
                    full_name=u_data["full_name"],
                    bio=u_data["bio"],
                    university=u_data["university"],
                    interests=u_data["interests"],
                    role=UserRole.student,
                    is_active=True,
                    is_verified=True,
                )
                db.add(user)
                await db.flush()
                print(f" [+] Đã tạo User: @{user.username} ({user.full_name})")
            else:
                print(f" [=] User đã tồn tại: @{user.username}")

            user_cache[user.username] = user

        # 2. Tạo các hoạt động đặc sắc tại Long Khánh
        for a_data in ACTIVITIES_DATA:
            # Kiểm tra xem hoạt động đã tồn tại theo tiêu đề chưa
            exist_q = select(Activity).where(Activity.title == a_data["title"])
            existing_act = (await db.execute(exist_q)).scalar_one_or_none()
            if existing_act:
                print(f" [=] Hoạt động đã tồn tại, bỏ qua: '{a_data['title']}'")
                continue

            host = user_cache.get(a_data["host_username"])
            if not host:
                host_q = select(User).where(User.username == a_data["host_username"])
                host = (await db.execute(host_q)).scalar_one()

            start_t = now + timedelta(hours=a_data["hours_offset"])
            end_t = start_t + timedelta(hours=a_data["duration_hours"])
            emb_text = f"{a_data['title']}\n{a_data['description']}\n{a_data['meeting_location']}"
            point_wkt = f"SRID=4326;POINT({a_data['lng']} {a_data['lat']})"

            act = Activity(
                host_id=host.id,
                title=a_data["title"],
                description=a_data["description"],
                category=a_data["category"],
                marker_location=point_wkt,
                meeting_location=a_data["meeting_location"],
                start_time=start_t,
                end_time=end_t,
                max_participants=a_data["max_participants"],
                current_participants=secrets.randbelow(max(2, a_data["max_participants"] // 2)) + 1,
                privacy="public",
                require_approval=False,
                social_work_days=a_data["social_work_days"],
                attendance_mode="manual",
                check_in_radius=300,
                check_in_code=secrets.token_hex(4).upper(),
                embedding=generate_embedding(emb_text),
            )
            db.add(act)
            await db.flush()

            # Tạo Trophy nếu có
            if "trophy_name" in a_data:
                tr_q = select(Trophy).where(Trophy.name == a_data["trophy_name"])
                existing_tr = (await db.execute(tr_q)).scalar_one_or_none()
                if not existing_tr:
                    trophy = Trophy(
                        activity_id=act.id,
                        name=a_data["trophy_name"],
                        description=a_data.get("trophy_desc", ""),
                    )
                    db.add(trophy)
                    await db.flush()

            print(f" [+] Đã tạo Hoạt động: '{act.title}' [@{host.username}] tại ({a_data['lat']}, {a_data['lng']})")

        await db.commit()
        print("=== HOÀN TẤT SEED DỮ LIỆU TP. LONG KHÁNH THÀNH CÔNG! ===")


if __name__ == "__main__":
    asyncio.run(run_seed())
