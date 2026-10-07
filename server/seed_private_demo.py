"""
Seed script for Phase 2: Private / Group-only Activities Demo.
Seeds:
- Groups: 'CLB Môi Trường Xanh', 'Đội CTXH Bách Khoa'
- Users:
  - 'thanh_vien_clb' (thành viên chính thức của CLB)
  - 'sinh_vien_ngoai' (sinh viên ngoài nhóm)
- Activities:
  1. 'Họp Ban Chủ nhiệm & Lên kế hoạch quý 4' (Private - CLB Môi Trường Xanh)
  2. 'Tập huấn kỹ năng nội bộ Đội CTXH' (Private - Đội CTXH Bách Khoa)
"""

import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.config import settings
from app.core.security import hash_password
from app.modules.users.models import User, UserRole
from app.modules.groups.models import Group, GroupMember, GroupRole, GroupPrivacy
from app.modules.activities.models import Activity, ActivityPrivacy


async def seed_private_demo():
    print("[*] BAT DAU SEED DU LIEU DEMO PHASE 2: PRIVATE ACTIVITIES...")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as db:
        # 1. Tạo hoặc lấy users
        # Host user
        host_user = await db.scalar(select(User).where(User.username == "chu_nhiem_clb"))
        if not host_user:
            host_user = User(
                username="chu_nhiem_clb",
                email="chunhiem@hcmut.edu.vn",
                full_name="Nguyễn Văn Chủ Nhiệm",
                password_hash=hash_password("password123"),
                role=UserRole.student,
            )
            db.add(host_user)
            await db.flush()

        # Member user (Tài khoản B - Xem được hoạt động)
        member_user = await db.scalar(select(User).where(User.username == "thanh_vien_clb"))
        if not member_user:
            member_user = User(
                username="thanh_vien_clb",
                email="thanhvien@hcmut.edu.vn",
                full_name="Trần Thành Viên",
                password_hash=hash_password("password123"),
                role=UserRole.student,
            )
            db.add(member_user)
            await db.flush()

        # Outsider user (Tài khoản A - Ngoài CLB, không xem được)
        outsider_user = await db.scalar(select(User).where(User.username == "sinh_vien_ngoai"))
        if not outsider_user:
            outsider_user = User(
                username="sinh_vien_ngoai",
                email="ngoaiclb@hcmut.edu.vn",
                full_name="Lê Sinh Viên Ngoài",
                password_hash=hash_password("password123"),
                role=UserRole.student,
            )
            db.add(outsider_user)
            await db.flush()

        # 2. Tạo hoặc lấy groups
        # Group 1: CLB Môi Trường Xanh
        group1 = await db.scalar(select(Group).where(Group.name == "CLB Môi Trường Xanh"))
        if not group1:
            group1 = Group(
                name="CLB Môi Trường Xanh",
                description="Câu lạc bộ hoạt động vì môi trường xanh Đại học Bách Khoa.",
                public_description="CLB Môi Trường Xanh tổ chức các chiến dịch thu gom rác, tái chế và lan tỏa lối sống xanh.",
                private_description="Tài liệu nội bộ và kế hoạch họp kín Ban Chủ nhiệm.",
                owner_id=host_user.id,
                privacy=GroupPrivacy.public,
            )
            db.add(group1)
            await db.flush()

        # Group 2: Đội CTXH Bách Khoa
        group2 = await db.scalar(select(Group).where(Group.name == "Đội CTXH Bách Khoa"))
        if not group2:
            group2 = Group(
                name="Đội CTXH Bách Khoa",
                description="Đội Công tác Xã hội Đại học Bách Khoa TP.HCM.",
                public_description="Tổ chức các chuyến đi mùa hè xanh, mái ấm tình thương và cứu trợ đồng bào.",
                private_description="Lịch trực văn phòng và giáo án tập huấn kỹ năng nội bộ.",
                owner_id=host_user.id,
                privacy=GroupPrivacy.public,
            )
            db.add(group2)
            await db.flush()

        # 3. Thêm member_user vào cả 2 CLB (host_user là admin, member_user là member)
        for grp in [group1, group2]:
            # Host membership
            host_mem = await db.scalar(
                select(GroupMember).where(GroupMember.group_id == grp.id, GroupMember.user_id == host_user.id)
            )
            if not host_mem:
                db.add(GroupMember(group_id=grp.id, user_id=host_user.id, role=GroupRole.admin))

            # Member membership
            mem = await db.scalar(
                select(GroupMember).where(GroupMember.group_id == grp.id, GroupMember.user_id == member_user.id)
            )
            if not mem:
                db.add(GroupMember(group_id=grp.id, user_id=member_user.id, role=GroupRole.member))

        await db.flush()

        # 4. Tạo 2 hoạt động Private
        now = datetime.now(timezone.utc)
        act1_start = now + timedelta(days=2, hours=3)
        act2_start = now + timedelta(days=3, hours=5)

        # Activity 1: Họp Ban Chủ nhiệm & Lên kế hoạch quý 4
        act1 = await db.scalar(select(Activity).where(Activity.title == "Họp Ban Chủ nhiệm & Lên kế hoạch quý 4"))
        if not act1:
            act1 = Activity(
                title="Họp Ban Chủ nhiệm & Lên kế hoạch quý 4",
                description="Buổi họp nội bộ nhằm tổng kết các chiến dịch môi trường vừa qua và phân công nhiệm vụ chiến dịch quý 4.",
                private_description="Link Google Meet họp kín: meet.google.com/abc-demo-xyz. Chỉ dành riêng cho BCN.",
                category="Social",
                location=f"POINT({106.802148} {10.882779})",
                location_name="Phòng họp Văn phòng Đoàn - Hội A4",
                start_time=act1_start,
                end_time=act1_start + timedelta(hours=2),
                host_id=host_user.id,
                group_id=group1.id,
                max_participants=25,
                current_participants=2,
                privacy=ActivityPrivacy.private,
            )
            db.add(act1)

        # Activity 2: Tập huấn kỹ năng nội bộ Đội CTXH
        act2 = await db.scalar(select(Activity).where(Activity.title == "Tập huấn kỹ năng nội bộ Đội CTXH"))
        if not act2:
            act2 = Activity(
                title="Tập huấn kỹ năng nội bộ Đội CTXH",
                description="Buổi rèn luyện kỹ năng sinh hoạt vòng tròn, sơ cấp cứu dã ngoại và kỹ năng hoạt náo đội hình.",
                private_description="Tài liệu bài hát sinh hoạt và phân công dụng cụ dã ngoại.",
                category="Volunteer",
                location=f"POINT({106.805148} {10.880779})",
                location_name="Khuôn viên Sân Cờ Cơ sở Dĩ An",
                start_time=act2_start,
                end_time=act2_start + timedelta(hours=3),
                host_id=host_user.id,
                group_id=group2.id,
                max_participants=40,
                current_participants=2,
                privacy=ActivityPrivacy.private,
            )
            db.add(act2)

        await db.commit()
        print("✅ ĐÃ SEED THÀNH CÔNG 2 HOẠT ĐỘNG RIÊNG TƯ (PRIVATE ACTIVITIES):")
        print("   1. [🔒 Private] Họp Ban Chủ nhiệm & Lên kế hoạch quý 4 (CLB Môi Trường Xanh)")
        print("   2. [🔒 Private] Tập huấn kỹ năng nội bộ Đội CTXH (Đội CTXH Bách Khoa)")
        print("   👤 Tài khoản B (thành viên CLB): thanh_vien_clb / password123")
        print("   👤 Tài khoản A (ngoài CLB): sinh_vien_ngoai / password123")


if __name__ == "__main__":
    asyncio.run(seed_private_demo())
