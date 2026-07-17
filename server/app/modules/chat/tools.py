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
    semantic_query: str | None = None,
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
    
    similarity_col = None
    if semantic_query:
        from app.modules.chat.embeddings import generate_embedding
        query_embedding = generate_embedding(semantic_query)
        if query_embedding:
            similarity_col = Activity.embedding.cosine_distance(query_embedding).label("similarity_distance")
            query = query.add_columns(similarity_col)
            # Only keep results with reasonable similarity if needed, or just sort by it
            query = query.order_by(Activity.embedding.cosine_distance(query_embedding).asc())

    if distance_col is not None:
        query = query.add_columns(distance_col)
        if similarity_col is None:
            query = query.order_by(distance_col.asc())
    elif similarity_col is None:
        query = query.order_by(Activity.start_time.asc())
        
    query = query.options(joinedload(Activity.host)).where(base_filter).limit(limit)
    
    result = await db.execute(query)
    
    activities_data = []
    rows = result.unique().all()
    for row in rows:
        # row[0] is always the Activity instance when using select(Activity).add_columns(...)
        activity = row[0] if isinstance(row, tuple) else row
        
        data = {
            "id": str(activity.id),
            "title": activity.title,
            "description": activity.description,
            "category": activity.category,
            "start_time": activity.start_time.isoformat(),
            "host_name": activity.host.username,
        }
        
        # If we added columns, let's see if we can find distance or similarity
        # Actually it's safer to just return the activity since Gemini doesn't strictly need the distance
        # but if we want, we can extract it if distance_col was added.
        if distance_col is not None and isinstance(row, tuple):
            # Distance is either at index 1 or 2 depending on whether similarity_col was added
            dist_idx = 2 if similarity_col is not None else 1
            data["distance_meters"] = round(row[dist_idx], 2)
            
        activities_data.append(data)
        
    return activities_data
