"""
Seed regular past activities for realistic user history.
No trophies, no CTXH, just regular student life activities:
- Sports (football, badminton)
- Study (exam prep, group study, CAD/CAM workshop)
- Social (coffee talk, club general meeting)
"""

import asyncio
import uuid
import datetime
from datetime import timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

from app.core.config import settings
from app.modules.users.models import User
from app.modules.activities.models import Activity, ActivityPrivacy
from app.modules.participation.models import JoinRequest, RequestStatus
from app.modules.groups.models import Group
from app.modules.chat.embeddings import generate_embedding

USER_LAT = 10.929718
USER_LNG = 107.250381

async def add_regular_past_activities():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.datetime.now(timezone.utc)
    u_id = uuid.UUID('1be9762d-d9bf-4fa4-b928-1aadd647a4ce')  # dat_nguyenthese80
    
    async with session() as db:
        groups = (await db.execute(select(Group))).unique().scalars().all()
        g_map = {g.name: g for g in groups}
        
        all_students = (await db.execute(select(User).where(User.role == 'student'))).scalars().all()
        other_users = [s for s in all_students if s.id != u_id]
        
        # 6 regular past activities without trophies or CTXH
        past_regular = [
            {
                'title': 'Giao lưu Bóng đá Mini 5v5 K22 Cơ Khí vs K22 Điện - Điện Tử',
                'description': 'Trận bóng đá giao hữu giữa hai chi đoàn K22 Cơ Khí và K22 Điện nhằm thắt chặt tinh thần hữu nghị và rèn luyện thể lực.',
                'category': 'Sports',
                'grp': g_map.get('CLB Thể Thao & Cầu Lông Sinh Viên BK'),
                'days_ago': 22,
                'hours_len': 2,
                'location': 'Sân bóng mini Cỏ Xanh Long Khánh',
                'participants': 16,
            },
            {
                'title': 'Buổi Học Nhóm & Giải Bài Tập Lớn Chi Tiết Máy K22',
                'description': 'Ôn tập tính toán trục, ổ lăn và bộ truyền bánh răng nón cho môn Chi Tiết Máy cùng các bạn K22 Cơ Khí.',
                'category': 'Study',
                'grp': g_map.get('CLB Robot & Sáng Tạo Cơ Khí BK'),
                'days_ago': 26,
                'hours_len': 3,
                'location': 'Phòng tự học Thư viện Long Khánh',
                'participants': 12,
            },
            {
                'title': 'Coffee Talk: Chia sẻ Kinh Nghiệm Tìm Kiếm Cơ Hội Thực Tập Sớm',
                'description': 'Giao lưu thân mật cùng các anh chị cựu sinh viên đi trước, chia sẻ kinh nghiệm chuẩn bị CV, phỏng vấn và thích nghi môi trường doanh nghiệp.',
                'category': 'Social',
                'grp': g_map.get('CLB Tin Học - BK IT Club'),
                'days_ago': 17,
                'hours_len': 2.5,
                'location': 'The Coffee House Long Khánh',
                'participants': 22,
            },
            {
                'title': 'Buổi Sinh Hoạt Định Kỳ & Gặp Gỡ Tân Thành Viên CLB Gia Sư 09/2026',
                'description': 'Họp mặt toàn thể thành viên CLB Gia Sư Bách Khoa đầu năm học mới, triển khai kế hoạch hoạt động các lớp tình thương và giao lưu gắn kết.',
                'category': 'Social',
                'grp': g_map.get('CLB Gia Sư Bách Khoa - BK Tutor Club'),
                'days_ago': 12,
                'hours_len': 2,
                'location': 'Trung tâm Văn hóa & Triển lãm Long Khánh',
                'participants': 28,
            },
            {
                'title': 'Giao Lưu Cầu Lông Đơn Nam Phong Trào Sinh Viên Cuối Tuần',
                'description': 'Buổi giao lưu đánh cầu lông phong trào rèn luyện sức khỏe, thư giãn cuối tuần sau những giờ học căng thẳng.',
                'category': 'Sports',
                'grp': g_map.get('CLB Thể Thao & Cầu Lông Sinh Viên BK'),
                'days_ago': 9,
                'hours_len': 3,
                'location': 'Sân Cầu Lông Thể Thao Tuổi Trẻ Long Khánh',
                'participants': 14,
            },
            {
                'title': 'Workshop Ứng Dụng CAD/CAM trong Thiết Kế Cơ Khí & In 3D',
                'description': 'Thực hành dựng hình 3D trên SolidWorks, xuất file G-code và vận hành máy in 3D FDM tại phòng lab sáng tạo.',
                'category': 'Study',
                'grp': g_map.get('CLB Robot & Sáng Tạo Cơ Khí BK'),
                'days_ago': 30,
                'hours_len': 4,
                'location': 'Phòng Lab Sáng tạo Cơ khí Long Khánh',
                'participants': 20,
            },
        ]
        
        for item in past_regular:
            act_id = uuid.uuid4()
            start_dt = now - timedelta(days=item['days_ago'], hours=4)
            end_dt = start_dt + timedelta(hours=item['hours_len'])
            created_dt = start_dt - timedelta(days=5)
            grp_id = item['grp'].id if item['grp'] else None
            
            act = Activity(
                id=act_id,
                host_id=u_id,
                group_id=grp_id,
                title=item['title'],
                description=item['description'],
                category=item['category'],
                social_work_days=0.0,  # Normal activity: no CTXH
                marker_location=f'SRID=4326;POINT({USER_LNG} {USER_LAT})',
                meeting_location=item['location'],
                start_time=start_dt,
                end_time=end_dt,
                max_participants=40,
                current_participants=item['participants'],
                privacy=ActivityPrivacy.public,
                attendance_mode='manual',
                created_at=created_dt,
            )
            # Add embedding
            try:
                emb = generate_embedding(f"{item['title']}. {item['description']}")
                if emb:
                    act.embedding = emb
            except Exception:
                pass
                
            db.add(act)
            
            # dat_nguyenthese80 participated and confirmed attendance
            jr_dat = JoinRequest(
                id=uuid.uuid4(),
                activity_id=act_id,
                user_id=u_id,
                status=RequestStatus.approved,
                attendance_confirmed=True,
                created_at=created_dt + timedelta(days=1),
            )
            db.add(jr_dat)
            
            # Add some other participants
            sampled = other_users[:min(len(other_users), item['participants'] - 1)]
            for ou in sampled:
                db.add(JoinRequest(
                    id=uuid.uuid4(),
                    activity_id=act_id,
                    user_id=ou.id,
                    status=RequestStatus.approved,
                    attendance_confirmed=True,
                    created_at=created_dt + timedelta(days=1),
                ))
                
        await db.commit()
        print('✅ Đã thêm thành công 6 hoạt động thông thường trong quá khứ!')

if __name__ == '__main__':
    asyncio.run(add_regular_past_activities())
