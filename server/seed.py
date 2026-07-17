import asyncio
import uuid
import datetime
import random
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.modules.users.models import User, UserRole
from app.modules.groups.models import Group, GroupMember, GroupRole
from app.modules.activities.models import Activity
from app.modules.participation.models import JoinRequest, RequestStatus
from app.modules.documents.models import Document

async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as db:
        print("Clearing existing data...")
        from sqlalchemy import text
        await db.execute(text("TRUNCATE TABLE join_requests, activities, documents, group_members, groups, user_follows, users CASCADE"))
        await db.commit()

        print("Creating users...")
        users_data = [
            ("alice", "alice@example.com", "Alice Nguyen"),
            ("bob", "bob@example.com", "Bob Tran"),
            ("charlie", "charlie@example.com", "Charlie Le"),
            ("diana", "diana@example.com", "Diana Pham"),
        ]
        
        users = []
        for username, email, full_name in users_data:
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                password_hash=hash_password("password123"),
                role=UserRole.student
            )
            db.add(user)
            users.append(user)
            
        await db.commit()
        for u in users:
            await db.refresh(u)
            
        print("Creating groups...")
        groups_data = [
            ("HUST CS K65", "Group for K65 Computer Science students", "Welcome to K65 CS! Here we discuss everything related to our major.", "Join our Zalo group at zalo.me/g/hustcsk65 for daily updates.", users[0].id),
            ("English Speaking Club", "Practice English together", "Welcome to ESC. We meet every Sunday.", "Zoom link for Sunday meetings: bit.ly/esc-zoom.", users[1].id),
            ("AI Research", "Discuss latest AI papers", "Open community for AI enthusiasts.", "Drive link to our paper repo: bit.ly/ai-papers.", users[2].id),
        ]
        
        groups = []
        for name, desc, pub_desc, priv_desc, owner_id in groups_data:
            group = Group(
                name=name, 
                description=desc, 
                public_description=pub_desc,
                private_description=priv_desc,
                owner_id=owner_id
            )
            db.add(group)
            groups.append(group)
            
        await db.commit()
        for g in groups:
            await db.refresh(g)
            
        print("Adding group members...")
        for group in groups:
            # Owner is always admin
            member = GroupMember(group_id=group.id, user_id=group.owner_id, role=GroupRole.admin)
            db.add(member)
            # Add some random members
            for user in users:
                if user.id != group.owner_id and random.choice([True, False]):
                    member = GroupMember(group_id=group.id, user_id=user.id, role=GroupRole.member)
                    db.add(member)
                    
        await db.commit()
        
        print("Creating activities...")
        from app.modules.forms.models import CustomForm, FormField
        
        act1_start = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2)
        act1 = Activity(
            title="Spring Volunteer Campaign - HCMUT 2026",
            description="""🌟 CHIẾN DỊCH XUÂN TÌNH NGUYỆN HCMUT 2026 🌟

Thời gian tập trung: 5h30 sáng
Địa điểm tập trung: Sân nhà A4, Cơ sở Dĩ An
Vật dụng cần mang: 
- Áo chiến dịch (hoặc áo Đoàn)
- Bình nước cá nhân
- Giày thể thao
- Nón tai bèo

Lịch trình dự kiến:
- 5h30 - 6h00: Tập trung, điểm danh và chia đội
- 6h00 - 7h00: Di chuyển đến địa bàn hoạt động
- 7h00 - 11h30: Dọn dẹp vệ sinh khu phố, sơn sửa trường mầm non
- 11h30 - 13h30: Ăn trưa, nghỉ ngơi
- 13h30 - 16h00: Thăm hỏi Mẹ Việt Nam Anh Hùng
- 16h00: Tổng kết và di chuyển về trường

Liên hệ: Trưởng ban tổ chức - Đặng Hà Thành (0912345678)
""",
            category="Social",
            location=f"POINT({106.802148} {10.882779})",
            location_name="KTX ĐHQG HCM",
            start_time=act1_start,
            end_time=act1_start + datetime.timedelta(hours=10),
            host_id=users[0].id,
            group_id=groups[0].id,
            max_participants=50,
            current_participants=1,
            custom_form=CustomForm(
                title="Đăng ký tham gia Xuân Tình Nguyện",
                description="Vui lòng điền thông tin để BTC sắp xếp công việc phù hợp.",
                fields=[
                    FormField(label="Họ và tên", field_type="text", is_required=True, order=0),
                    FormField(label="MSSV", field_type="text", is_required=True, order=1),
                    FormField(label="Có kinh nghiệm tình nguyện chưa?", field_type="boolean", is_required=False, order=2),
                ]
            )
        )
        db.add(act1)
        
        act2_start = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
        act2 = Activity(
            title="Giải chạy bộ sinh viên - 5K Challenge",
            description="""Thử thách chạy bộ 5K quanh khuôn viên Làng Đại học dành cho toàn thể sinh viên.
Đích đến là Hồ Đá. Không yêu cầu kinh nghiệm, chỉ cần tinh thần thể thao!
Nhớ mang theo nước uống và khởi động kỹ trước khi tham gia.

Mỗi người hoàn thành sẽ nhận được huy chương điện tử!
""",
            category="Sports",
            location=f"POINT({106.805} {10.880})",
            location_name="Hồ Đá, Làng Đại học",
            start_time=act2_start,
            end_time=act2_start + datetime.timedelta(hours=3),
            host_id=users[1].id,
            max_participants=100,
            current_participants=1,
            custom_form=CustomForm(
                title="Đăng ký giải chạy",
                fields=[
                    FormField(label="Size áo (S/M/L/XL)", field_type="text", is_required=True, order=0),
                    FormField(label="Cam kết sức khỏe tốt", field_type="boolean", is_required=True, order=1)
                ]
            )
        )
        db.add(act2)
        
        act3_start = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3)
        act3 = Activity(
            title="Read Attention Is All You Need",
            description="Paper reading session discussing the Transformer architecture. Read the paper in advance!",
            category="Study",
            location=f"POINT({105.8342} {21.0278})",
            location_name="Hanoi",
            start_time=act3_start,
            end_time=act3_start + datetime.timedelta(hours=2),
            host_id=users[2].id,
            group_id=groups[2].id,
            max_participants=10,
            current_participants=1
        )
        db.add(act3)
        
        activities = [act1, act2, act3]
        
        # Generate embeddings if available
        try:
            from app.modules.chat.embeddings import generate_embedding
            for act in activities:
                emb = await generate_embedding(f"{act.title}\n{act.description or ''}")
                act.embedding = emb
        except Exception as e:
            print(f"Could not generate embeddings: {e}")
            
        await db.commit()
        
        print("Creating trophies...")
        from app.modules.trophies.models import Trophy
        t1 = Trophy(name="Chiến binh Mùa Hè Xanh", description="Hoàn thành xuất sắc chiến dịch tình nguyện Mùa Hè Xanh.", icon="🌟")
        t2 = Trophy(name="Vận động viên 5K", description="Hoàn thành giải chạy bộ 5K.", icon="🏃‍♂️")
        db.add_all([t1, t2])
        await db.commit()
            
        await db.commit()
        for a in activities:
            await db.refresh(a)
            
        print("Adding activity participants...")
        for act in activities:
            # Host is approved
            p = JoinRequest(activity_id=act.id, user_id=act.host_id, status=RequestStatus.approved)
            db.add(p)
            for user in users:
                if user.id != act.host_id and random.choice([True, False]):
                    form_res = {}
                    if act.custom_form:
                        for field in act.custom_form.fields:
                            if field.field_type == 'boolean':
                                form_res[str(field.id) if field.id else field.label] = True
                            else:
                                form_res[str(field.id) if field.id else field.label] = "Sample response"
                    p = JoinRequest(
                        activity_id=act.id, 
                        user_id=user.id, 
                        status=RequestStatus.approved,
                        form_responses=form_res if form_res else None
                    )
                    db.add(p)
        
        await db.commit()
        
        print("Adding user trophies...")
        from app.modules.trophies.models import UserTrophy
        ut1 = UserTrophy(user_id=users[0].id, trophy_id=t1.id)
        ut2 = UserTrophy(user_id=users[1].id, trophy_id=t2.id)
        db.add_all([ut1, ut2])
        await db.commit()
        
        print("Creating documents...")
        docs_data = [
            ("React Cheat Sheet", "Very useful", "react_cheat_sheet.pdf", "application/pdf", 10240, users[0].id, groups[0].id),
            ("AI Syllabus", "Course syllabus for this semester", "syllabus.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 20480, users[2].id, groups[2].id),
            ("Public Event Poster", "Poster for our upcoming event", "poster.jpg", "image/jpeg", 512000, users[3].id, None),
        ]
        
        for title, desc, fname, ftype, fsize, auth_id, group_id in docs_data:
            doc = Document(
                title=title,
                description=desc,
                file_name=fname,
                file_type=ftype,
                file_size=fsize,
                file_url=f"https://example.com/seed/{fname}",
                author_id=auth_id,
                group_id=group_id
            )
            db.add(doc)
            
        await db.commit()
        
        print("Seeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(seed())
