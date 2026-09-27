"""
Seed Activities, Groups, Trophies and Past History for UniConnect Demo.
- Groups: CLB Gia Su Bach Khoa, CLB Robot BK, CLB The Thao, CLB Tin Hoc, Doi CTXH
- Upcoming Main CTXH Activity: "Chiến dịch Gia sư Áo xanh 10/2026 — Lớp Học Tình Thương Cho Em"
  + Trophy: "Tình nguyện viên gia sư áo xanh 10/2026"
  + CTXH: 3.0 days
  + QR Code + GPS checkin (radius 500m around 10.929718, 107.250381)
  + Active right now so host and user can immediately demo rotating QR + GPS check-in!
- Upcoming Main Normal Activity: "Giải Cầu Lông Đôi Nam Nữ Giao Lưu Sinh Viên Bách Khoa K22"
- Upcoming CTXH Activity 2: "Chiến dịch Chủ Nhật Xanh 10/2026 — Thu gom Pin cũ và Rác điện tử" (2.0 days CTXH) -> Total 5.0 days in 2 weeks for AI!
- Upcoming Conflict Activity: "Hội thảo Xu hướng Kỹ thuật & Khởi nghiệp BK 2026" (conflicts with user's busy slot)
- Busy Slot for dat_nguyenthese80: "Lớp Chuyên đề Cơ khí & Robot K22"
- 4 Past Activities with 4 Unique Trophies for dat_nguyenthese80 (8.0 days CTXH, 4 trophies, Gold rank!)
- Gemini vector embeddings for semantic search
"""

import asyncio
import datetime
from datetime import timezone, timedelta, time, date
import uuid
import random
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text, select

from app.core.config import settings
from app.modules.users.models import User, UserRole
from app.modules.groups.models import Group, GroupMember, GroupRole, GroupPrivacy
from app.modules.activities.models import Activity, ActivityPrivacy
from app.modules.trophies.models import Trophy, UserTrophy
from app.modules.participation.models import JoinRequest, RequestStatus
from app.modules.calendar.models import UserBusySlot, RecurrenceType
from app.modules.chat.embeddings import generate_embedding

# User location (Long Khanh, Dong Nai)
USER_LAT = 10.929718
USER_LNG = 107.250381

async def seed_data():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.datetime.now(timezone.utc)

    async with async_session() as db:
        print("🧹 1. Dọn dẹp dữ liệu hoạt động, nhóm, danh hiệu cũ...")
        await db.execute(text("TRUNCATE TABLE join_requests, comments, content_likes, activity_cohosts, activity_cohost_invitations, custom_forms, form_fields, trophy_grant_requests, user_trophies, trophies, user_busy_slots, activities, group_members, group_join_requests, groups CASCADE;"))
        await db.commit()

        # 2. Lấy các users chính
        q = await db.execute(select(User).where(User.username.in_(["dat_nguyenthese80", "minh_khoi", "khanh_vy", "hoang_nam", "bao_long", "phuong_thao", "ctxh_bk", "doan_bk"])))
        users_map = {u.username: u for u in q.scalars().all()}
        
        q_students = await db.execute(select(User).where(User.role == UserRole.student))
        all_students = q_students.scalars().all()
        
        dat_user = users_map.get("dat_nguyenthese80")
        khanh_vy = users_map.get("khanh_vy")
        minh_khoi = users_map.get("minh_khoi")
        bao_long = users_map.get("bao_long")
        hoang_nam = users_map.get("hoang_nam")
        phuong_thao = users_map.get("phuong_thao")
        ctxh_bk = users_map.get("ctxh_bk")
        doan_bk = users_map.get("doan_bk")

        print("🏢 2. Tạo các Câu lạc bộ & Tổ chức (Groups)...")
        # CLB Gia Sư Bách Khoa
        grp_gia_su = Group(
            id=uuid.uuid4(),
            name="CLB Gia Sư Bách Khoa - BK Tutor Club",
            description="Nơi quy tụ sinh viên Bách Khoa nhiệt huyết, tổ chức các lớp dạy học miễn phí, gia sư tình nguyện cho học sinh có hoàn cảnh khó khăn.",
            public_description="Chào mừng bạn đến với CLB Gia Sư Bách Khoa! Chúng mình cùng nhau lan tỏa tri thức và niềm vui học tập đến các em nhỏ.",
            private_description="Nhóm Zalo nội bộ thành viên CLB Gia Sư: https://zalo.me/g/bktutor2026. Lịch sinh hoạt định kỳ vào tối thứ 6.",
            owner_id=khanh_vy.id if khanh_vy else dat_user.id,
            privacy=GroupPrivacy.public,
            allow_member_activities=True,
            require_approval=False,
            avatar_url="https://images.unsplash.com/photo-1577896851231-70ef18881754?auto=format&fit=crop&w=400&q=80",
            created_at=now - timedelta(days=60)
        )
        
        # CLB Cơ Khí & Chế Tạo Robot BK
        grp_robot = Group(
            id=uuid.uuid4(),
            name="CLB Robot & Sáng Tạo Cơ Khí BK",
            description="Câu lạc bộ học thuật dành cho sinh viên đam mê Chế tạo máy, Cơ điện tử, Robotics, IoT và tham gia các giải Robocon sinh viên.",
            public_description="Cùng nhau thiết kế mô hình 3D, gia công CNC, lập trình vi điều khiển và chế tạo robot thi đấu.",
            private_description="Kho linh kiện phòng lab H6 Cơ Khí: Tủ B2. Vui lòng ghi sổ mượn đồ khi sử dụng linh kiện.",
            owner_id=minh_khoi.id if minh_khoi else dat_user.id,
            privacy=GroupPrivacy.public,
            allow_member_activities=True,
            require_approval=False,
            avatar_url="https://images.unsplash.com/photo-1485827404703-89b55fcc595e?auto=format&fit=crop&w=400&q=80",
            created_at=now - timedelta(days=70)
        )

        # CLB Cầu Lông & Thể Thao BK
        grp_sports = Group(
            id=uuid.uuid4(),
            name="CLB Thể Thao & Cầu Lông Sinh Viên BK",
            description="Sân chơi rèn luyện sức khỏe, giao lưu kết nối đam mê cầu lông, bóng đá, bóng bàn cho sinh viên và cựu sinh viên Bách Khoa.",
            public_description="Tập luyện cố định vào các chiều thứ 3, 5, 7. Tổ chức các giải đấu giao hữu mở rộng mỗi tháng.",
            private_description="Quỹ cầu và tiền sân chuyển khoản thủ quỹ trước ngày 10 hàng tháng. Sân tập chính: Nhà thi đấu C3.",
            owner_id=bao_long.id if bao_long else dat_user.id,
            privacy=GroupPrivacy.public,
            allow_member_activities=True,
            require_approval=False,
            avatar_url="https://images.unsplash.com/photo-1521537634581-0dced2fee2ef?auto=format&fit=crop&w=400&q=80",
            created_at=now - timedelta(days=65)
        )

        # CLB Tin Học Bách Khoa
        grp_it = Group(
            id=uuid.uuid4(),
            name="CLB Tin Học - BK IT Club",
            description="Cộng đồng sinh viên lập trình, phát triển phần mềm, trí tuệ nhân tạo và an toàn thông tin tại ĐH Bách Khoa.",
            public_description="Chia sẻ kinh nghiệm làm dự án, luyện thuật toán LeetCode, tham gia Hackathon và kết nối nhà tuyển dụng.",
            private_description="Discord server: https://discord.gg/bkitclub. Nhóm nghiên cứu AI họp vào 19:30 thứ 4.",
            owner_id=hoang_nam.id if hoang_nam else dat_user.id,
            privacy=GroupPrivacy.public,
            allow_member_activities=True,
            require_approval=False,
            avatar_url="https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&w=400&q=80",
            created_at=now - timedelta(days=80)
        )

        # Ban Công Tác Xã Hội BK
        grp_ctxh = Group(
            id=uuid.uuid4(),
            name="Ban Công Tác Xã Hội - ĐH Bách Khoa",
            description="Tổ chức chính thức điều phối các phong trào tình nguyện, Mùa Hè Xanh, Tiếp Sức Mùa Thi và cấp ngày CTXH cho sinh viên trường.",
            public_description="Trang thông tin chính thống về các hoạt động cộng đồng, thiện nguyện của sinh viên Bách Khoa.",
            private_description="Đầu mối phụ trách hồ sơ minh chứng: Văn phòng Đoàn Thanh niên - Hội Sinh viên P.102.",
            owner_id=ctxh_bk.id if ctxh_bk else dat_user.id,
            privacy=GroupPrivacy.public,
            allow_member_activities=True,
            require_approval=False,
            avatar_url="https://images.unsplash.com/photo-1469571486292-0ba58a3f068b?auto=format&fit=crop&w=400&q=80",
            created_at=now - timedelta(days=100)
        )

        db.add_all([grp_gia_su, grp_robot, grp_sports, grp_it, grp_ctxh])
        await db.flush()

        # Thêm thành viên cho các nhóm
        members = [
            # dat_user tham gia CLB Gia Sư, CLB Robot, CLB Thể Thao
            GroupMember(group_id=grp_gia_su.id, user_id=dat_user.id, role=GroupRole.member),
            GroupMember(group_id=grp_robot.id, user_id=dat_user.id, role=GroupRole.member),
            GroupMember(group_id=grp_sports.id, user_id=dat_user.id, role=GroupRole.member),
            # khanh_vy là admin CLB Gia Sư
            GroupMember(group_id=grp_gia_su.id, user_id=khanh_vy.id, role=GroupRole.admin),
            # minh_khoi là admin CLB Robot
            GroupMember(group_id=grp_robot.id, user_id=minh_khoi.id, role=GroupRole.admin),
            # bao_long là admin CLB Thể Thao
            GroupMember(group_id=grp_sports.id, user_id=bao_long.id, role=GroupRole.admin),
            # hoang_nam là admin CLB Tin Học
            GroupMember(group_id=grp_it.id, user_id=hoang_nam.id, role=GroupRole.admin),
            # phuong_thao tham gia CLB Gia Sư
            GroupMember(group_id=grp_gia_su.id, user_id=phuong_thao.id, role=GroupRole.member),
        ]
        db.add_all(members)
        await db.flush()
        print("✅ Đã tạo xong 5 Câu lạc bộ và gán quyền thành viên!")

        print("🌟 3. Tạo Hoạt động CTXH tâm điểm (CLB Gia Sư Bách Khoa + Trophy)...")
        # Hoạt động 1: Tâm điểm CTXH + Điểm danh QR & GPS
        # Đang diễn ra NGAY LÚC NÀY: bắt đầu 30 phút trước, kết thúc 3 giờ sau
        # Để host (khanh_vy) có nút Hiển thị QR và dat_nguyenthese80 có nút Điểm danh QR ngay tức thì!
        act_giasu_id = uuid.uuid4()
        act_giasu_desc = (
            "Chiến dịch 'Gia sư Áo xanh Tháng 10/2026' do CLB Gia Sư Bách Khoa phối hợp cùng Trung tâm Học tập Cộng đồng tổ chức.\n\n"
            "📌 GIỚI THIỆU:\n"
            "Chương trình nhằm hỗ trợ củng cố kiến thức các môn Toán, Tiếng Anh và Khoa học Tự nhiên cho hơn 60 em học sinh có hoàn cảnh khó khăn tại địa phương. "
            "Đây là cơ hội tuyệt vời để các bạn sinh viên Bách Khoa rèn luyện kỹ năng sư phạm, giao tiếp và lan tỏa ngọn lửa tri thức đến cộng đồng.\n\n"
            "📋 YÊU CẦU NGƯỜI THAM GIA:\n"
            "- Đối tượng: Sinh viên năm 1 đến năm 4 tất cả các khoa của ĐH Bách Khoa.\n"
            "- Tinh thần: Nhiệt tình, kiên nhẫn, yêu thương trẻ em.\n"
            "- Trang phục: Áo thun tình nguyện của CLB hoặc áo đồng phục trường Bách Khoa lịch sự.\n"
            "- Chuẩn bị: Bút, vở nháp, thước kẻ và giáo trình tóm tắt do CLB cung cấp trước.\n\n"
            "⏰ LỊCH TRÌNH CHI TIẾT:\n"
            "• 07:30 - 08:00: Tập trung tại Trung tâm Học tập Cộng đồng, quét mã QR điểm danh GPS.\n"
            "• 08:00 - 08:30: Phân chia nhóm kèm cặp học sinh theo khối lớp (1 kèm 2).\n"
            "• 08:30 - 10:30: Hướng dẫn ôn tập lý thuyết và giải bài tập thực hành môn Toán & Tiếng Anh.\n"
            "• 10:30 - 11:30: Tổ chức sinh hoạt tập thể, trò chơi đố vui có thưởng và trao quà cho các em.\n"
            "• 11:30 - 12:00: Họp rút kinh nghiệm, ký xác nhận hoàn thành và kết thúc buổi học.\n\n"
            "💰 KINH PHÍ & QUYỀN LỢI:\n"
            "- Hoàn toàn MIỄN PHÍ tham gia. CLB hỗ trợ nước uống và bữa ăn trưa nhẹ.\n"
            "- Cấp 3.0 NGÀY CÔNG TÁC XÃ HỘI (CTXH) chính thức theo quy chuẩn trường.\n\n"
            "📍 ĐỊA ĐIỂM:\n"
            "Trung tâm Học tập Cộng đồng Long Khánh (Đường Nguyễn Thị Minh Khai, P. Xuân An, TP. Long Khánh). "
            "Gửi xe miễn phí tại khuôn viên trung tâm."
        )

        act_giasu = Activity(
            id=act_giasu_id,
            host_id=khanh_vy.id if khanh_vy else dat_user.id,
            group_id=grp_gia_su.id,
            title="Chiến dịch Gia sư Áo xanh 10/2026 — Lớp Học Tình Thương Cho Em",
            description=act_giasu_desc,
            private_description="Tập trung tại phòng hội trường số 2. Gặp bạn Vy (Trưởng ban điều phối - SĐT: 0912345678) để nhận giáo trình.",
            category="Volunteer",
            social_work_days=3.0,
            marker_location=f"SRID=4326;POINT({USER_LNG} {USER_LAT})",
            meeting_location="Trung tâm Học tập Cộng đồng Long Khánh (Gần Công viên Bia Chiến Thắng)",
            start_time=now - timedelta(minutes=30),  # Đang diễn ra
            end_time=now + timedelta(hours=3, minutes=30),
            max_participants=40,
            current_participants=24,
            privacy=ActivityPrivacy.public,
            require_approval=False,
            attendance_mode="qr_code",
            check_in_radius=500,  # 500m quanh vị trí người dùng
            check_in_code="GSBK2026",
            created_at=now - timedelta(days=5),
        )
        
        # Tạo Trophy cho hoạt động này
        trophy_giasu = Trophy(
            id=uuid.uuid4(),
            name="Tình nguyện viên gia sư áo xanh 10/2026",
            description="Vinh danh tình nguyện viên xuất sắc tham gia giảng dạy và hỗ trợ học sinh có hoàn cảnh khó khăn tại Chiến dịch Gia sư Áo xanh Tháng 10/2026.",
            activity_id=act_giasu_id,
            created_at=now - timedelta(days=5),
        )
        
        db.add(act_giasu)
        db.add(trophy_giasu)
        await db.flush()

        # Thêm join request cho dat_nguyenthese80 (đã approved, chưa check-in -> để test nút Quét QR / Điểm danh)
        req_dat = JoinRequest(
            id=uuid.uuid4(),
            activity_id=act_giasu_id,
            user_id=dat_user.id,
            status=RequestStatus.approved,
            message="Em rất muốn tham gia giảng dạy môn Toán và hỗ trợ các em nhỏ!",
            attendance_confirmed=False,  # Chưa điểm danh -> sẵn sàng bấm check in trong video
            created_at=now - timedelta(days=3)
        )
        db.add(req_dat)

        # Thêm 23 bạn sinh viên đã đăng ký tham gia (đạt 24 người bao gồm cả host)
        added_giasu_count = 1  # req_dat counted
        for other_u in all_students:
            if other_u and other_u.id != dat_user.id and other_u.id != khanh_vy.id:
                if added_giasu_count >= 23:
                    break
                db.add(JoinRequest(
                    id=uuid.uuid4(),
                    activity_id=act_giasu_id,
                    user_id=other_u.id,
                    status=RequestStatus.approved,
                    attendance_confirmed=random.choice([True, False]),
                    created_at=now - timedelta(days=random.randint(1, 4))
                ))
                added_giasu_count += 1

        print("🏸 4. Tạo Hoạt động Thường tâm điểm (CLB Cầu Lông & Thể Thao BK)...")
        # Hoạt động 2: Hoạt động bình thường (Thể thao / Thư giãn)
        act_caulong_id = uuid.uuid4()
        act_caulong_desc = (
            "Giải Cầu Lông Đôi Nam Nữ Giao Lưu Sinh Viên Bách Khoa K22 — Sân Cầu Lông Thể Thao Long Khánh.\n\n"
            "📌 GIỚI THIỆU:\n"
            "Nhằm tạo sân chơi lành mạnh, giải tỏa căng thẳng sau những tuần học đồ án căng thẳng và gắn kết tinh thần đồng môn K22 Bách Khoa. "
            "Giải đấu thi đấu theo thể thức đôi nam nữ phối hợp và đôi nam phong trào, cọ xát vui là chính!\n\n"
            "📋 YÊU CẦU NGƯỜI THAM GIA:\n"
            "- Trình độ: Trung bình - khá (biết phát cầu, đập cầu cơ bản, di chuyển nhịp nhàng).\n"
            "- Trang phục: Đồ thể thao thoáng mát, mang GIÀY ĐẾ KẾP chuyên dụng cho sân thảm cầu lông.\n"
            "- Dụng cụ: Tự túc vợt cá nhân và khăn lau mồ hôi. CLB tài trợ cầu thi đấu Hải Yến.\n\n"
            "⏰ LỊCH TRÌNH:\n"
            "• 08:00 - 08:15: Tập trung tại cụm sân 3 và 4, bốc thăm chia bảng đấu.\n"
            "• 08:15 - 08:30: Khởi động ép dẻo toàn thân, đánh cầu làm quen sân.\n"
            "• 08:30 - 10:15: Thi đấu vòng tròn tính điểm chọn ra 4 đội xuất sắc nhất vào Bán kết.\n"
            "• 10:15 - 11:00: Trận Chung kết nảy lửa tranh cúp vô địch.\n"
            "• 11:00 - 11:30: Trao huy chương lưu niệm, chụp ảnh check-in và liên hoan nước mía giao lưu.\n\n"
            "💰 CHI PHÍ: 30.000đ/bạn (bao gồm tiền thuê sân thảm 3 tiếng và cầu thi đấu). Nước suối miễn phí.\n"
            "📍 ĐỊA ĐIỂM: Sân Cầu Lông Thể Thao Tuổi Trẻ (Đường Hùng Vương, P. Xuân Bình, TP. Long Khánh). Có chỗ để xe máy rộng rãi."
        )

        act_caulong = Activity(
            id=act_caulong_id,
            host_id=bao_long.id if bao_long else dat_user.id,
            group_id=grp_sports.id,
            title="Giải Cầu Lông Đôi Nam Nữ Giao Lưu Sinh Viên Bách Khoa K22",
            description=act_caulong_desc,
            private_description="Nhóm Zalo giải cầu lông: https://zalo.me/g/caulongk22bk. Liên hệ Long (SĐT: 0988776655).",
            category="Sports",
            social_work_days=0.0,
            marker_location=f"SRID=4326;POINT({USER_LNG + 0.004} {USER_LAT + 0.003})",  # Cách vị trí user ~450m
            meeting_location="Sân Cầu Lông Thể Thao Tuổi Trẻ (Đường Hùng Vương, TP. Long Khánh)",
            start_time=now + timedelta(days=2, hours=1),
            end_time=now + timedelta(days=2, hours=4, minutes=30),
            max_participants=20,
            current_participants=14,
            privacy=ActivityPrivacy.public,
            require_approval=False,
            attendance_mode="auto",
            check_in_radius=300,
            created_at=now - timedelta(days=4),
        )
        db.add(act_caulong)

        print("🌿 5. Tạo Hoạt động CTXH thứ 2 (2.0 ngày CTXH) để AI Chatbot gợi ý đủ 5 ngày CTXH...")
        # Hoạt động 3: CTXH 2.0 ngày -> Kết hợp hoạt động Gia Sư (3.0 ngày) = ĐỦ ĐÚNG 5.0 NGÀY CTXH TRONG 2 TUẦN!
        act_chunhatxanh_id = uuid.uuid4()
        act_chunhatxanh = Activity(
            id=act_chunhatxanh_id,
            host_id=phuong_thao.id if phuong_thao else dat_user.id,
            group_id=grp_ctxh.id,
            title="Chiến dịch Ngày Chủ Nhật Xanh 10/2026 — Thu Gom Rác Thải Nhựa & Đổi Pin Cũ",
            description=(
                "Chiến dịch Chủ Nhật Xanh phối hợp cùng Ban Công tác Xã hội ĐH Bách Khoa tổ chức gian hàng thu gom rác thải điện tử, "
                "đổi pin cũ lấy cây xanh và dọn dẹp vệ sinh môi trường đô thị quanh khu vực công viên trung tâm.\n"
                "Tham gia đầy đủ 1 buổi được cấp 2.0 NGÀY CÔNG TÁC XÃ HỘI (CTXH) chính thức."
            ),
            category="Volunteer",
            social_work_days=2.0,
            marker_location=f"SRID=4326;POINT({USER_LNG - 0.003} {USER_LAT - 0.002})",
            meeting_location="Công viên Vườn hoa Bia Chiến Thắng Long Khánh",
            start_time=now + timedelta(days=8, hours=1),
            end_time=now + timedelta(days=8, hours=5),
            max_participants=50,
            current_participants=28,
            privacy=ActivityPrivacy.public,
            require_approval=False,
            attendance_mode="qr_code",
            check_in_radius=400,
            created_at=now - timedelta(days=2),
        )
        db.add(act_chunhatxanh)

        print("🤖 6. Tạo các hoạt động học thuật & hoạt động xung đột lịch bận...")
        # Hoạt động 4: Workshop Robot
        act_robot = Activity(
            id=uuid.uuid4(),
            host_id=minh_khoi.id if minh_khoi else dat_user.id,
            group_id=grp_robot.id,
            title="Workshop Lập Trình Robot Mini Dò Line & Điều Khiển Cánh Tay Robot K22",
            description="Buổi thực hành lập trình vi điều khiển STM32/ESP32, lắp ráp cảm biến quang dò line và vận hành mô hình cánh tay robot 4 bậc tự do.",
            category="Study",
            social_work_days=0.0,
            marker_location=f"SRID=4326;POINT({USER_LNG + 0.002} {USER_LAT - 0.004})",
            meeting_location="Phòng Lab Công nghệ Không gian Mở (Tầng 2 Thư viện Long Khánh)",
            start_time=now + timedelta(days=4, hours=2),
            end_time=now + timedelta(days=4, hours=5),
            max_participants=25,
            current_participants=18,
            privacy=ActivityPrivacy.public,
            require_approval=True,
            attendance_mode="manual",
            created_at=now - timedelta(days=3),
        )
        db.add(act_robot)

        # Hoạt động 5: Seminar trùng giờ với Lịch học của User (để demo Conflict Detection)
        # Diễn ra vào chiều ngày mai từ 14:00 đến 16:30
        conflict_start = (now + timedelta(days=1)).replace(hour=14, minute=0, second=0, microsecond=0)
        conflict_end = conflict_start + timedelta(hours=2, minutes=30)
        
        act_conflict = Activity(
            id=uuid.uuid4(),
            host_id=hoang_nam.id if hoang_nam else dat_user.id,
            group_id=grp_it.id,
            title="Hội Thảo Trí Tuệ Nhân Tạo & Xu Hướng Nghề Nghiệp Kỹ Thuật 2026",
            description="Chia sẻ từ các chuyên gia đầu ngành về ứng dụng Generative AI trong kỹ thuật chế tạo, phân tích dữ liệu và định hướng đồ án tốt nghiệp.",
            category="Study",
            social_work_days=0.0,
            marker_location=f"SRID=4326;POINT({USER_LNG + 0.005} {USER_LAT + 0.002})",
            meeting_location="Hội trường Trung tâm Văn hóa & Triển lãm Long Khánh",
            start_time=conflict_start,
            end_time=conflict_end,
            max_participants=60,
            current_participants=35,
            privacy=ActivityPrivacy.public,
            require_approval=False,
            attendance_mode="auto",
            created_at=now - timedelta(days=1),
        )
        db.add(act_conflict)

        # Tạo Lịch bận cá nhân cho dat_nguyenthese80 trùng đúng khung giờ này!
        busy_slot_dat = UserBusySlot(
            id=uuid.uuid4(),
            user_id=dat_user.id,
            title="Học Chuyên đề Kỹ thuật Cơ khí K22 (Thầy Thắng)",
            recurrence="none",
            start_datetime=conflict_start - timedelta(minutes=15),
            end_datetime=conflict_end + timedelta(minutes=15),
        )
        db.add(busy_slot_dat)

        print("🏆 7. Tạo 4 Hoạt động ĐÃ DIỄN RA trong quá khứ kèm 4 Danh hiệu Độc nhất vô nhị...")
        # Hoạt động quá khứ 1: Mùa Hè Xanh (5.0 ngày CTXH)
        past_act_1_id = uuid.uuid4()
        past_act_1 = Activity(
            id=past_act_1_id,
            host_id=ctxh_bk.id if ctxh_bk else dat_user.id,
            group_id=grp_ctxh.id,
            title="Chiến dịch Mùa Hè Xanh 2026 — Mặt trận Xã Xuân Lập & Bảo Quang",
            description="Chiến dịch tình nguyện cao điểm Mùa Hè Xanh 2026, tham gia xây dựng tuyến đường nông thôn mới, sửa chữa điện gia dụng và dạy học cho thiếu nhi.",
            category="Volunteer",
            social_work_days=5.0,
            marker_location=f"SRID=4326;POINT({USER_LNG} {USER_LAT})",
            meeting_location="UBND Xã Xuân Lập, TP. Long Khánh",
            start_time=now - timedelta(days=45),
            end_time=now - timedelta(days=40),
            max_participants=50,
            current_participants=50,
            privacy=ActivityPrivacy.public,
            attendance_mode="manual",
            created_at=now - timedelta(days=50),
        )
        trophy_1 = Trophy(
            id=uuid.uuid4(),
            name="Chiến sĩ Mùa Hè Xanh Kiên Cường 2026",
            description="Vinh danh chiến sĩ đã cống hiến trọn vẹn nhiệt huyết tuổi trẻ, xuất sắc hoàn thành mọi công trình thanh niên tại mặt trận nông thôn Mùa Hè Xanh 2026.",
            activity_id=past_act_1_id,
            created_at=now - timedelta(days=50),
        )
        db.add(past_act_1)
        db.add(trophy_1)

        # Hoạt động quá khứ 2: Hiến máu nhân đạo (1.0 ngày CTXH)
        past_act_2_id = uuid.uuid4()
        p2_start = now - timedelta(days=28, hours=6)
        p2_end = p2_start + timedelta(hours=4)
        past_act_2 = Activity(
            id=past_act_2_id,
            host_id=ctxh_bk.id if ctxh_bk else dat_user.id,
            group_id=grp_ctxh.id,
            title="Ngày Hội Hiến Máu Tình Nguyện Giọt Hồng Bách Khoa 08/2026",
            description="Chương trình hiến máu nhân đạo đợt 2 năm 2026 phối hợp cùng Bệnh viện Truyền máu Huyết học.",
            category="Volunteer",
            social_work_days=1.0,
            marker_location=f"SRID=4326;POINT({USER_LNG} {USER_LAT})",
            meeting_location="Bệnh viện Đa khoa Khu vực Long Khánh",
            start_time=p2_start,
            end_time=p2_end,
            max_participants=100,
            current_participants=92,
            privacy=ActivityPrivacy.public,
            attendance_mode="manual",
            created_at=now - timedelta(days=32),
        )
        trophy_2 = Trophy(
            id=uuid.uuid4(),
            name="Trái Tim Hồng Nhân Ái Bách Khoa 2026",
            description="Tuyên dương nghĩa cử cao đẹp hiến máu cứu người, sẻ chia giọt máu hồng vì sự sống của cộng đồng.",
            activity_id=past_act_2_id,
            created_at=now - timedelta(days=32),
        )
        db.add(past_act_2)
        db.add(trophy_2)

        # Hoạt động quá khứ 3: Giải chạy Marathon (0 ngày CTXH)
        past_act_3_id = uuid.uuid4()
        p3_start = now - timedelta(days=20, hours=5)
        p3_end = p3_start + timedelta(hours=3)
        past_act_3 = Activity(
            id=past_act_3_id,
            host_id=bao_long.id if bao_long else dat_user.id,
            group_id=grp_sports.id,
            title="Giải Marathon Tiếp Sức Sinh Viên Bách Khoa — Chạy Vì Tương Lai 2026",
            description="Giải chạy phong trào cự ly 10km rèn luyện sức bền và ý chí kiên trì của sinh viên Bách Khoa.",
            category="Sports",
            social_work_days=0.0,
            marker_location=f"SRID=4326;POINT({USER_LNG} {USER_LAT})",
            meeting_location="Quảng trường Công viên Long Khánh",
            start_time=p3_start,
            end_time=p3_end,
            max_participants=80,
            current_participants=75,
            privacy=ActivityPrivacy.public,
            attendance_mode="manual",
            created_at=now - timedelta(days=25),
        )
        trophy_3 = Trophy(
            id=uuid.uuid4(),
            name="Đôi Chân Thép Tiên Phong BK Cup 2026",
            description="Chứng nhận vận động viên hoàn thành xuất sắc cự ly chạy việt dã 10km với thành tích ấn tượng.",
            activity_id=past_act_3_id,
            created_at=now - timedelta(days=25),
        )
        db.add(past_act_3)
        db.add(trophy_3)

        # Hoạt động quá khứ 4: Tái chế Rác thải Nhựa (2.0 ngày CTXH)
        past_act_4_id = uuid.uuid4()
        p4_start = now - timedelta(days=14, hours=6)
        p4_end = p4_start + timedelta(hours=4)
        past_act_4 = Activity(
            id=past_act_4_id,
            host_id=phuong_thao.id if phuong_thao else dat_user.id,
            group_id=grp_ctxh.id,
            title="Chiến dịch Phân Loại Rác & Tái Chế Nhựa Sinh Thái 08/2026",
            description="Tuyên truyền phân loại rác tại nguồn, thu gom chai nhựa tái chế và tạo mô hình thùng rác thông minh.",
            category="Volunteer",
            social_work_days=2.0,
            marker_location=f"SRID=4326;POINT({USER_LNG} {USER_LAT})",
            meeting_location="Khu dân cư Phường Phú Bình, TP. Long Khánh",
            start_time=p4_start,
            end_time=p4_end,
            max_participants=40,
            current_participants=38,
            privacy=ActivityPrivacy.public,
            attendance_mode="manual",
            created_at=now - timedelta(days=18),
        )
        trophy_4 = Trophy(
            id=uuid.uuid4(),
            name="Đại Sứ Môi Trường Xanh Bách Khoa 2026",
            description="Vinh danh cá nhân có đóng góp tích cực và lan tỏa mạnh mẽ lối sống xanh, bảo vệ môi trường đô thị bền vững.",
            activity_id=past_act_4_id,
            created_at=now - timedelta(days=18),
        )
        db.add(past_act_4)
        db.add(trophy_4)

        await db.flush()

        # Gán 4 danh hiệu và ghi nhận điểm danh (attendance_confirmed=True) cho dat_nguyenthese80!
        print("🎖️ 8. Gán 4 Danh hiệu và 8.0 Ngày CTXH cho Nguyễn Đức Đạt...")
        past_joins = [
            JoinRequest(
                id=uuid.uuid4(),
                activity_id=past_act_1_id,
                user_id=dat_user.id,
                status=RequestStatus.approved,
                attendance_confirmed=True,
                created_at=now - timedelta(days=46)
            ),
            JoinRequest(
                id=uuid.uuid4(),
                activity_id=past_act_2_id,
                user_id=dat_user.id,
                status=RequestStatus.approved,
                attendance_confirmed=True,
                created_at=now - timedelta(days=29)
            ),
            JoinRequest(
                id=uuid.uuid4(),
                activity_id=past_act_3_id,
                user_id=dat_user.id,
                status=RequestStatus.approved,
                attendance_confirmed=True,
                created_at=now - timedelta(days=21)
            ),
            JoinRequest(
                id=uuid.uuid4(),
                activity_id=past_act_4_id,
                user_id=dat_user.id,
                status=RequestStatus.approved,
                attendance_confirmed=True,
                created_at=now - timedelta(days=15)
            ),
        ]
        db.add_all(past_joins)

        user_trophies = [
            UserTrophy(id=uuid.uuid4(), user_id=dat_user.id, trophy_id=trophy_1.id, activity_id=past_act_1_id, created_at=now - timedelta(days=40)),
            UserTrophy(id=uuid.uuid4(), user_id=dat_user.id, trophy_id=trophy_2.id, activity_id=past_act_2_id, created_at=now - timedelta(days=28)),
            UserTrophy(id=uuid.uuid4(), user_id=dat_user.id, trophy_id=trophy_3.id, activity_id=past_act_3_id, created_at=now - timedelta(days=20)),
            UserTrophy(id=uuid.uuid4(), user_id=dat_user.id, trophy_id=trophy_4.id, activity_id=past_act_4_id, created_at=now - timedelta(days=14)),
        ]
        db.add_all(user_trophies)

        await db.commit()
        print("✅ Đã commit toàn bộ hoạt động, CLB và danh hiệu vào CSDL!")

        # 9. Sinh Vector Embeddings cho các hoạt động để AI Chatbot hoạt động hoàn hảo
        print("🧠 9. Đang tạo Vector Embeddings cho các hoạt động bằng Gemini...")
        all_acts_res = await db.execute(select(Activity))
        all_acts = all_acts_res.unique().scalars().all()
        for act in all_acts:
            embed_text = f"{act.title}. {act.description or ''} Thể loại: {act.category}. Địa điểm: {act.meeting_location or ''}. CTXH: {act.social_work_days or 0} ngày."
            try:
                emb = generate_embedding(embed_text)
                if emb:
                    act.embedding = emb
            except Exception as e:
                print(f"   ⚠️ Lỗi embed cho {act.title}: {e}")
        await db.commit()
        print("🎉 HOÀN TẤT SEED TOÀN BỘ HOẠT ĐỘNG, CLB, DANH HIỆU VÀ EMBEDDINGS THÀNH CÔNG RỰC RỠ!")

if __name__ == "__main__":
    asyncio.run(seed_data())
