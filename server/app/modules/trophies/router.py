import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.core.security import get_current_user
from app.modules.trophies.models import Trophy, UserTrophy
from app.modules.trophies.schemas import TrophyCreate, TrophyResponse, UserTrophyResponse
from app.modules.users.models import User

router = APIRouter(prefix="/trophies", tags=["trophies"])

@router.post("", response_model=TrophyResponse, status_code=201)
async def create_trophy(
    data: TrophyCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Only verified users or admins can create trophies
    user = await db.scalar(select(User).where(User.id == uuid.UUID(current_user["sub"])))
    if not user or (not user.is_verified and user.role != "admin"):
        raise HTTPException(status_code=403, detail="Only verified users can create trophies.")
    
    trophy = Trophy(
        name=data.name,
        points=data.points,
        icon_url=data.icon_url,
        creator_id=user.id
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
async def get_user_trophies(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserTrophy)
        .options(joinedload(UserTrophy.trophy))
        .where(UserTrophy.user_id == user_id)
        .order_by(UserTrophy.created_at.desc())
    )
    return list(result.scalars().all())

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
    # Only creator of the trophy can award it
    trophy = await db.scalar(select(Trophy).where(Trophy.id == trophy_id))
    if not trophy or str(trophy.creator_id) != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Not authorized to award this trophy.")
        
    user_trophy = UserTrophy(
        user_id=data.user_id,
        trophy_id=trophy_id,
        activity_id=data.activity_id
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
    return result.scalar_one()
