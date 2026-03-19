from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import func

from ..database import get_db
from ..models import Story, StorySummary, Item, User, UserSave, StoryItem, Persona
from .. import schemas
from .. import schemas
from ..dependencies import get_current_user, get_optional_current_user
from ..services.retrieval import search_similar_stories

router = APIRouter(
    prefix="/stories",
    tags=["stories"],
)

@router.get("/", response_model=List[schemas.Story])
async def get_stories(
    timeframe: str = Query("today", enum=["today", "7d", "30d", "all"]),
    limit: int = Query(50, ge=1, le=200),  # Added limit parameter
    persona: Optional[str] = None,
    category: Optional[str] = None,
    min_signal: int = 0,
    db: AsyncSession = Depends(get_db),
    user_data: Optional[dict] = Depends(get_optional_current_user)
):
    # Calculate date range
    now = datetime.utcnow()
    start_date = None
    
    if timeframe == "today":
        # Strictly 48 hours to prevent older stories from bleeding into "Today" feed
        start_date = now - timedelta(hours=48)
    elif timeframe == "7d":
        start_date = now - timedelta(days=7)
    elif timeframe == "30d":
        start_date = now - timedelta(days=30)
    
    # Base Query
    stmt = select(Story).where(Story.is_active == True)
    
    if start_date:
        stmt = stmt.where(Story.created_at >= start_date)
        
    if min_signal > 0:
        stmt = stmt.where(Story.signal_score >= min_signal)

    # Filter by Persona/Category
    # Need to join StorySummary if filtering by these, or check classification_json?
    # Checking StorySummary ensures content exists for that persona.
    if persona or category:
        stmt = stmt.join(StorySummary)
        if persona:
            try:
                persona_enum = Persona(persona)
                stmt = stmt.where(StorySummary.persona == persona_enum)
            except ValueError:
                 # If invalid persona string, return empty or ignore
                 # For safety, let's return empty, as it's an invalid filter
                 return []
        if category:
            # Support multiple categories (comma-separated)
            categories = [c.strip() for c in category.split(',')]
            stmt = stmt.where(StorySummary.category.in_(categories))
           # Sort
    # Fetch enough candidates to allow diversity mixing (3x limit)
    stmt = stmt.order_by(Story.created_at.desc(), Story.signal_score.desc())
    stmt = stmt.limit(limit * 3)
    
    # Eager load related data
    # Eager load related data
    # Optimization: Use selectinload for collections (items) to avoid Cartesian product of joinedload
    stmt = stmt.options(
        selectinload(Story.items).selectinload(Item.source), 
        selectinload(Story.summaries)
    )
    
    # --- Two-Stage Diversity Selection ---
    # Stage A: Build candidate pool with source guarantees
    
    # 1. Get top N by signal (high-quality stories) - ensure enough signal depth
    # Use 2.4x limit for signal candidates (e.g. 120 for limit=50, 240 for limit=100)
    top_signal_limit = int(limit * 2.4)
    top_signal_stmt = stmt.order_by(Story.signal_score.desc(), Story.created_at.desc()).limit(top_signal_limit)
    result = await db.execute(top_signal_stmt)
    top_signal_stories = result.scalars().unique().all()
    
    # 2. Get top 2 stories per source (guarantee source coverage)
    # Increase limit to ensure we find stories from lower-volume sources 
    # even if high-volume sources (OpenAI, HF) have hundreds of recent items
    per_source_stmt = stmt.order_by(Story.created_at.desc(), Story.signal_score.desc()).limit(2500)
    result = await db.execute(per_source_stmt)
    all_stories = result.scalars().unique().all()
    
    # Group by source and take top 2 per source
    by_source_temp = {}
    for s in all_stories:
        src_name = "Unknown"
        if s.items and s.items[0].source:
            src_name = s.items[0].source.name
        
        if src_name not in by_source_temp:
            by_source_temp[src_name] = []
        by_source_temp[src_name].append(s)
    
    guaranteed_stories = []
    for src, stories_list in by_source_temp.items():
        # Take top 2 by signal score per source
        sorted_by_signal = sorted(stories_list, key=lambda x: x.signal_score, reverse=True)
        guaranteed_stories.extend(sorted_by_signal[:2])
    
    # Combine and deduplicate
    candidate_pool = list({s.id: s for s in (top_signal_stories + guaranteed_stories)}.values())
    
    # Stage B: Apply soft per-source caps and build final list
    by_source = {}
    for s in candidate_pool:
        src_name = "Unknown"
        if s.items and s.items[0].source:
            src_name = s.items[0].source.name
        
        if src_name not in by_source:
            by_source[src_name] = []
        by_source[src_name].append(s)
    
    # Sort each source's stories by signal score
    for src in by_source:
        by_source[src] = sorted(by_source[src], key=lambda x: x.signal_score, reverse=True)
    
    # Interleave with soft cap of 3 stories per source
    final_list = []
    source_counts = {}
    MAX_PER_SOURCE = 3
    
    # Round-robin through sources with soft cap
    while len(final_list) < limit and any(by_source.values()):
        added_this_round = False
        
        # Sort sources by how many stories they've contributed (fewer first)
        sorted_sources = sorted(by_source.keys(), key=lambda src: source_counts.get(src, 0))
        
        for src in sorted_sources:
            if by_source[src]:
                # Stage 1: Respect soft cap
                if source_counts.get(src, 0) < MAX_PER_SOURCE:
                    s = by_source[src].pop(0)
                    final_list.append(s)
                    source_counts[src] = source_counts.get(src, 0) + 1
                    added_this_round = True
                    if len(final_list) >= limit:
                        break
        
        if not added_this_round:
            # If we're stuck (all active sources hit cap) but have space, relax cap
            # Take the highest signal score available across ALL remaining sources
            remaining_pool = []
            for src_list in by_source.values():
                remaining_pool.extend(src_list)
            
            # Sort by signal score
            remaining_pool.sort(key=lambda x: x.signal_score, reverse=True)
            
            # Fill remaining slots
            slots_needed = limit - len(final_list)
            final_list.extend(remaining_pool[:slots_needed])
            break
            
    stories = final_list

    # Note: Fallback summaries are now handled in the frontend
    # The frontend will use item.clean_text or item.title if no summaries exist
    
    # Persistence Check
    if user_data:
        user_id = user_data['id']
        story_ids = [s.id for s in stories]
        
        if story_ids:
            save_stmt = select(UserSave.story_id).where(
                UserSave.user_id == user_id,
                UserSave.story_id.in_(story_ids)
            )
            save_result = await db.execute(save_stmt)
            saved_ids = set(save_result.scalars().all())
            
            for s in stories:
                s.is_saved = s.id in saved_ids
            
    return stories

@router.get("/{story_id}", response_model=schemas.Story)
async def get_story(story_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Story)
        .where(Story.id == story_id)
        .options(selectinload(Story.items).selectinload(Item.source), selectinload(Story.summaries))
    )
    result = await db.execute(stmt)
    story = result.scalars().first()
    
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # RAG: Fetch related stories
    try:
        similar = await search_similar_stories(story.canonical_title, exclude_story_id=story.id, limit=3)
        story.related_stories = [
            schemas.RelatedStory(
                id=s.id,
                canonical_title=s.canonical_title,
                created_at=s.created_at,
                similarity_score=score
            )
            for s, score in similar
        ]
    except Exception as e:
        print(f"Error fetching related stories: {e}")
        story.related_stories = []

    return story

# --- Persistence ---

@router.post("/{story_id}/save")
async def save_story(
    story_id: str, 
    user_data: dict = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    user_id = user_data['id']
    email = user_data.get('email')
    
    # 1. Sync User
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user:
        new_user = User(id=user_id, email=email)
        db.add(new_user)
        await db.flush()
        
    # 2. Check if already saved
    stmt = select(UserSave).where(
        UserSave.user_id == user_id,
        UserSave.story_id == story_id
    )
    res = await db.execute(stmt)
    existing = res.scalars().first()
    
    if not existing:
        entry = UserSave(user_id=user_id, story_id=story_id)
        db.add(entry)
        await db.commit()
        return {"status": "saved", "saved": True}
        
    return {"status": "already_saved", "saved": True}

@router.delete("/{story_id}/save")
async def unsave_story(
    story_id: str,
    user_data: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_id = user_data['id']
    
    stmt = select(UserSave).where(
        UserSave.user_id == user_id,
        UserSave.story_id == story_id
    )
    res = await db.execute(stmt)
    existing = res.scalars().first()
    
    if existing:
        await db.delete(existing)
        await db.commit()
        return {"status": "unsaved", "saved": False}
        
    return {"status": "not_found", "saved": False}

@router.get("/user/saved", response_model=List[schemas.Story])
async def get_saved_stories(
    user_data: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_id = user_data['id']
    
    stmt = (
        select(Story)
        .join(UserSave, Story.id == UserSave.story_id)
        .where(UserSave.user_id == user_id)
        .options(selectinload(Story.items), selectinload(Story.summaries))
        .order_by(UserSave.saved_at.desc())
    )
    
    result = await db.execute(stmt)
    stories = result.scalars().unique().all()
    
    for s in stories:
        s.is_saved = True
        
    return stories
