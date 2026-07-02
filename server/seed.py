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
            ("HUST CS K65", "Group for K65 Computer Science students", users[0].id),
            ("English Speaking Club", "Practice English together", users[1].id),
            ("AI Research", "Discuss latest AI papers", users[2].id),
        ]
        
        groups = []
        for name, desc, owner_id in groups_data:
            group = Group(name=name, description=desc, owner_id=owner_id)
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
        activities_data = [
            ("Learn React", "Study group for ReactJS", "Study", 21.0278, 105.8342, users[0].id, groups[0].id),
            ("Badminton Weekly", "Play badminton at Bach Khoa stadium", "Sports", 21.0051, 105.8456, users[1].id, None),
            ("Read Attention Is All You Need", "Paper reading session", "Study", 21.0278, 105.8342, users[2].id, groups[2].id),
            ("Coffee Talk", "Casual chat at The Coffee House", "Social", 21.0123, 105.8234, users[3].id, None),
        ]
        
        activities = []
        for title, desc, cat, lat, lng, host_id, group_id in activities_data:
            start_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=random.randint(1, 5))
            act = Activity(
                title=title,
                description=desc,
                category=cat,
                location=f"POINT({lng} {lat})",
                location_name="Hanoi",
                start_time=start_time,
                end_time=start_time + datetime.timedelta(hours=2),
                host_id=host_id,
                group_id=group_id,
                max_participants=10,
                current_participants=1
            )
            db.add(act)
            activities.append(act)
            
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
                    p = JoinRequest(activity_id=act.id, user_id=user.id, status=RequestStatus.approved)
                    db.add(p)
        
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
