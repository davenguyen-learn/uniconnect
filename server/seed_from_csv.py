"""
Seed from CSV — Nạp dữ liệu cực nhanh từ các file CSV đã tạo sẵn vào PostgreSQL.
Không cần gọi Gemini API, hoàn thành trong 2-3 giây.

Chạy:
  python seed_from_csv.py [--users 50] [--groups 20] [--activities 40] [--docs 25] [--no-embed]
"""

import argparse
import asyncio
import csv
import datetime
import json
import os
import random
import sys
import uuid

# Fix Vietnamese print on Windows terminal
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.modules.users.models import User, UserRole, UserFollow
from app.modules.activities.models import Activity, ActivityPrivacy
from app.modules.groups.models import Group, GroupMember, GroupRole, GroupPrivacy, GroupJoinRequest
from app.modules.participation.models import JoinRequest, RequestStatus
from app.modules.documents.models import Document
from app.modules.chat.embeddings import generate_embedding

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed_data")


def load_csv(file_name: str) -> list[dict]:
    path = os.path.join(DATA_DIR, file_name)
    if not os.path.exists(path):
        print(f"❌ Không tìm thấy file {path}. Hãy chạy seed_data_generator.py trước!")
        return []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


async def seed(
    num_users: int = 50,
    num_groups: int = 25,
    num_activities: int = 50,
    num_docs: int = 30,
    enable_embeddings: bool = True,
):
    print("=" * 60)
    print("⚡ BẮT ĐẦU SEED NHANH TỪ CSV VÀO POSTGRESQL")
    print("=" * 60)

    # 1. Đọc dữ liệu từ file
    users_raw = load_csv("users.csv")
    groups_raw = load_csv("groups.csv")
    activities_raw = load_csv("activities.csv")
    docs_raw = load_csv("documents.csv")

    if not users_raw or not groups_raw or not activities_raw:
        print("❌ Thiếu dữ liệu CSV trong seed_data/. Vui lòng chạy seed_data_generator.py!")
        return

    # Random sample theo số lượng yêu cầu
    selected_users = random.sample(users_raw, min(num_users, len(users_raw)))
    selected_groups = random.sample(groups_raw, min(num_groups, len(groups_raw)))
    selected_activities = random.sample(activities_raw, min(num_activities, len(activities_raw)))
    selected_docs = random.sample(docs_raw, min(num_docs, len(docs_raw))) if docs_raw else []

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as db:
        # BƯỚC 0: Truncate sạch sẽ
        print("🗑️  Dọn dẹp database cũ...")
        await db.execute(text(
            "TRUNCATE TABLE join_requests, documents, group_join_requests, "
            "group_members, activities, groups, user_follows, users CASCADE"
        ))
        await db.commit()

        # BƯỚC 1: Tạo Users
        print(f"👤 Tạo {len(selected_users)} Users...")
        users_db = []
        hashed_password = hash_password("password123")
        used_usernames = set()
        used_emails = set()

        for idx, u in enumerate(selected_users):
            uname = u["username"]
            if uname in used_usernames:
                uname = f"{uname}_{idx}"
            used_usernames.add(uname)

            uemail = u["email"]
            if uemail in used_emails:
                uemail = f"user_{idx}_{uemail}"
            used_emails.add(uemail)

            try:
                interests = json.loads(u.get("interests", "[]"))
            except Exception:
                interests = ["Cầu lông", "Lập trình", "Cà phê"]

            user = User(
                username=uname,
                email=uemail,
                full_name=u["full_name"],
                bio=u.get("bio", ""),
                interests=interests,
                university=u.get("university", "Đại học Công nghệ Đồng Nai"),
                password_hash=hashed_password,
                role=UserRole.student,
                is_active=True,
                is_verified=random.choice([True, True, True, False]),
            )
            db.add(user)
            users_db.append(user)

        await db.commit()
        for u in users_db:
            await db.refresh(u)

        # BƯỚC 2: User Follows
        print("🔗 Tạo User Follows...")
        follow_pairs = set()
        for u in users_db:
            k = random.randint(3, min(10, len(users_db) - 1))
            targets = random.sample([o for o in users_db if o.id != u.id], k)
            for t in targets:
                pair = (u.id, t.id)
                if pair not in follow_pairs:
                    follow_pairs.add(pair)
                    db.add(UserFollow(follower_id=u.id, following_id=t.id))
        await db.commit()

        # BƯỚC 3: Groups & Members
        print(f"👥 Tạo {len(selected_groups)} Groups & Memberships...")
        groups_db = []
        used_group_names = set()

        for idx, g in enumerate(selected_groups):
            gname = g["name"]
            if gname in used_group_names:
                gname = f"{gname} #{idx+1}"
            used_group_names.add(gname)

            owner = random.choice(users_db)
            privacy = GroupPrivacy.private if g.get("privacy") == "private" else GroupPrivacy.public
            group = Group(
                name=gname,
                description=g.get("description", ""),
                public_description=g.get("public_description", ""),
                private_description=g.get("private_description", ""),
                privacy=privacy,
                require_approval=str(g.get("require_approval")).lower() == "true",
                allow_member_activities=str(g.get("allow_member_activities")).lower() != "false",
                allow_member_documents=str(g.get("allow_member_documents")).lower() != "false",
                owner_id=owner.id,
            )
            db.add(group)
            groups_db.append(group)

        await db.commit()
        for g in groups_db:
            await db.refresh(g)

        for g in groups_db:
            # Owner là admin
            db.add(GroupMember(group_id=g.id, user_id=g.owner_id, role=GroupRole.admin))
            num_m = random.randint(5, min(20, len(users_db) - 1))
            candidates = [u for u in users_db if u.id != g.owner_id]
            members = random.sample(candidates, min(num_m, len(candidates)))
            for m in members:
                role = GroupRole.admin if random.random() < 0.1 else GroupRole.member
                db.add(GroupMember(group_id=g.id, user_id=m.id, role=role))

            if g.require_approval:
                # Add pending requests
                candidates_req = random.sample(users_db, min(3, len(users_db)))
                for u in candidates_req:
                    if u.id != g.owner_id:
                        db.add(GroupJoinRequest(group_id=g.id, user_id=u.id, status="pending"))

        await db.commit()

        # BƯỚC 4: Activities
        print(f"📅 Tạo {len(selected_activities)} Activities...")
        activities_db = []
        now = datetime.datetime.now(datetime.timezone.utc)

        for a in selected_activities:
            days_from_now = int(a.get("days_from_now", random.randint(-5, 20)))
            hours_dur = max(1, int(a.get("hours_duration", 2)))
            act_start = now + datetime.timedelta(days=days_from_now)
            act_start = act_start.replace(
                hour=random.choice([7, 8, 9, 14, 15, 16, 17, 18, 19]),
                minute=random.choice([0, 15, 30, 45]),
                second=0, microsecond=0,
            )
            act_end = act_start + datetime.timedelta(hours=hours_dur)

            lat = float(a.get("latitude", 10.9333))
            lng = float(a.get("longitude", 107.2406))
            # Clamp trong Long Khánh
            lat = max(10.92, min(10.96, lat))
            lng = max(107.22, min(107.26, lng))

            group_id = random.choice(groups_db).id if (groups_db and random.random() > 0.4) else None
            privacy = ActivityPrivacy.private if a.get("privacy") == "private" else ActivityPrivacy.public
            max_p = max(2, int(a.get("max_participants", 10)))
            sw_days = float(a.get("social_work_days", 0))

            act = Activity(
                title=a["title"],
                description=a.get("description", ""),
                private_description=a.get("private_description", ""),
                category=a.get("category", "Social"),
                location=f"POINT({lng} {lat})",
                location_name=a.get("location_name", "TP. Long Khánh"),
                start_time=act_start,
                end_time=act_end,
                host_id=random.choice(users_db).id,
                group_id=group_id,
                max_participants=max_p,
                current_participants=1,
                privacy=privacy,
                require_approval=str(a.get("require_approval")).lower() == "true",
                social_work_days=sw_days if sw_days > 0 else None,
            )
            db.add(act)
            activities_db.append(act)

        await db.commit()
        for act in activities_db:
            await db.refresh(act)

        # BƯỚC 4b: Join Requests & Sync
        print("🎟️  Tạo JoinRequests & đồng bộ số người tham gia...")
        for act in activities_db:
            # Host always approved
            db.add(JoinRequest(
                activity_id=act.id,
                user_id=act.host_id,
                status=RequestStatus.approved,
                attendance_confirmed=(act.start_time < now),
            ))

            max_extra = min(act.max_participants - 1, len(users_db) - 1, 15)
            if max_extra > 0:
                num_approved = random.randint(1, max_extra)
                candidates = [u for u in users_db if u.id != act.host_id]
                random.shuffle(candidates)

                for idx in range(min(num_approved, len(candidates))):
                    user = candidates[idx]
                    db.add(JoinRequest(
                        activity_id=act.id,
                        user_id=user.id,
                        status=RequestStatus.approved,
                        responded_at=act.start_time - datetime.timedelta(hours=random.randint(1, 48)),
                        attendance_confirmed=(act.start_time < now and random.random() > 0.2),
                    ))
                act.current_participants = 1 + min(num_approved, len(candidates))

                if act.start_time > now:
                    for idx in range(num_approved, min(num_approved + 2, len(candidates))):
                        user = candidates[idx]
                        db.add(JoinRequest(
                            activity_id=act.id,
                            user_id=user.id,
                            status=RequestStatus.pending,
                            message=random.choice(["Cho mình tham gia với nhé!", "Xin chào, mình xin 1 slot ạ!", None]),
                        ))

        await db.commit()

        # BƯỚC 4c: Embeddings
        if enable_embeddings and settings.GEMINI_API_KEY:
            print("🧠 Đang tạo Embeddings cho activities...")
            for act in activities_db:
                try:
                    text_to_embed = f"{act.title}\n{act.description}"
                    emb = generate_embedding(text_to_embed)
                    if emb:
                        act.embedding = emb
                except Exception:
                    pass
            await db.commit()

        # BƯỚC 5: Documents
        if selected_docs:
            print(f"📄 Tạo {len(selected_docs)} Documents...")
            for d in selected_docs:
                file_name = d["file_name"].replace(" ", "_")
                file_size = int(d.get("file_size_kb", 1024)) * 1024
                group_id = random.choice(groups_db).id if (groups_db and random.random() > 0.3) else None
                base_url = settings.R2_PUBLIC_URL or "https://storage.uniconnect.vn"
                if not base_url.startswith("http"):
                    base_url = f"https://{base_url}"

                doc = Document(
                    title=d["title"],
                    description=d.get("description", ""),
                    file_name=file_name,
                    file_type=d.get("file_type", "application/pdf"),
                    file_size=file_size,
                    file_url=f"{base_url}/documents/{file_name}",
                    author_id=random.choice(users_db).id,
                    group_id=group_id,
                )
                db.add(doc)
            await db.commit()

    print("\n" + "=" * 60)
    print(f"🎉 SEED THÀNH CÔNG TỪ CSV TRONG VÀI GIÂY!")
    print("=" * 60)
    print(f"   👤 Users:        {len(users_db)}")
    print(f"   👥 Groups:       {len(groups_db)}")
    print(f"   📅 Activities:   {len(activities_db)}")
    print(f"   🔑 Mật khẩu:     password123")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed nhanh từ file CSV")
    parser.add_argument("--users", type=int, default=50, help="Số users cần seed (mặc định 50)")
    parser.add_argument("--groups", type=int, default=25, help="Số groups cần seed (mặc định 25)")
    parser.add_argument("--activities", type=int, default=50, help="Số activities cần seed (mặc định 50)")
    parser.add_argument("--docs", type=int, default=30, help="Số documents cần seed (mặc định 30)")
    parser.add_argument("--no-embed", action="store_true", help="Bỏ qua tạo embeddings để nhanh hơn nữa")

    args = parser.parse_args()
    asyncio.run(seed(
        num_users=args.users,
        num_groups=args.groups,
        num_activities=args.activities,
        num_docs=args.docs,
        enable_embeddings=not args.no_embed,
    ))
