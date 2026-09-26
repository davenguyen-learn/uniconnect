import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_optional_current_user
from app.modules.trophies.models import Trophy, UserTrophy
from app.modules.trophies.schemas import TrophyCreate, TrophyResponse, UserTrophyResponse, ActivitySimple
from app.modules.users.models import User

router = APIRouter(prefix="/trophies", tags=["trophies"])

@router.post("", response_model=TrophyResponse, status_code=201)
async def create_trophy(
    data: TrophyCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Only edu_org or admins can create trophies
    user = await db.scalar(select(User).where(User.id == uuid.UUID(current_user["sub"])))
    user_role = user.role.value if (user and hasattr(user.role, "value")) else str(user.role if user else "")
    if not user or user_role not in ["admin", "edu_org"]:
        raise HTTPException(
            status_code=403,
            detail="Chỉ Ban Quản trị hoặc Tổ chức Giáo dục (edu_org) mới có quyền tạo Trophy."
        )
    
    existing = await db.scalar(select(Trophy).where(Trophy.name == data.name))
    if existing:
        if data.description is not None:
            existing.description = data.description
        if data.activity_id is not None:
            existing.activity_id = data.activity_id
        await db.commit()
        await db.refresh(existing)
        return existing

    trophy = Trophy(
        name=data.name,
        description=data.description,
        activity_id=data.activity_id,
    )
    db.add(trophy)
    await db.commit()
    await db.refresh(trophy)
    return trophy

@router.get("", response_model=list[TrophyResponse])
async def list_trophies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Trophy).order_by(Trophy.created_at.desc()))
    return list(result.scalars().all())

@router.get("/user/{user_id}", response_model=list[UserTrophyResponse])
async def get_user_trophies(
    user_id: uuid.UUID,
    current_user: dict | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(UserTrophy)
        .options(
            joinedload(UserTrophy.trophy),
            joinedload(UserTrophy.activity)
        )
        .where(UserTrophy.user_id == user_id)
        .order_by(UserTrophy.created_at.desc())
    )
    user_trophies = list(result.unique().scalars().all())

    viewer_id = uuid.UUID(current_user["sub"]) if (current_user and "sub" in current_user) else None
    viewer_role = current_user.get("role") if current_user else None
    is_admin = viewer_role == "admin"

    activity_ids = [ut.activity_id for ut in user_trophies if ut.activity_id]
    viewer_approved_acts = set()
    if viewer_id and activity_ids:
        from app.modules.participation.models import JoinRequest, RequestStatus
        res_parts = await db.execute(
            select(JoinRequest.activity_id).where(
                JoinRequest.activity_id.in_(activity_ids),
                JoinRequest.user_id == viewer_id,
                JoinRequest.status == RequestStatus.approved,
            )
        )
        viewer_approved_acts = set(res_parts.scalars().all())

    response_items = []
    for ut in user_trophies:
        item = UserTrophyResponse.model_validate(ut)
        if ut.activity:
            privacy_val = (
                ut.activity.privacy.value
                if hasattr(ut.activity.privacy, "value")
                else str(ut.activity.privacy)
            )
            is_private = privacy_val == "private"
            has_access = (
                not is_private
                or is_admin
                or (viewer_id and ut.activity.host_id == viewer_id)
                or (ut.activity.id in viewer_approved_acts)
            )
            if has_access:
                item.activity = ActivitySimple(
                    id=ut.activity.id,
                    title=ut.activity.title,
                    privacy=privacy_val,
                    is_accessible=True,
                )
            else:
                item.activity = ActivitySimple(
                    id=None,
                    title="Sự kiện nội bộ",
                    privacy="private",
                    is_accessible=False,
                )
        response_items.append(item)

    return response_items

class TrophyAwardRequest(BaseModel):
    user_id: uuid.UUID
    activity_id: uuid.UUID | None = None

@router.post("/{trophy_id}/award", response_model=UserTrophyResponse)
async def award_trophy(
    trophy_id: uuid.UUID,
    data: TrophyAwardRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    trophy = await db.scalar(select(Trophy).where(Trophy.id == trophy_id))
    if not trophy:
        raise HTTPException(status_code=404, detail="Trophy not found.")
        
    user_trophy = UserTrophy(
        user_id=data.user_id,
        trophy_id=trophy_id,
        activity_id=data.activity_id or trophy.activity_id
    )
    db.add(user_trophy)
    await db.commit()
    await db.refresh(user_trophy)
    
    # Reload with relations
    result = await db.execute(
        select(UserTrophy)
        .options(joinedload(UserTrophy.trophy))
        .where(UserTrophy.id == user_trophy.id)
    )
    return result.unique().scalar_one()
