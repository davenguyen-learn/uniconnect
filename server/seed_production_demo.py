"""Standalone CLI script to seed production demo data.
Run:
  python server/seed_production_demo.py
Or with custom DATABASE_URL:
  $env:DATABASE_URL="postgresql+asyncpg://..."
  python server/seed_production_demo.py
"""

import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings
from app.modules.admin.seed_service import seed_demo_database


async def run():
    print(f"[INFO] Connecting to database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'localhost'}...")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as db:
        print("[INFO] Starting demo data seeding...")
        result = await seed_demo_database(db)
        print("\n" + "=" * 60)
        print("SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Users seeded:      {result['seeded_users']}")
        print(f"Groups seeded:     {result['seeded_groups']}")
        print(f"Activities seeded: {result['seeded_activities']}")
        print(f"Trophies seeded:   {result['seeded_trophies']}")
        print("\nTest Accounts for Postman & Web:")
        for acc in result["test_accounts"]:
            print(f"  • {acc['role'].upper():<9} : {acc['email']:<24} (Password: {acc['password']})")
        print("=" * 60 + "\n")

    await engine.dispose()


if __name__ == "__main__":
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    asyncio.run(run())
