"""
Seed Clean Users for Demo.
- Featured Student (Khoa Co khi, DH Bach Khoa TP.HCM, K22 nam 3, que Long Khanh Dong Nai, the thao, phuot, xem phim, etc.)
- Star Friend User (for follow demo)
- ~18 popular, realistic Vietnamese student users with clean usernames (no random numbers)
- Proper created_at (1-2 months ago)
- Initial user_follows relationships
"""

import asyncio
import datetime
from datetime import timezone, timedelta
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text, select

from app.core.config import settings
from app.core.security import hash_password
from app.modules.users.models import User, UserRole, UserFollow

async def seed_users():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    # Current time reference: 2026-09-26
    now = datetime.datetime.now(timezone.utc)
    # 45 days ago ~ early August 2026 (1.5 months ago)
    joined_date_featured = now - timedelta(days=47, hours=4, minutes=15)
    
    std_password_hash = hash_password("password123")
    
    async with async_session() as db:
        print("🧹 Dọn dẹp các user dummy cũ (giữ lại các tài khoản quản trị và tài khoản chính nếu có)...")
        # Xóa user_follows cũ
        await db.execute(text("TRUNCATE TABLE user_follows CASCADE"))
        
        # Xóa các user dummy có dấu gạch dưới kèm số như phuc_61, tuan_62
        await db.execute(text("""
            DELETE FROM users 
            WHERE username ~ '^[a-z]+_[0-9]+$'
        """))
        await db.commit()
        
        # 1. User demo chính: Nguyễn Đức Đạt (dat_nguyenthese80 & dat_nguyen)
        # Kiểm tra xem dat_nguyenthese80 đã có chưa, nếu có thì UPDATE, nếu chưa thì INSERT
        res = await db.execute(select(User).where(User.username == "dat_nguyenthese80"))
        dat_user = res.scalar_one_or_none()
        
        featured_bio = (
            "K22 Khoa Cơ Khí - ĐH Bách Khoa TP.HCM ⚙️ | Quê: Long Khánh, Đồng Nai 🌿\n"
            "⚽ Đam mê thể thao (Bóng đá, Cầu lông), thích chạy bộ rèn luyện sức khỏe.\n"
            "🛵 Đam mê đi phượt cuối tuần, thích khám phá các cung đường biển & cắm trại.\n"
            "🎬 Mê xem phim rạp, đặc biệt là phim trinh thám và Sci-Fi.\n"
            "Tích cực tham gia các hoạt động CTXH & Mùa Hè Xanh. Sống nhiệt huyết, không ngừng học hỏi!"
        )
        featured_interests = ["Bóng đá", "Cầu lông", "Đi phượt", "Xem phim", "Kỹ thuật Cơ khí", "Tình nguyện CTXH"]
        featured_avatar = "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?auto=format&fit=crop&w=400&q=80"
        
        if dat_user:
            dat_user.full_name = "Nguyễn Đức Đạt"
            dat_user.university = "Trường Đại học Bách Khoa - ĐHQG TP.HCM"
            dat_user.bio = featured_bio
            dat_user.interests = featured_interests
            dat_user.avatar_url = featured_avatar
            dat_user.created_at = joined_date_featured
            dat_user.is_verified = True
            dat_user.password_hash = std_password_hash
        else:
            dat_user = User(
                id=uuid.uuid4(),
                email="dat.nguyenthese80@gmail.com",
                username="dat_nguyenthese80",
                full_name="Nguyễn Đức Đạt",
                university="Trường Đại học Bách Khoa - ĐHQG TP.HCM",
                bio=featured_bio,
                interests=featured_interests,
                avatar_url=featured_avatar,
                password_hash=std_password_hash,
                role=UserRole.student,
                is_active=True,
                is_verified=True,
                created_at=joined_date_featured,
            )
            db.add(dat_user)
            
        # 2. Star User thứ hai để demo click "Theo dõi / Follow" (Lê Minh Khôi)
        res = await db.execute(select(User).where(User.username == "minh_khoi"))
        khoi_user = res.scalar_one_or_none()
        
        khoi_bio = (
            "K22 Cơ Khí Chế Tạo - ĐH Bách Khoa TP.HCM ⚙️ | Quê: Long Khánh, Đồng Nai 🛵\n"
            "Đam mê robot, cơ điện tử, thích chơi thể thao (bóng đá, bơi lội), xem phim chiếu rạp và phượt bụi cuối tuần 🏕️.\n"
            "Thành viên CLB Chế tạo máy BK & Đội Tình nguyện Xung kích. Rất vui được kết nối!"
        )
        khoi_interests = ["Cơ điện tử", "Bóng đá", "Đi phượt", "Xem phim", "Bơi lội", "Robotics"]
        khoi_avatar = "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=400&q=80"
        khoi_joined = now - timedelta(days=52, hours=6)
        
        if khoi_user:
            khoi_user.full_name = "Lê Minh Khôi"
            khoi_user.university = "Trường Đại học Bách Khoa - ĐHQG TP.HCM"
            khoi_user.bio = khoi_bio
            khoi_user.interests = khoi_interests
            khoi_user.avatar_url = khoi_avatar
            khoi_user.created_at = khoi_joined
            khoi_user.is_verified = True
            khoi_user.password_hash = std_password_hash
        else:
            khoi_user = User(
                id=uuid.uuid4(),
                email="khoi.le@hcmut.edu.vn",
                username="minh_khoi",
                full_name="Lê Minh Khôi",
                university="Trường Đại học Bách Khoa - ĐHQG TP.HCM",
                bio=khoi_bio,
                interests=khoi_interests,
                avatar_url=khoi_avatar,
                password_hash=std_password_hash,
                role=UserRole.student,
                is_active=True,
                is_verified=True,
                created_at=khoi_joined,
            )
            db.add(khoi_user)

        # 3. Các tổ chức & quản trị
        org_users_data = [
            {
                "username": "ctxh_bk",
                "email": "ctxh@hcmut.edu.vn",
                "full_name": "Ban Công tác Xã hội ĐH Bách Khoa",
                "role": UserRole.edu_org,
                "bio": "Kênh thông tin và điều phối các hoạt động Công tác Xã hội chính thức của Trường ĐH Bách Khoa - ĐHQG TP.HCM.",
                "avatar_url": "https://images.unsplash.com/photo-1511632765486-a01980e01a18?auto=format&fit=crop&w=400&q=80",
                "interests": ["Tình nguyện", "CTXH", "Mùa hè xanh", "Hiến máu nhân đạo"],
                "created_at": now - timedelta(days=90)
            },
            {
                "username": "doan_bk",
                "email": "doan@hcmut.edu.vn",
                "full_name": "Đoàn Thanh niên - Hội Sinh viên HCMUT",
                "role": UserRole.edu_org,
                "bio": "Đoàn TNCS Hồ Chí Minh - Hội Sinh viên Việt Nam Trường Đại học Bách Khoa TP.HCM.",
                "avatar_url": "https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=400&q=80",
                "interests": ["Đoàn Hội", "Phong trào sinh viên", "Kỹ năng mềm", "Khởi nghiệp"],
                "created_at": now - timedelta(days=90)
            },
            {
                "username": "admin_bk",
                "email": "admin@hcmut.edu.vn",
                "full_name": "Ban Quản trị UniConnect HCMUT",
                "role": UserRole.admin,
                "bio": "Quản trị viên kỹ thuật hệ thống UniConnect HCMUT.",
                "avatar_url": "https://images.unsplash.com/photo-1505373877841-8d25f7d46678?auto=format&fit=crop&w=400&q=80",
                "interests": ["Hệ thống", "Bảo mật", "Hỗ trợ sinh viên"],
                "created_at": now - timedelta(days=120)
            }
        ]

        for org in org_users_data:
            q = await db.execute(select(User).where(User.username == org["username"]))
            ou = q.scalar_one_or_none()
            if ou:
                ou.full_name = org["full_name"]
                ou.role = org["role"]
                ou.bio = org["bio"]
                ou.avatar_url = org["avatar_url"]
                ou.interests = org["interests"]
                ou.created_at = org["created_at"]
                ou.password_hash = std_password_hash
            else:
                ou = User(
                    id=uuid.uuid4(),
                    email=org["email"],
                    username=org["username"],
                    full_name=org["full_name"],
                    role=org["role"],
                    university="Trường Đại học Bách Khoa - ĐHQG TP.HCM",
                    bio=org["bio"],
                    avatar_url=org["avatar_url"],
                    interests=org["interests"],
                    password_hash=std_password_hash,
                    is_active=True,
                    is_verified=True,
                    created_at=org["created_at"]
                )
                db.add(ou)

        # 4. Danh sách 18 sinh viên Bách Khoa tên hay, phổ biến, thông tin phong phú
        students_data = [
            ("hoang_nam", "nam.tran@hcmut.edu.vn", "Trần Hoàng Nam", "K22 Khoa học Máy tính 💻 | Thích lập trình web, chơi bóng rổ 🏀 và guitar 🎸.", ["Web Dev", "Bóng rổ", "Guitar", "Hackathon"], "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=400&q=80", 42),
            ("khanh_vy", "vy.tran@hcmut.edu.vn", "Trần Khánh Vy", "K22 Quản lý Công nghiệp 📊 | Yêu thích tổ chức sự kiện, MC hội thảo và đọc sách 📚.", ["Tổ chức sự kiện", "MC", "Đọc sách", "Yoga"], "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=400&q=80", 55),
            ("gia_huy", "huy.do@hcmut.edu.vn", "Đỗ Gia Huy", "K22 Kỹ thuật Ô tô 🚗 | Mê xe thể thao, chạy xe đường trường và bóng đá cuối tuần ⚽.", ["Ô tô", "Bóng đá", "Phượt xe", "Công nghệ"], "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?auto=format&fit=crop&w=400&q=80", 48),
            ("phuong_thao", "thao.huynh@hcmut.edu.vn", "Huỳnh Phương Thảo", "K22 Kỹ thuật Môi trường 🌱 | Yêu thiên nhiên, tình nguyện viên chiến dịch Xanh 🌻.", ["Môi trường", "Tình nguyện", "Trồng cây", "Nhiếp ảnh"], "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80", 60),
            ("minh_triet", "triet.le@hcmut.edu.vn", "Lê Minh Triết", "K21 Kỹ thuật Điện - Điện tử ⚡ | Nghiên cứu IoT, mạch nhúng và thích leo núi dã ngoại 🏔️.", ["IoT", "Điện tử", "Leo núi", "Bơi lội"], "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=400&q=80", 50),
            ("linh_dan", "dan.dang@hcmut.edu.vn", "Đặng Linh Đan", "K23 Kỹ thuật Phần mềm 👩‍💻 | Thích UI/UX design, vẽ tranh digital và xem anime 🎨.", ["UI/UX", "Vẽ tranh", "Anime", "Cầu lông"], "https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=400&q=80", 38),
            ("quoc_bao", "bao.dang@hcmut.edu.vn", "Đặng Quốc Bảo", "K22 Kỹ thuật Xây dựng 🏗️ | Mê thiết kế công trình, chạy marathon và chụp ảnh kiến trúc 📷.", ["Xây dựng", "Chạy bộ", "Kiến trúc", "Cầu lông"], "https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?auto=format&fit=crop&w=400&q=80", 45),
            ("thanh_truc", "truc.vu@hcmut.edu.vn", "Vũ Thanh Trúc", "K22 Kỹ thuật Hóa học 🧪 | Thích thí nghiệm, làm bánh 🧁 và tham gia hoạt động văn nghệ trường.", ["Hóa học", "Làm bánh", "Hát", "CTXH"], "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=400&q=80", 52),
            ("tuan_kiet", "kiet.phan@hcmut.edu.vn", "Phan Tuấn Kiệt", "K23 Logistics & Chuỗi cung ứng 📦 | Thích cờ vua ♟️, bóng chuyền 🏐 và nghe podcast kinh tế.", ["Logistics", "Cờ vua", "Bóng chuyền", "Podcast"], "https://images.unsplash.com/photo-1501196354995-cbb51c65aaea?auto=format&fit=crop&w=400&q=80", 35),
            ("quynh_chi", "chi.ngo@hcmut.edu.vn", "Ngô Quỳnh Chi", "K22 Công nghệ Sinh học 🧬 | Thích nghiên cứu vi sinh, cắm hoa 🌸 và đạp xe sáng sớm.", ["Sinh học", "Cắm hoa", "Đạp xe", "Đọc sách"], "https://images.unsplash.com/photo-1488426862026-3ee34a7d66df?auto=format&fit=crop&w=400&q=80", 40),
            ("bao_long", "long.le@hcmut.edu.vn", "Lê Bảo Long", "K22 Kỹ thuật Cơ khí ⚙️ | Chế tạo mô hình RC, thích bóng đá ⚽ và đi phượt bằng xe máy.", ["Cơ khí", "Bóng đá", "Đi phượt", "Mô hình"], "https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?auto=format&fit=crop&w=400&q=80", 44),
            ("anh_thu", "thu.pham@hcmut.edu.vn", "Phạm Anh Thư", "K21 Quản lý Công nghiệp 📈 | Đam mê khởi nghiệp, thích bơi lội 🏊‍♀️ và du lịch khám phá.", ["Khởi nghiệp", "Bơi lội", "Du lịch", "Tiếng Anh"], "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=400&q=80", 58),
            ("hai_dang", "dang.vu@hcmut.edu.vn", "Vũ Hải Đăng", "K21 Khoa học Máy tính 💻 | Nghiên cứu AI / Deep Learning, thích chơi cờ tướng ♟️.", ["AI", "Deep Learning", "Cờ tướng", "Chạy bộ"], "https://images.unsplash.com/photo-1496345875659-11f7dd282d1d?auto=format&fit=crop&w=400&q=80", 56),
            ("yen_nhi", "nhi.hoang@hcmut.edu.vn", "Hoàng Yến Nhi", "K23 Kỹ thuật Máy tính 🖥️ | Thích học ngoại ngữ (IELTS 8.0) 🗣️, đàn piano 🎹 và làm tình nguyện viên.", ["Ngoại ngữ", "Piano", "Tình nguyện", "Coding"], "https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=400&q=80", 32),
            ("quang_khai", "khai.dinh@hcmut.edu.vn", "Đinh Quang Khải", "K23 Kỹ thuật Hệ thống Công nghiệp 🏭 | Thích bóng bàn 🏓, bơi lội và đi phượt cắm trại 🏕️.", ["Bóng bàn", "Bơi lội", "Cắm trại", "Phượt"], "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=400&q=80", 36),
            ("bao_ngoc", "ngoc.huynh@hcmut.edu.vn", "Huỳnh Bảo Ngọc", "K22 Kỹ thuật Y sinh 🩺 | Thích nghiên cứu thiết bị y tế, chụp ảnh đường phố 📸.", ["Y sinh", "Nhiếp ảnh", "Cầu lông", "Đi bộ"], "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=400&q=80", 49),
            ("duc_thinh", "thinh.ngo@hcmut.edu.vn", "Ngô Đức Thịnh", "K22 Cơ điện tử 🤖 | Thành viên đội Robocon BK, thích chế tạo mạch và xem phim hành động 🍿.", ["Robocon", "Cơ điện tử", "Phim ảnh", "Thể thao"], "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=400&q=80", 47),
            ("dieu_linh", "linh.trinh@hcmut.edu.vn", "Trịnh Diệu Linh", "K23 Kỹ thuật Dầu khí ⛽ | Thích khám phá địa chất, leo núi 🧗‍♀️ và hoạt động cộng đồng.", ["Địa chất", "Leo núi", "Tình nguyện", "Yoga"], "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=400&q=80", 34),
        ]

        created_students = []
        for uname, uemail, ufullname, ubio, uinterests, uavatar, days_ago in students_data:
            q = await db.execute(select(User).where(User.username == uname))
            su = q.scalar_one_or_none()
            join_dt = now - timedelta(days=days_ago, hours=3, minutes=12)
            if su:
                su.full_name = ufullname
                su.email = uemail
                su.bio = ubio
                su.interests = uinterests
                su.avatar_url = uavatar
                su.created_at = join_dt
                su.university = "Trường Đại học Bách Khoa - ĐHQG TP.HCM"
                su.password_hash = std_password_hash
                su.is_verified = True
                created_students.append(su)
            else:
                su = User(
                    id=uuid.uuid4(),
                    username=uname,
                    email=uemail,
                    full_name=ufullname,
                    bio=ubio,
                    interests=uinterests,
                    avatar_url=uavatar,
                    university="Trường Đại học Bách Khoa - ĐHQG TP.HCM",
                    password_hash=std_password_hash,
                    role=UserRole.student,
                    is_active=True,
                    is_verified=True,
                    created_at=join_dt,
                )
                db.add(su)
                created_students.append(su)

        await db.commit()
        print("✅ Đã cập nhật và tạo mới xong toàn bộ Users!")

        # 5. Khởi tạo mạng lưới Follows (để số follower/following hiển thị đẹp mắt)
        # Giữ trạng thái: dat_user CHƯA follow khoi_user (hoặc ngược lại) để lúc demo bấm nút Follow ăn ngay!
        print("👥 Khởi tạo mạng lưới Follows cho các tài khoản...")
        
        # Lấy lại đối tượng mới nhất từ DB
        dat_res = await db.execute(select(User).where(User.username == "dat_nguyenthese80"))
        dat_obj = dat_res.scalar_one()
        
        khoi_res = await db.execute(select(User).where(User.username == "minh_khoi"))
        khoi_obj = khoi_res.scalar_one()
        
        all_res = await db.execute(select(User).where(User.role == UserRole.student))
        all_students = all_res.scalars().all()
        
        follows_to_add = []
        
        # Cho 12 bạn học sinh follow Lê Minh Khôi (khoi_obj) -> Để khi quay profile Lê Minh Khôi có 12 followers!
        # Và dat_nguyenthese80 CHƯA follow Lê Minh Khôi -> Khi bấm "Theo dõi", số follower tăng lên 13!
        followers_for_khoi = [s for s in all_students if s.id != khoi_obj.id and s.id != dat_obj.id][:12]
        for f in followers_for_khoi:
            follows_to_add.append(UserFollow(follower_id=f.id, following_id=khoi_obj.id))
            
        # Cho Lê Minh Khôi following lại 6 bạn
        following_for_khoi = [s for s in all_students if s.id != khoi_obj.id and s.id != dat_obj.id][2:8]
        for target in following_for_khoi:
            follows_to_add.append(UserFollow(follower_id=khoi_obj.id, following_id=target.id))
            
        # Cho 10 bạn follow Nguyễn Đức Đạt (dat_obj)
        followers_for_dat = [s for s in all_students if s.id != dat_obj.id and s.id != khoi_obj.id][:10]
        for f in followers_for_dat:
            follows_to_add.append(UserFollow(follower_id=f.id, following_id=dat_obj.id))
            
        # Cho Nguyễn Đức Đạt following 5 bạn
        following_for_dat = [s for s in all_students if s.id != dat_obj.id and s.id != khoi_obj.id][3:8]
        for target in following_for_dat:
            follows_to_add.append(UserFollow(follower_id=dat_obj.id, following_id=target.id))

        db.add_all(follows_to_add)
        await db.commit()
        print(f"✅ Đã thêm {len(follows_to_add)} lượt Follow sinh động!")
        print("🎉 HOÀN THÀNH SEED USER ĐẸP CHO DEMO!")

if __name__ == "__main__":
    asyncio.run(seed_users())
