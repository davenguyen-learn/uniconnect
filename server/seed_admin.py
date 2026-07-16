"""Seed script to create an admin user. Run: python seed_admin.py"""

import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.modules.users.models import User, UserRole


ADMIN_EMAIL = "admin@uniconnect.vn"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
ADMIN_FULL_NAME = "System Admin"


async def seed_admin():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as db:
        # Check if admin already exists
        result = await db.execute(select(User).where(User.email == ADMIN_EMAIL))
        existing = result.scalar_one_or_none()

        if existing:
            if existing.role != UserRole.admin:
                existing.role = UserRole.admin
                await db.commit()
                print(f"✅ Updated existing user '{ADMIN_USERNAME}' to admin role.")
            else:
                print(f"ℹ️  Admin user '{ADMIN_USERNAME}' already exists.")
            return

        admin = User(
            email=ADMIN_EMAIL,
            username=ADMIN_USERNAME,
            full_name=ADMIN_FULL_NAME,
            password_hash=hash_password(ADMIN_PASSWORD),
            role=UserRole.admin,
        )
        db.add(admin)
        await db.commit()
        print(f"✅ Created admin user: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_admin())
