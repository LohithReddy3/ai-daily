from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
import json
from ..database import get_db
from ..models import DailyBrief, Persona
from ..schemas import DailyBrief as DailyBriefSchema

router = APIRouter(
    prefix="/brief",
    tags=["brief"],
)

@router.get("/today", response_model=DailyBriefSchema)
async def get_daily_brief(
    persona: Persona = Query(..., description="Target persona: builders, executors..."),
    db: AsyncSession = Depends(get_db)
):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    stmt = (
        select(DailyBrief)
        .where(DailyBrief.date == today)
        .where(DailyBrief.persona == persona)
    )
    
    result = await db.execute(stmt)
    brief = result.scalars().first()
    
    if not brief:
        # Fallback: Get the latest available brief for this persona
        latest_stmt = (
            select(DailyBrief)
            .where(DailyBrief.persona == persona)
            .order_by(DailyBrief.date.desc())
            .limit(1)
        )
        res = await db.execute(latest_stmt)
        brief = res.scalars().first()
        
    if not brief:
        raise HTTPException(status_code=404, detail=f"No briefs found. Ask admin to run job.")
        
    return brief

@router.get("/date/{date_str}", response_model=DailyBriefSchema)
async def get_brief_by_date(
    date_str: str,
    persona: Persona = Query(...),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(DailyBrief)
        .where(DailyBrief.date == date_str)
        .where(DailyBrief.persona == persona)
    )
    result = await db.execute(stmt)
    brief = result.scalars().first()
    
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")
        
    return brief
