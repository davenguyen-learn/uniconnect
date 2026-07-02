import asyncio
import uuid
import datetime
import random
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

from app.core.config import settings
from app.modules.users.models import User
from app.modules.activities.models import Activity
from app.modules.groups.models import Group  # Required for relationship resolution

async def seed_nearby():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as db:
        # Get a user to act as host
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        
        if not user:
            print("No users found in database.")
            return

        print(f"Using user {user.username} as host.")

        # Target location
        base_lat = 10.97814696824309
        base_lng = 106.86980154532799
        
        activities_data = [
            ("Dong Nai Camping", "Weekend camping trip", "Social", base_lat + 0.01, base_lng + 0.01),
            ("HCMC Tech Meetup", "Discussing React and Node.js", "Study", base_lat - 0.05, base_lng - 0.02),
            ("Morning Run", "5km run around the lake", "Sports", base_lat + 0.005, base_lng - 0.005),
            ("Food Tour", "Trying local street food", "Social", base_lat - 0.01, base_lng + 0.02),
            ("Board Game Night", "Catan and Monopoly", "Gaming", base_lat, base_lng),
        ]
        
        activities = []
        for title, desc, cat, lat, lng in activities_data:
            start_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=random.randint(1, 5))
            act = Activity(
                title=title,
                description=desc,
                category=cat,
                location=f"POINT({lng} {lat})",
                location_name="Nearby Location",
                start_time=start_time,
                end_time=start_time + datetime.timedelta(hours=2),
                host_id=user.id,
                group_id=None,
                max_participants=10,
                current_participants=1
            )
            db.add(act)
            activities.append(act)
            
        await db.commit()
        print("Successfully seeded 5 nearby activities!")

if __name__ == "__main__":
    asyncio.run(seed_nearby())
