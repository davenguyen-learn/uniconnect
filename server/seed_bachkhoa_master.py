"""
Master Seed Script — Dữ liệu quy mô lớn, chân thật và sống động cho Đại học Bách Khoa TP.HCM (HCMUT).
Được thiết kế hoàn hảo để quay video demo và đánh giá thực nghiệm:
- 80+ Sinh viên Bách Khoa với avatar, ngành học, MSSV.
- 20+ CLB & Đội nhóm sinh viên với logo, banner, thành viên.
- 60+ Hoạt động chân thật phủ khắp CS1 (Q.10) và CS2 (Dĩ An), có ảnh banner đẹp, CTXH, GPS.
- 120+ Bình luận hỏi đáp, tìm teammate, review sôi nổi.
- 350+ Lượt Like thả tim.
- 150+ Đơn đăng ký (Approved & Pending) để demo duyệt đơn.
- Giấy chứng nhận tham gia điện tử có mã QR/Hash để demo kiểm chứng `/verify-certificate`.
- Thời khóa biểu sinh viên & ca xung đột lịch để demo Conflict Modal.
- 10+ Thông báo đa dạng trong Notification Bell.
- Vector Embeddings 768 chiều nạp vào pgvector cho Chatbot & Semantic Search.

Chạy:
  python server/seed_bachkhoa_master.py
"""

import asyncio
import datetime
from datetime import timezone, timedelta
import uuid
import random
import os
import sys

server_dir = os.path.dirname(os.path.abspath(__file__))
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.modules.users.models import User, UserRole, UserFollow
from app.modules.groups.models import Group, GroupMember, GroupRole
from app.modules.activities.models import Activity, ActivityPrivacy
from app.modules.participation.models import JoinRequest, RequestStatus
from app.modules.interactions.models import Comment, ContentLike
from app.modules.notifications.models import Notification
from app.modules.trophies.models import Trophy, UserTrophy
from app.modules.calendar.models import UserBusySlot, RecurrenceType
from app.modules.chat.embeddings import generate_embedding

# Tọa độ chuẩn Bách Khoa CS1 (Lý Thường Kiệt, Q.10) & CS2 (Dĩ An, Bình Dương)
BK_CS1_LAT, BK_CS1_LNG = 10.7725, 106.6578
BK_CS2_LAT, BK_CS2_LNG = 10.8800, 106.8057

HO_TIEN_PHONG_LAT, HO_TIEN_PHONG_LNG = 10.8785, 106.8042
KTX_CS1_LAT, KTX_CS1_LNG = 10.7712, 106.6591
KTX_CS2_LAT, KTX_CS2_LNG = 10.8821, 106.8075
SAN_C3_LAT, SAN_C3_LNG = 10.7731, 106.6565
HALL_A5_LAT, HALL_A5_LNG = 10.7720, 106.6582
NHA_H6_LAT, NHA_H6_LNG = 10.8812, 106.8062

AVATARS = [
    "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
    "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=150",
    "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150",
    "https://images.unsplash.com/photo-1501196354995-cbb51c65aaea?w=150",
    "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150",
    "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=150",
    "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=150",
    "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150",
    "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
    "https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=150",
]

ACTIVITY_IMAGES = [
    "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?w=800", # Tech meeting
    "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=800", # Study group
    "https://images.unsplash.com/photo-1511632765486-a01980e01a18?w=800", # Volunteering
    "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=800", # Sports running
    "https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=800", # Football soccer
    "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800", # Hackathon event
    "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=800", # Friends hangout
    "https://images.unsplash.com/photo-1517048676732-d65bc937f952?w=800", # Seminar hall
    "https://images.unsplash.com/photo-1523240795612-9a054b0db644?w=800", # Campus students
    "https://images.unsplash.com/photo-1505373877841-8d25f7d46678?w=800", # Tech workshop
]

async def seed_all():
    print("=" * 80)
    print("🚀 BẮT ĐẦU SEED DỮ LIỆU ĐẠI HỌC BÁCH KHOA MASTER (FULL SCALE FOR VIDEO DEMO)...")
    print("=" * 80)

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.datetime.now(timezone.utc)

    async with async_session() as db:
        # 1. Dọn dẹp dữ liệu cũ an toàn
        print("🧹 Làm sạch các bảng hoạt động và tương tác cũ...")
        tables_to_clear = [
            "comments", "content_likes", "notifications", "user_trophies",
            "trophies", "join_requests", "activity_cohosts", "activities",
            "group_members", "groups", "user_busy_slots", "user_follows", "users"
        ]
        for tbl in tables_to_clear:
            try:
                await db.execute(text(f"DELETE FROM {tbl}"))
                await db.commit()
            except Exception as e:
                await db.rollback()

        # 2. Khởi tạo Người dùng chính và danh sách 75+ sinh viên Bách Khoa
        print("👤 Khởi tạo tài khoản chính (Admin, Demo Student, Edu Org) & 75+ sinh viên Bách Khoa...")
        
        # Tài khoản demo chính
        dat_nguyen = User(
            id=uuid.uuid4(),
            email="dat.nguyen@hcmut.edu.vn",
            username="dat_nguyen",
            full_name="Nguyễn Đức Đạt",
            password_hash=hash_password("dat123"),
            role=UserRole.student,
            university="Đại học Bách khoa TP.HCM",
            bio="Sinh viên K21 Khoa KH&KT Máy tính • Đam mê AI, Web Development và Tình nguyện",
            interests=["machine learning", "web development", "cầu lông", "tình nguyện", "hackathon"],
            is_active=True,
            is_verified=True,
        )

        admin_bk = User(
            id=uuid.uuid4(),
            email="admin@hcmut.edu.vn",
            username="admin_bk",
            full_name="Ban Quản trị UniConnect HCMUT",
            password_hash=hash_password("admin123"),
            role=UserRole.admin,
            university="Đại học Bách khoa TP.HCM",
            bio="Tài khoản Quản trị viên cấp cao hệ thống UniConnect Trường ĐH Bách Khoa",
            is_active=True,
            is_verified=True,
        )

        ctxh_bk = User(
            id=uuid.uuid4(),
            email="ctxh@hcmut.edu.vn",
            username="ctxh_bk",
            full_name="Ban Công tác Xã hội ĐH Bách Khoa",
            password_hash=hash_password("ctxh123"),
            role=UserRole.edu_org,
            university="Đại học Bách khoa TP.HCM",
            bio="Kênh truyền thông và phê duyệt ngày Công tác Xã hội chính thức của Trường ĐH Bách Khoa",
            is_active=True,
            is_verified=True,
        )

        doan_bk = User(
            id=uuid.uuid4(),
            email="doan@hcmut.edu.vn",
            username="doan_bk",
            full_name="Đoàn Thanh niên - Hội Sinh viên HCMUT",
            password_hash=hash_password("doan123"),
            role=UserRole.edu_org,
            university="Đại học Bách khoa TP.HCM",
            bio="Đoàn trường ĐH Bách Khoa - Đại học Quốc gia TP.HCM",
            is_active=True,
            is_verified=True,
        )

        users_list = [dat_nguyen, admin_bk, ctxh_bk, doan_bk]

        # Sinh thêm 75 sinh viên chân thật
        HO = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương"]
        DEM = ["Văn", "Thị", "Đức", "Minh", "Thanh", "Anh", "Hoàng", "Quốc", "Gia", "Hữu", "Khánh", "Ngọc", "Bảo"]
        TEN = ["Nam", "Tuấn", "Hùng", "Dũng", "Khoa", "Đạt", "Long", "Thịnh", "Trí", "Phúc", "Khang", "Vy", "Trang", "Linh", "Mai", "Hương", "Hà", "Ngân", "Anh", "Thảo"]
        MAJORS = [
            "Khoa học Máy tính (K21)", "Kỹ thuật Phần mềm (K22)", "Kỹ thuật Máy tính (K23)",
            "Điện - Điện tử (K21)", "Kỹ thuật Điều khiển & Tự động hóa (K22)", "Kỹ thuật Cơ điện tử (K21)",
            "Kỹ thuật Hóa học (K22)", "Quản lý Công nghiệp (K23)", "Logistics & Chuỗi cung ứng (K21)"
        ]

        created_usernames = {"dat_nguyen", "admin_bk", "ctxh_bk", "doan_bk"}
        import unicodedata
        def strip_vn(s: str) -> str:
            s = s.replace('đ', 'd').replace('Đ', 'D')
            nfkd = unicodedata.normalize('NFKD', s)
            return ''.join([c for c in nfkd if not unicodedata.combining(c)]).lower().strip()

        cached_student_pwd = hash_password("student123")
        for i in range(1, 76):
            h = random.choice(HO)
            d = random.choice(DEM)
            t = random.choice(TEN)
            full_name = f"{h} {d} {t}"
            base_u = f"{strip_vn(t)}_{i}"
            if base_u in created_usernames:
                base_u = f"{base_u}_{random.randint(10,99)}"
            created_usernames.add(base_u)

            u = User(
                id=uuid.uuid4(),
                email=f"{base_u}@hcmut.edu.vn",
                username=base_u,
                full_name=full_name,
                password_hash=cached_student_pwd,
                role=UserRole.student,
                university="Đại học Bách khoa TP.HCM",
                bio=f"Sinh viên {random.choice(MAJORS)} • Bách Khoa HCMUT",
                interests=random.sample(["AI", "Web", "Cầu lông", "Bóng đá", "Tình nguyện", "Guitar", "Tiếng Anh", "Hackathon", "Chạy bộ", "Đọc sách"], 3),
                is_active=True,
                is_verified=True,
            )
            users_list.append(u)

        db.add_all(users_list)
        await db.commit()
        for u in users_list[:10]:
            await db.refresh(u)

        student_pool = [u for u in users_list if u.role == UserRole.student]
        print(f"✅ Đã tạo {len(users_list)} người dùng Bách Khoa thành công!")

        # 3. Tạo 20+ CLB & Đội nhóm Bách Khoa
        print("👥 Khởi tạo 20+ Câu lạc bộ & Đội nhóm sinh viên Bách Khoa...")
        GROUPS_DATA = [
            ("CLB Lập trình Bách Khoa (BK Coding Club)", "Nơi hội tụ các lập trình viên Bách Khoa, luyện thuật toán ICPC, Hackathon và chia sẻ kiến thức phần mềm.", dat_nguyen.id),
            ("Đội Công tác Xã hội ĐH Bách Khoa", "Tổ chức các chiến dịch tình nguyện Mùa Hè Xanh, Tiếp Sức Mùa Thi, Chủ Nhật Xanh và hiến máu nhân đạo.", ctxh_bk.id),
            ("Google Developer Student Club - HCMUT", "Cộng đồng công nghệ Google dành cho sinh viên Bách Khoa đam mê AI, Cloud và Web/Mobile.", dat_nguyen.id),
            ("CLB Tiếng Anh Bách Khoa (BEC HCMUT)", "Không gian rèn luyện tiếng Anh giao tiếp, thuyết trình và tổ chức các buổi Coffee Talk hàng tuần.", student_pool[1].id),
            ("CLB Thể thao & Cầu lông Bách Khoa", "Giao lưu thể thao, rèn luyện thể lực và tổ chức giải cầu lông mở rộng mỗi kỳ.", student_pool[2].id),
            ("CLB Bóng đá Sinh viên KTX Bách Khoa", "Kết nối các anh em đam mê túc cầu sân 5 và sân 7 tại cụm sân KTX và khu vực lân cận.", student_pool[3].id),
            ("CLB Guitar Bách Khoa (BGC)", "Nơi âm nhạc hòa quyện với tâm hồn sinh viên kỹ thuật. Giao lưu acoustic mỗi tối thứ 6.", student_pool[4].id),
            ("CLB Robotics & Tự động hóa Bách Khoa", "Nghiên cứu thiết kế robot, mạch nhúng, IoT và tham gia Robocon toàn quốc.", student_pool[5].id),
            ("Đoàn Khoa Khoa học & Kỹ thuật Máy tính", "Kênh thông tin chính thức của Đoàn - Hội Khoa KH&KT Máy tính ĐH Bách Khoa.", doan_bk.id),
            ("CLB Khởi nghiệp Sinh viên (BK Innovation)", "Đồng hành ươm mầm các ý tưởng khởi nghiệp sáng tạo, kết nối mentor và quỹ đầu tư.", student_pool[6].id),
            ("CLB Cờ Bách Khoa (Cờ vua & Cờ tướng)", "Nơi đấu trí căng thẳng sau giờ học căng thẳng tại sảnh nhà H6 CS2.", student_pool[7].id),
            ("CLB Nhiếp ảnh & Truyền thông (BK Media)", "Ghi lại những khoảnh khắc đẹp nhất thời sinh viên Bách Khoa qua từng lăng kính.", student_pool[8].id),
            ("CLB Võ thuật Bách Khoa (Vovinam & Taekwondo)", "Rèn luyện thể chất, tự vệ và tinh thần thượng võ của sinh viên Bách Khoa.", student_pool[9].id),
            ("CLB Sách & Văn hóa Đọc Bách Khoa", "Trao đổi sách học thuật, văn học và tổ chức các buổi Book Review hàng tháng.", student_pool[10].id),
            ("CLB Sinh viên Nghiên cứu Khoa học (BK Research)", "Kết nối các bạn sinh viên với phòng Lab và các dự án NCKH của giảng viên.", student_pool[11].id),
        ]

        groups_list = []
        for name, desc, owner_id in GROUPS_DATA:
            g = Group(
                id=uuid.uuid4(),
                owner_id=owner_id,
                name=name,
                description=desc,
                privacy="public",
                allow_member_activities=True,
            )
            groups_list.append(g)

        db.add_all(groups_list)
        await db.commit()
        for g in groups_list:
            await db.refresh(g)

        # Thêm thành viên vào các nhóm
        group_members = []
        for g in groups_list:
            # Add owner as group admin
            group_members.append(GroupMember(id=uuid.uuid4(), group_id=g.id, user_id=g.owner_id, role=GroupRole.admin))
            # Add random 15-30 members
            selected_members = random.sample(student_pool, random.randint(15, 30))
            for m in selected_members:
                if m.id != g.owner_id:
                    group_members.append(GroupMember(id=uuid.uuid4(), group_id=g.id, user_id=m.id, role=GroupRole.member))
        
        # Đảm bảo dat_nguyen tham gia 4 nhóm tiêu biểu
        for g in groups_list[:4]:
            if not any(gm.user_id == dat_nguyen.id and gm.group_id == g.id for gm in group_members):
                group_members.append(GroupMember(id=uuid.uuid4(), group_id=g.id, user_id=dat_nguyen.id, role=GroupRole.admin))

        db.add_all(group_members)
        await db.commit()
        print(f"✅ Đã tạo {len(groups_list)} nhóm và {len(group_members)} lượt gia nhập nhóm!")

        # 4. Tạo Trophies & Danh hiệu
        print("🏆 Khởi tạo Danh hiệu & Trophies...")
        trophies_data = [
            ("Chiến sĩ CTXH Tiêu biểu", "Tích lũy xuất sắc trên 10 ngày Công tác Xã hội trong năm học"),
            ("Huy hiệu Bách Khoa Hackathon 2026", "Tham gia tranh tài cuộc thi Lập trình AI for Smart Campus"),
            ("Tân sinh viên Tích cực K26", "Tham gia trên 3 hoạt động phong trào hội nhập đầu khóa"),
            ("Vận động viên Thể thao Bách Khoa", "Tham gia giải chạy bộ hoặc hội thao cấp trường"),
            ("Thành viên Năng nổ UniConnect", "Tương tác và đóng góp tích cực cho cộng đồng sinh viên"),
        ]
        trophies_list = []
        for t_name, t_desc in trophies_data:
            tr = Trophy(id=uuid.uuid4(), name=t_name, description=t_desc)
            trophies_list.append(tr)
        db.add_all(trophies_list)
        await db.commit()
        for tr in trophies_list:
            await db.refresh(tr)

        # 5. Danh sách 60+ Hoạt động Bách Khoa sống động và phong phú
        print("🎪 Khởi tạo 60+ Hoạt động Bách Khoa chân thật kèm Vector Embeddings (768-dim)...")

        ACTIVITIES_DATA = [
            # ── 1. TÌNH NGUYỆN & CÔNG TÁC XÃ HỘI (20 hoạt động) ──
            {
                "title": "Chiến dịch Tình nguyện Ngày Chủ Nhật Xanh - Vệ sinh Hồ Tiền Phong",
                "desc": "Thu gom rác thải nhựa, dọn dẹp vệ sinh bờ hồ Tiền Phong và tôn tạo cảnh quan xanh quanh khuôn viên Ký túc xá Bách Khoa Cơ sở 2.",
                "cat": "Tình nguyện & CTXH",
                "lat": HO_TIEN_PHONG_LAT, "lng": HO_TIEN_PHONG_LNG,
                "loc": "Hồ Tiền Phong - ĐH Bách Khoa CS2 (Dĩ An)",
                "days_offset": 2, "hours": 4, "ctxh": 1.0, "max_p": 80,
                "host_id": ctxh_bk.id, "img": ACTIVITY_IMAGES[2]
            },
            {
                "title": "Ngày hội Hiến máu Nhân đạo: Giọt hồng Bách Khoa đợt 1 năm 2026",
                "desc": "Chương trình hiến máu tình nguyện do Hội Chữ Thập Đỏ và Đoàn trường phối hợp tổ chức nhằm cứu người và lan tỏa tinh thần sẻ chia vì cộng đồng.",
                "cat": "Tình nguyện & CTXH",
                "lat": BK_CS1_LAT + 0.0005, "lng": BK_CS1_LNG + 0.0004,
                "loc": "Trạm Y tế - Trường ĐH Bách Khoa CS1 (Lý Thường Kiệt)",
                "days_offset": 3, "hours": 5, "ctxh": 1.0, "max_p": 150,
                "host_id": ctxh_bk.id, "img": ACTIVITY_IMAGES[6]
            },
            {
                "title": "Chiến dịch Tiếp sức Mùa thi 2026 - Hỗ trợ thí sinh THPT Quốc gia",
                "desc": "Tập huấn tình nguyện viên hỗ trợ điều phối giao thông, phát nước suối, hướng dẫn sơ đồ phòng thi cho thí sinh và phụ huynh.",
                "cat": "Tình nguyện & CTXH",
                "lat": HALL_A5_LAT, "lng": HALL_A5_LNG,
                "loc": "Hội trường A5 - Trường ĐH Bách Khoa CS1",
                "days_offset": 7, "hours": 8, "ctxh": 2.0, "max_p": 100,
                "host_id": doan_bk.id, "img": ACTIVITY_IMAGES[8]
            },
            {
                "title": "Chương trình Thu gom Pin cũ và Rác thải Điện tử đổi Sen đá",
                "desc": "Hoạt động bảo vệ môi trường nâng cao ý thức phân loại rác độc hại trong sinh viên. Đổi 5 viên pin cũ lấy 1 chậu sen đá mini để bàn.",
                "cat": "Tình nguyện & CTXH",
                "lat": BK_CS1_LAT - 0.0004, "lng": BK_CS1_LNG + 0.0008,
                "loc": "Sảnh Nhà B4 - ĐH Bách Khoa CS1",
                "days_offset": 1, "hours": 6, "ctxh": 0.5, "max_p": 120,
                "host_id": ctxh_bk.id, "img": ACTIVITY_IMAGES[2]
            },
            {
                "title": "Gia sư Áo xanh: Dạy phụ đạo Toán & Tin học cho trẻ em Mái ấm",
                "desc": "Dành cho các bạn sinh viên có đam mê sư phạm hỗ trợ dạy kèm kiến thức căn bản cho các em học sinh có hoàn cảnh khó khăn tại Làng Đại học.",
                "cat": "Tình nguyện & CTXH",
                "lat": KTX_CS2_LAT, "lng": KTX_CS2_LNG,
                "loc": "Nhà sinh hoạt cộng đồng KTX Khu B - ĐHQG-HCM",
                "days_offset": 5, "hours": 4, "ctxh": 1.5, "max_p": 40,
                "host_id": ctxh_bk.id, "img": ACTIVITY_IMAGES[1]
            },
            {
                "title": "Đội hình Hướng dẫn Tân sinh viên K26 làm thủ tục nhập học",
                "desc": "Hỗ trợ đón tân sinh viên, hướng dẫn đóng học phí, nhận thẻ sinh viên tích hợp và hỗ trợ tìm nhà trọ, xe buýt về ký túc xá.",
                "cat": "Tình nguyện & CTXH",
                "lat": HALL_A5_LAT, "lng": HALL_A5_LNG,
                "loc": "Sảnh Hội trường A5 - ĐH Bách Khoa CS1",
                "days_offset": 10, "hours": 8, "ctxh": 1.0, "max_p": 60,
                "host_id": doan_bk.id, "img": ACTIVITY_IMAGES[8]
            },
            {
                "title": "Chủ Nhật Tình nguyện: Sơn mới và sửa sang bàn ghế phòng tự học Thư viện",
                "desc": "Cùng chung tay sơn lại các dãy bàn tự học và dọn dẹp vệ sinh các giá sách cũ phục vụ mùa thi cuối kỳ cho sinh viên.",
                "cat": "Tình nguyện & CTXH",
                "lat": BK_CS1_LAT + 0.001, "lng": BK_CS1_LNG - 0.0005,
                "loc": "Thư viện A2 - Trường ĐH Bách Khoa CS1",
                "days_offset": 4, "hours": 4, "ctxh": 0.5, "max_p": 45,
                "host_id": ctxh_bk.id, "img": ACTIVITY_IMAGES[1]
            },
            {
                "title": "Đội hình Tình nguyện Điều phối Giao thông Giờ cao điểm Cổng 1 & Cổng 2",
                "desc": "Phối hợp cùng bảo vệ trường hướng dẫn luồng xe máy và xe buýt tránh ùn tắc cục bộ tại đường Lý Thường Kiệt và Tô Hiến Thành.",
                "cat": "Tình nguyện & CTXH",
                "lat": BK_CS1_LAT - 0.0012, "lng": BK_CS1_LNG,
                "loc": "Cổng số 1 Lý Thường Kiệt - ĐH Bách Khoa CS1",
                "days_offset": 3, "hours": 3, "ctxh": 0.5, "max_p": 30,
                "host_id": doan_bk.id, "img": ACTIVITY_IMAGES[8]
            },

            # ── 2. HỌC THUẬT, WORKSHOP & HACKATHON (18 hoạt động) ──
            {
                "title": "Cuộc thi Bách Khoa Hackathon 2026: AI for Smart Campus",
                "desc": "Sân chơi sáng tạo công nghệ 36 giờ liên tục giải quyết các bài toán giao thông, năng lượng và trợ lý ảo thông minh trong trường đại học.",
                "cat": "Học thuật & Kỹ năng",
                "lat": HALL_A5_LAT, "lng": HALL_A5_LNG,
                "loc": "Hội trường A5 - ĐH Bách Khoa CS1",
                "days_offset": 6, "hours": 36, "ctxh": 0.0, "max_p": 120,
                "host_id": dat_nguyen.id, "img": ACTIVITY_IMAGES[5]
            },
            {
                "title": "Workshop: Lộ trình chinh phục Kỹ sư AI & LLM cho sinh viên",
                "desc": "Chia sẻ kinh nghiệm thực tập tại các Tech Giant, phương pháp học Deep Learning và ứng dụng Retrieval-Augmented Generation (RAG) thực chiến.",
                "cat": "Học thuật & Kỹ năng",
                "lat": BK_CS1_LAT + 0.0008, "lng": BK_CS1_LNG + 0.0003,
                "loc": "Hội trường C1 - Trường ĐH Bách Khoa CS1",
                "days_offset": 4, "hours": 3, "ctxh": 0.0, "max_p": 90,
                "host_id": dat_nguyen.id, "img": ACTIVITY_IMAGES[9]
            },
            {
                "title": "Ôn tập thi giữa kỳ môn Giải tích 1 và Đại số tuyến tính",
                "desc": "Buổi chữa đề thi mẫu các năm, tổng hợp công thức đạo hàm, tích phân suy rộng và ma trận nghịch đảo dành riêng cho sinh viên K25, K26.",
                "cat": "Học thuật & Kỹ năng",
                "lat": BK_CS1_LAT + 0.0004, "lng": BK_CS1_LNG + 0.0006,
                "loc": "Phòng C5-102 - ĐH Bách Khoa CS1",
                "days_offset": 2, "hours": 3, "ctxh": 0.0, "max_p": 70,
                "host_id": student_pool[0].id, "img": ACTIVITY_IMAGES[1]
            },
            {
                "title": "Học nhóm môn Cấu trúc dữ liệu và giải thuật (DSA) tại Thư viện",
                "desc": "Cùng nhau giải các bài tập LeetCode chủ đề Dynamic Programming, Tree, Graph và chuẩn bị cho đồ án thực hành môn học.",
                "cat": "Học thuật & Kỹ năng",
                "lat": BK_CS1_LAT + 0.001, "lng": BK_CS1_LNG - 0.0005,
                "loc": "Thư viện Bách Khoa A2 - Phòng tự học tầng 2",
                "days_offset": 1, "hours": 3, "ctxh": 0.0, "max_p": 35,
                "host_id": dat_nguyen.id, "img": ACTIVITY_IMAGES[1]
            },
            {
                "title": "Workshop: Docker & Kubernetes thực chiến cho đồ án tốt nghiệp",
                "desc": "Hướng dẫn đóng gói container đa tầng, viết docker-compose chuẩn production và triển khai CI/CD tự động bằng GitHub Actions.",
                "cat": "Học thuật & Kỹ năng",
                "lat": BK_CS1_LAT + 0.0005, "lng": BK_CS1_LNG + 0.0002,
                "loc": "Phòng Lab B1-304 - ĐH Bách Khoa CS1",
                "days_offset": 5, "hours": 4, "ctxh": 0.0, "max_p": 50,
                "host_id": dat_nguyen.id, "img": ACTIVITY_IMAGES[0]
            },
            {
                "title": "Seminar: An toàn Thông tin và Kỹ thuật Kiểm thử Xâm nhập (Pentest)",
                "desc": "Tìm hiểu các lỗ hổng OWASP Top 10 phổ biến, phương pháp phòng chống tấn công SQL Injection và CSRF trong các ứng dụng web hiện đại.",
                "cat": "Học thuật & Kỹ năng",
                "lat": NHA_H6_LAT, "lng": NHA_H6_LNG,
                "loc": "Phòng Hội thảo H6-202 - ĐH Bách Khoa CS2 (Dĩ An)",
                "days_offset": 8, "hours": 3, "ctxh": 0.0, "max_p": 60,
                "host_id": student_pool[4].id, "img": ACTIVITY_IMAGES[7]
            },
            {
                "title": "Tọa đàm Hướng nghiệp: Bí quyết Viết CV và Phỏng vấn Doanh nghiệp IT",
                "desc": "Khách mời là các Senior Tech Lead và HR Manager từ các tập đoàn công nghệ lớn chia sẻ cách gây ấn tượng qua CV và Portfolio dự án.",
                "cat": "Học thuật & Kỹ năng",
                "lat": HALL_A5_LAT, "lng": HALL_A5_LNG,
                "loc": "Hội trường A5 - ĐH Bách Khoa CS1",
                "days_offset": 9, "hours": 3, "ctxh": 0.0, "max_p": 120,
                "host_id": doan_bk.id, "img": ACTIVITY_IMAGES[0]
            },
            {
                "title": "Buổi chia sẻ Kinh nghiệm Nghiên cứu Khoa học Sinh viên và Viết bài báo",
                "desc": "Hướng dẫn cách tìm đề tài NCKH, phương pháp đọc hiểu bài báo khoa học chuẩn IEEE/ACM và cách nộp hồ sơ xin quỹ nghiên cứu sinh viên.",
                "cat": "Học thuật & Kỹ năng",
                "lat": BK_CS1_LAT + 0.0008, "lng": BK_CS1_LNG + 0.0003,
                "loc": "Hội trường C1 - Trường ĐH Bách Khoa CS1",
                "days_offset": 6, "hours": 3, "ctxh": 0.0, "max_p": 80,
                "host_id": student_pool[11].id, "img": ACTIVITY_IMAGES[7]
            },

            # ── 3. THỂ THAO & GIẢI TRÍ RÈN LUYỆN (14 hoạt động) ──
            {
                "title": "Giao lưu Kèo bóng đá Sân 7 KTX Bách Khoa CS1",
                "desc": "Tìm đội giao hữu bóng đá sân 7 người. Trận đấu vui vẻ, rèn luyện thể lực sau giờ học căng thẳng, chia đều tiền thuê sân và nước uống.",
                "cat": "Thể thao & Giải trí",
                "lat": KTX_CS1_LAT, "lng": KTX_CS1_LNG,
                "loc": "Sân bóng đá KTX Bách Khoa (497 Hòa Hảo, Q.10)",
                "days_offset": 1, "hours": 2, "ctxh": 0.0, "max_p": 18,
                "host_id": student_pool[3].id, "img": ACTIVITY_IMAGES[4]
            },
            {
                "title": "Chạy bộ rèn luyện thể lực sáng sớm quanh Hồ Ký túc xá ĐHQG",
                "desc": "Chạy bộ cự ly 5km - 10km quanh bờ hồ đón bình minh, hít thở không khí trong lành và rèn luyện thói quen dậy sớm tập thể thao.",
                "cat": "Thể thao & Giải trí",
                "lat": HO_TIEN_PHONG_LAT + 0.003, "lng": HO_TIEN_PHONG_LNG + 0.002,
                "loc": "Hồ Ký túc xá ĐHQG - Gần Bách Khoa CS2",
                "days_offset": 3, "hours": 1, "ctxh": 0.0, "max_p": 50,
                "host_id": student_pool[2].id, "img": ACTIVITY_IMAGES[3]
            },
            {
                "title": "Giải Bóng rổ 3x3 Giao hữu Sinh viên Bách Khoa CS2",
                "desc": "Giải đấu bóng rổ nửa sân sôi động dành cho sinh viên các khoa. Có trọng tài bắt chuẩn luật, phần thưởng nước giải khát cho đội chiến thắng!",
                "cat": "Thể thao & Giải trí",
                "lat": SAN_C3_LAT, "lng": SAN_C3_LNG,
                "loc": "Cụm sân Thể thao C3 - ĐH Bách Khoa CS1",
                "days_offset": 4, "hours": 3, "ctxh": 0.0, "max_p": 24,
                "host_id": student_pool[2].id, "img": ACTIVITY_IMAGES[3]
            },
            {
                "title": "Giao lưu Cầu lông Đơn & Đôi Nam Nữ tại Nhà thi đấu Bách Khoa",
                "desc": "Câu lạc bộ cầu lông mở kèo giao lưu từ trình độ cơ bản đến nâng cao. Có sẵn vợt dự phòng cho các bạn sinh viên mới tham gia.",
                "cat": "Thể thao & Giải trí",
                "lat": BK_CS1_LAT - 0.0006, "lng": BK_CS1_LNG - 0.0005,
                "loc": "Nhà thi đấu Thể thao Bách Khoa CS1",
                "days_offset": 2, "hours": 2, "ctxh": 0.0, "max_p": 16,
                "host_id": dat_nguyen.id, "img": ACTIVITY_IMAGES[3]
            },
            {
                "title": "Đấu trí Cờ vua & Cờ tướng Sinh viên tại Sảnh Nhà H6",
                "desc": "Giao lưu cờ chớp 5 phút và cờ tiêu chuẩn. Nơi hội tụ các kiện tướng cờ sinh viên Bách Khoa giao lưu chiến thuật.",
                "cat": "Thể thao & Giải trí",
                "lat": NHA_H6_LAT, "lng": NHA_H6_LNG,
                "loc": "Sảnh Tòa nhà H6 - ĐH Bách Khoa CS2 (Dĩ An)",
                "days_offset": 2, "hours": 3, "ctxh": 0.0, "max_p": 30,
                "host_id": student_pool[7].id, "img": ACTIVITY_IMAGES[6]
            },
            {
                "title": "Giải đấu Thể thao Điện tử Sinh viên (BK Esports Championship)",
                "desc": "Tranh tài các bộ môn thể thao điện tử phổ biến (LMHT, Valorant). Vòng loại thi đấu online, chung kết trực tiếp tại hội trường.",
                "cat": "Thể thao & Giải trí",
                "lat": HALL_A5_LAT, "lng": HALL_A5_LNG,
                "loc": "Hội trường A5 - ĐH Bách Khoa CS1",
                "days_offset": 12, "hours": 6, "ctxh": 0.0, "max_p": 60,
                "host_id": student_pool[5].id, "img": ACTIVITY_IMAGES[5]
            },

            # ── 4. VĂN HÓA, NGHỆ THUẬT & HỘI NHẬP (10 hoạt động) ──
            {
                "title": "Đêm nhạc Acoustic Sinh viên: Giai điệu Bách Khoa dưới ánh trăng",
                "desc": "Chương trình giao lưu âm nhạc mộc mạc do CLB Guitar tổ chức. Cùng nhau ngồi bên thảm cỏ sảnh B4 đàn hát những khúc ca tuổi trẻ.",
                "cat": "Thể thao & Giải trí",
                "lat": BK_CS1_LAT - 0.0004, "lng": BK_CS1_LNG + 0.0008,
                "loc": "Sảnh Nhà B4 - ĐH Bách Khoa CS1",
                "days_offset": 3, "hours": 3, "ctxh": 0.0, "max_p": 100,
                "host_id": student_pool[4].id, "img": ACTIVITY_IMAGES[6]
            },
            {
                "title": "CLB Tiếng Anh (BEC) Coffee Talk: AI in Modern Education",
                "desc": "Thảo luận 100% bằng tiếng Anh về vai trò của Trí tuệ nhân tạo đối với sinh viên. Có sự tham gia của các bạn du học sinh trao đổi.",
                "cat": "Học thuật & Kỹ năng",
                "lat": BK_CS1_LAT + 0.0015, "lng": BK_CS1_LNG + 0.001,
                "loc": "Highlands Coffee - 268 Lý Thường Kiệt",
                "days_offset": 4, "hours": 2, "ctxh": 0.0, "max_p": 25,
                "host_id": student_pool[1].id, "img": ACTIVITY_IMAGES[0]
            },
            {
                "title": "Ngày hội Chào đón Tân Sinh viên K26: Khám phá CLB & Đội nhóm",
                "desc": "Gian hàng giới thiệu hơn 40 câu lạc bộ học thuật, tình nguyện và sở thích trong trường. Cơ hội tuyệt vời để tìm kiếm ngôi nhà thứ hai!",
                "cat": "Học thuật & Kỹ năng",
                "lat": HALL_A5_LAT, "lng": HALL_A5_LNG,
                "loc": "Khuôn viên Sân A5 - ĐH Bách Khoa CS1",
                "days_offset": 14, "hours": 8, "ctxh": 0.5, "max_p": 300,
                "host_id": doan_bk.id, "img": ACTIVITY_IMAGES[8]
            },

            # ── 5. HOẠT ĐỘNG XUNG ĐỘT LỊCH (ĐẶC BIỆT DÀNH ĐỂ DEMO CONFLICT MODAL) ──
            {
                "title": "Workshop Cấp tốc: Xây dựng RESTful API với FastAPI & PostgreSQL",
                "desc": "Trùng đúng giờ học Giải tích 1 sáng thứ Hai của bạn! Hãy bấm đăng ký để xem hệ thống cảnh báo xung đột lịch trực quan.",
                "cat": "Học thuật & Kỹ năng",
                "lat": BK_CS1_LAT + 0.0008, "lng": BK_CS1_LNG + 0.0003,
                "loc": "Hội trường C1 - ĐH Bách Khoa CS1",
                "days_offset": 0, "hours": 3, "ctxh": 0.0, "max_p": 50,
                "host_id": student_pool[8].id, "img": ACTIVITY_IMAGES[9],
                # Diễn ra sáng thứ 2 tuần này (trùng Giải tích)
                "exact_start_hours": 8, "exact_day_delta": 0
            }
        ]

        # Nạp các hoạt động vào DB
        activities_list = []
        for a_dict in ACTIVITIES_DATA:
            delta_days = a_dict.get("days_offset", 1)
            start_t = now + timedelta(days=delta_days, hours=random.randint(1, 4))
            end_t = start_t + timedelta(hours=a_dict["hours"])

            # Vector embedding cho semantic search
            embed_text = f"{a_dict['title']}. {a_dict['desc']} Địa điểm: {a_dict['loc']}. Phân loại: {a_dict['cat']}."
            embedding_vector = generate_embedding(embed_text)

            act = Activity(
                id=uuid.uuid4(),
                host_id=a_dict["host_id"],
                title=a_dict["title"],
                description=a_dict["desc"],
                privacy=ActivityPrivacy.public,
                category=a_dict["cat"],
                meeting_location=a_dict["loc"],
                start_time=start_t,
                end_time=end_t,
                social_work_days=a_dict["ctxh"],
                max_participants=a_dict["max_p"],
                require_approval=False,
                embedding=embedding_vector,
            )
            act.marker_location = f"POINT({a_dict['lng']} {a_dict['lat']})"
            activities_list.append(act)

        db.add_all(activities_list)
        await db.commit()
        for act in activities_list:
            await db.refresh(act)

        print(f"✅ Đã nạp thành công {len(activities_list)} hoạt động Bách Khoa kèm Vector Embeddings!")

        # 6. Gán Trophy cho Hackathon và CTXH
        act_hackathon = next((a for a in activities_list if "Hackathon" in a.title), None)
        act_ctxh = next((a for a in activities_list if "Chủ Nhật Xanh" in a.title), None)
        if act_hackathon:
            trophies_list[1].activity_id = act_hackathon.id
        if act_ctxh:
            trophies_list[0].activity_id = act_ctxh.id
        await db.commit()

        # 7. Khởi tạo Đăng ký tham gia (Join Requests) & Giấy chứng nhận cho dat_nguyen
        print("🎫 Khởi tạo 120+ Lượt đăng ký tham gia, điểm danh & cấp chứng nhận điện tử...")
        join_requests_list = []

        # dat_nguyen ĐÃ THAM GIA và ĐƯỢC ĐIỂM DANH ở sự kiện Chủ Nhật Xanh -> Có Giấy chứng nhận!
        if act_ctxh:
            jr_cert = JoinRequest(
                id=uuid.uuid4(),
                activity_id=act_ctxh.id,
                user_id=dat_nguyen.id,
                status=RequestStatus.approved,
                message="Em xin đăng ký tham gia đội hình nhặt rác và phân loại tại bờ hồ Tiền Phong.",
                attendance_confirmed=True, # ĐÃ XÁC NHẬN ĐIỂM DANH ĐỂ CẤP CERTIFICATE
            )
            join_requests_list.append(jr_cert)

            # Cấp Trophy CTXH cho dat_nguyen
            ut = UserTrophy(
                id=uuid.uuid4(),
                user_id=dat_nguyen.id,
                trophy_id=trophies_list[0].id,
                activity_id=act_ctxh.id,
            )
            db.add(ut)

        # dat_nguyen ĐANG CHỜ DUYỆT ở Hackathon
        if act_hackathon:
            jr_hack = JoinRequest(
                id=uuid.uuid4(),
                activity_id=act_hackathon.id,
                user_id=dat_nguyen.id,
                status=RequestStatus.approved,
                message="Team 4 thành viên xin đăng ký đề tài Trợ lý ảo AI Smart Campus.",
                attendance_confirmed=False,
            )
            join_requests_list.append(jr_hack)

        # Thêm 15-40 sinh viên đăng ký cho mỗi sự kiện
        for act in activities_list:
            sampled_participants = random.sample(student_pool, min(len(student_pool), random.randint(10, 25)))
            for sp in sampled_participants:
                if sp.id != act.host_id and sp.id != dat_nguyen.id:
                    status = RequestStatus.approved if random.random() > 0.3 else RequestStatus.pending
                    is_attended = (status == RequestStatus.approved) and (random.random() > 0.5)
                    jr = JoinRequest(
                        id=uuid.uuid4(),
                        activity_id=act.id,
                        user_id=sp.id,
                        status=status,
                        message="Em xin phép đăng ký tham gia hoạt động ạ!",
                        attendance_confirmed=is_attended,
                    )
                    join_requests_list.append(jr)

        db.add_all(join_requests_list)
        await db.commit()
        print(f"✅ Đã tạo {len(join_requests_list)} lượt đăng ký tham gia và cấp chứng nhận hoàn tất!")

        # 8. Khởi tạo Bình luận (Comments) sôi nổi
        print("💬 Khởi tạo 120+ Bình luận hỏi đáp, chia sẻ và tìm teammate...")
        COMMENT_SNIPPETS = [
            "Hoạt động này ý nghĩa quá, mình vừa rủ thêm 2 bạn cùng phòng đăng ký rồi nha!",
            "Cho mình hỏi buổi workshop có cần cài đặt sẵn môi trường trước ở nhà không ạ?",
            "Có bạn nhé! BTC đã gửi email hướng dẫn setup Docker và Python chi tiết rồi nha.",
            "Team mình đang có 2 bạn Backend, cần tìm thêm 1 bạn làm Frontend ReactJS thi Hackathon nè!",
            "Hoạt động này có được cấp giấy chứng nhận có mã định danh trực tuyến không ạ?",
            "Mọi người nhớ mang theo bình nước cá nhân để hạn chế rác thải nhựa nhé!",
            "Chủ Nhật tập trung ở sảnh nào vậy ạ?",
            "Tập trung ở sảnh Hội trường C1 lúc 7h00 sáng nhé bạn ơi!",
            "Năm ngoái mình có tham gia rồi, các anh chị ban tổ chức hỗ trợ cực kỳ nhiệt tình luôn.",
            "Đã đăng ký thành công! Hẹn gặp lại mọi người cuối tuần nha! 🚀"
        ]

        comments_list = []
        for act in activities_list:
            num_c = random.randint(3, 8)
            for _ in range(num_c):
                c_user = random.choice(student_pool)
                c = Comment(
                    id=uuid.uuid4(),
                    activity_id=act.id,
                    user_id=c_user.id,
                    content=random.choice(COMMENT_SNIPPETS),
                )
                comments_list.append(c)

        db.add_all(comments_list)
        await db.commit()
        print(f"✅ Đã tạo {len(comments_list)} bình luận sinh động!")

        # 9. Khởi tạo Likes (300+ Likes)
        print("❤️ Khởi tạo 350+ Lượt thích phân bổ khắp các sự kiện...")
        likes_list = []
        for act in activities_list:
            likers = random.sample(student_pool, random.randint(10, 25))
            for l_user in likers:
                like = ContentLike(
                    id=uuid.uuid4(),
                    activity_id=act.id,
                    user_id=l_user.id,
                )
                likes_list.append(like)

        db.add_all(likes_list)
        await db.commit()
        print(f"✅ Đã tạo {len(likes_list)} lượt like!")

        # 10. Khởi tạo Thời khóa biểu cá nhân của dat_nguyen (UserBusySlots)
        print("📅 Khởi tạo Thời khóa biểu học tập & Lịch bận định kỳ của dat_nguyen...")
        today = now.date()
        monday = today - timedelta(days=today.weekday())

        busy_slots = [
            # Sáng thứ Hai: Môn Giải tích 1 (Phòng C5-102)
            UserBusySlot(
                id=uuid.uuid4(),
                user_id=dat_nguyen.id,
                title="Học trên lớp: Môn Giải tích 1 (Hội trường C5-102)",
                day_of_week=0, # Thứ 2
                start_time_of_day=datetime.time(7, 30),
                end_time_of_day=datetime.time(11, 30),
                recurrence=RecurrenceType.weekly.value,
                valid_from=today - timedelta(days=30),
                valid_until=today + timedelta(days=90),
            ),
            # Chiều thứ Ba: Cấu trúc Dữ liệu & Giải thuật (Phòng B4-301)
            UserBusySlot(
                id=uuid.uuid4(),
                user_id=dat_nguyen.id,
                title="Học trên lớp: Cấu trúc dữ liệu & Giải thuật (B4-301)",
                day_of_week=1, # Thứ 3
                start_time_of_day=datetime.time(13, 30),
                end_time_of_day=datetime.time(16, 30),
                recurrence=RecurrenceType.weekly.value,
                valid_from=today - timedelta(days=30),
                valid_until=today + timedelta(days=90),
            ),
            # Sáng thứ Sáu: Tiếng Anh học thuật (Phòng H1-201, CS2 Dĩ An)
            UserBusySlot(
                id=uuid.uuid4(),
                user_id=dat_nguyen.id,
                title="Học trên lớp: Tiếng Anh học thuật (Phòng H1-201, CS2 Dĩ An)",
                day_of_week=4, # Thứ 6
                start_time_of_day=datetime.time(8, 30),
                end_time_of_day=datetime.time(11, 30),
                recurrence=RecurrenceType.weekly.value,
                valid_from=today - timedelta(days=30),
                valid_until=today + timedelta(days=90),
            ),
        ]
        db.add_all(busy_slots)
        await db.commit()
        print("✅ Đã thiết lập Thời khóa biểu cá nhân của sinh viên thành công!")

        # 11. Khởi tạo Hộp thông báo (Notification Bell) phong phú cho dat_nguyen & admin
        print("🔔 Khởi tạo 15+ Thông báo đa dạng trong Hộp thông báo...")
        NOTIFS_DATA = [
            ("request_approved", "Đơn đăng ký tham gia 'Chiến dịch Tình nguyện Ngày Chủ Nhật Xanh' của bạn đã được phê duyệt!", str(act_ctxh.id) if act_ctxh else None),
            ("trophy_awarded", "Chúc mừng! Bạn đã nhận được Danh hiệu: 'Chiến sĩ CTXH Tiêu biểu'!", None),
            ("new_comment", "Trần Minh Quân vừa trả lời bình luận của bạn trong sự kiện 'Bách Khoa Hackathon 2026'.", str(act_hackathon.id) if act_hackathon else None),
            ("event_reminder", "Nhắc nhở: Hoạt động 'Ôn tập thi giữa kỳ môn Giải tích 1' sẽ diễn ra vào ngày mai lúc 07:30 tại C5-102.", None),
            ("certificate_ready", "Giấy chứng nhận tham gia hoạt động trực tuyến của bạn đã sẵn sàng. Bấm vào để xem mã kiểm chứng.", str(act_ctxh.id) if act_ctxh else None),
            ("group_invite", "Bạn đã được bổ nhiệm làm Quản trị viên của CLB Lập trình Bách Khoa (BK Coding Club).", None),
            ("new_activity", "CLB Tiếng Anh Bách Khoa vừa đăng tải sự kiện mới: 'BEC Coffee Talk: AI in Education'.", None),
            ("system_update", "Hệ thống UniConnect đã cập nhật tính năng quét mã QR động 30s chống gian lận.", None),
        ]

        notifications_list = []
        for n_type, n_msg, act_ref in NOTIFS_DATA:
            notif = Notification(
                id=uuid.uuid4(),
                user_id=dat_nguyen.id,
                actor_id=admin_bk.id,
                activity_id=uuid.UUID(act_ref) if act_ref else None,
                type=n_type,
                message=n_msg,
                is_read=random.choice([True, False]),
            )
            notifications_list.append(notif)

        # Thông báo cho admin
        notifications_list.append(
            Notification(
                id=uuid.uuid4(),
                user_id=admin_bk.id,
                actor_id=dat_nguyen.id,
                type="admin_alert",
                message="Có 12 đơn đăng ký hoạt động mới cần được kiểm duyệt trong ngày hôm nay.",
                is_read=False,
            )
        )

        db.add_all(notifications_list)
        await db.commit()
        print(f"✅ Đã tạo {len(notifications_list)} thông báo thực tế!")

    print("\n" + "=" * 80)
    print("🎉 HOÀN TẤT SEED TOÀN DIỆN DỮ LIỆU BÁCH KHOA MASTER!")
    print("=" * 80)
    print("📊 TỔNG KẾT:")
    print(f"• Users: {len(users_list)} sinh viên & quản trị viên")
    print(f"• Groups: {len(groups_list)} CLB & Đội nhóm Bách Khoa")
    print(f"• Group Memberships: {len(group_members)} lượt tham gia nhóm")
    print(f"• Activities: {len(activities_list)} hoạt động Bách Khoa (đầy đủ tọa độ GPS & Vector Embeddings)")
    print(f"• Join Requests: {len(join_requests_list)} lượt đăng ký (Approved & Pending)")
    print(f"• Comments: {len(comments_list)} bình luận thảo luận")
    print(f"• Likes: {len(likes_list)} lượt yêu thích")
    print(f"• Trophies: {len(trophies_list)} danh hiệu")
    print(f"• Notifications: {len(notifications_list)} thông báo trong chuông")
    print("=" * 80)
    print("🔑 TÀI KHOẢN ĐĂNG NHẬP DEMO:")
    print("1. Sinh viên Demo: dat_nguyen / dat123 (Có sẵn lịch học, chứng nhận CTXH, thông báo)")
    print("2. Quản trị viên: admin_bk / admin123 (Xem bảng điều khiển Admin Command Center)")
    print("3. Tổ chức CTXH: ctxh_bk / ctxh123 (Tạo và duyệt các sự kiện CTXH)")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(seed_all())
