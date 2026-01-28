from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timedelta

from ..database import get_db
from ..models import Story, StorySummary
from .. import schemas

router = APIRouter(
    prefix="/stories",
    tags=["stories"],
)

@router.get("/", response_model=List[schemas.Story])
async def get_stories(
    timeframe: str = Query("today", enum=["today", "7d", "30d"]),
    persona: Optional[str] = None,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    # Calculate date range
    now = datetime.utcnow()
    if timeframe == "today":
        start_date = now - timedelta(hours=24)
    elif timeframe == "7d":
        start_date = now - timedelta(days=7)
    else:
        start_date = now - timedelta(days=30)
    
    from sqlalchemy import func
    from ..models import Item

    # Query stories
    # Join with StorySummary for filtering and Item for signal ranking
    stmt = (
        select(Story)
        .outerjoin(StorySummary)
        .outerjoin(Item)
        .where(Story.created_at >= start_date)
    )

    if persona:
        # Use the enum value if possible or ensure comparison works
        stmt = stmt.where(StorySummary.persona == persona)
    
    if category:
        stmt = stmt.where(StorySummary.category == category)

    # Rank by item count (signal)
    stmt = (
        stmt.group_by(Story.id)
        .options(selectinload(Story.items), selectinload(Story.summaries))
        .order_by(func.count(Item.id).desc(), Story.created_at.desc())
        .limit(10 if timeframe == "today" else 30)
    )
    
    result = await db.execute(stmt)
    # Use unique() because of the joins
    stories = result.scalars().unique().all()
    
    return stories

@router.get("/{story_id}", response_model=schemas.Story)
async def get_story(story_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Story)
        .where(Story.id == story_id)
        .options(selectinload(Story.items), selectinload(Story.summaries))
    )
    result = await db.execute(stmt)
    story = result.scalars().first()
    
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
        
    return story
