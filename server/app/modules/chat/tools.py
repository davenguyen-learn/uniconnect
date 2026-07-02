"""Tools for LLM function calling."""

import uuid
from typing import Annotated

from sqlalchemy import and_, or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_SetSRID, ST_Distance, ST_X, ST_Y

from app.modules.activities.models import Activity
from app.modules.groups.models import GroupMember
from datetime import datetime, timezone

async def search_activities_tool(
    db: AsyncSession,
    user_id: uuid.UUID,
    category: str | None = None,
    keyword: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
    radius_meters: int = 10000,
    limit: int = 5,
) -> list[dict]:
    """Search for activities based on user criteria. 
    This is called by the LLM when recommending activities.
    """
    now = datetime.now(timezone.utc)
    
    # Base access filter: Public activity OR user is in the group
    access_filter = or_(
        Activity.group_id.is_(None),
        Activity.group_id.in_(
            select(GroupMember.group_id).where(GroupMember.user_id == user_id)
        )
    )

    base_filter = and_(
        Activity.is_deleted == False,
        Activity.end_time > now,
        access_filter,
    )

    if category:
        base_filter = and_(base_filter, Activity.category.ilike(f"%{category}%"))
        
    if keyword:
        base_filter = and_(
            base_filter, 
            or_(
                Activity.title.ilike(f"%{keyword}%"),
                Activity.description.ilike(f"%{keyword}%")
            )
        )

    distance_col = None
    if lat is not None and lng is not None:
        point = ST_SetSRID(ST_MakePoint(lng, lat), 4326)
        base_filter = and_(
            base_filter,
            Activity.location.isnot(None),
            ST_DWithin(Activity.location, point, radius_meters)
        )
        distance_col = ST_Distance(Activity.location, point).label("distance_meters")

    query = select(Activity)
    if distance_col is not None:
        query = query.add_columns(distance_col).order_by(distance_col.asc())
    else:
        query = query.order_by(Activity.start_time.asc())
        
    query = query.options(joinedload(Activity.host)).where(base_filter).limit(limit)
    
    result = await db.execute(query)
    
    activities_data = []
    if distance_col is not None:
        rows = result.unique().all()
        for row in rows:
            activity = row[0]
            dist = row[1]
            activities_data.append({
                "id": str(activity.id),
                "title": activity.title,
                "description": activity.description,
                "category": activity.category,
                "start_time": activity.start_time.isoformat(),
                "host_name": activity.host.username,
                "distance_meters": round(dist, 2)
            })
    else:
        activities = result.unique().scalars().all()
        for activity in activities:
            activities_data.append({
                "id": str(activity.id),
                "title": activity.title,
                "description": activity.description,
                "category": activity.category,
                "start_time": activity.start_time.isoformat(),
                "host_name": activity.host.username,
            })
            
    return activities_data
