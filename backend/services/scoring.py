from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from ..database import SessionLocal
from ..models import Story, StoryItem, Source, StoryState, Item
import asyncio
import logging
from sqlalchemy import func

logger = logging.getLogger(__name__)

BENCHMARK_KEYWORDS = ["benchmark", "evals", "accuracy", "perplexity", "score", "top-1", "mmlu", "humaneval", "latency", "tok/s", "token", "context window"]
FIRST_HAND_KEYWORDS = ["paper", "official", "release", "launch", "announcing", "introducing", "blog.google", "openai.com", "anthropic.com", "meta.com"]

async def calculate_signal_score(story, sources):
    score = 0
    
    # 1. Source Reputation
    total_reputation = sum(s.reputation_weight for s in sources)
    score += total_reputation * 10
    
    # 2. Number of distinct sources
    unique_domains = len(set(s.url for s in sources)) # Simplified domain check
    if unique_domains > 1:
        score += unique_domains * 5
    
    # 3. Content Length of primary item
    primary_item = next((si.item for si in story.story_items if si.is_primary), None)
    if primary_item and primary_item.content_length > 1000:
        score += 5
    if primary_item and primary_item.content_length > 5000: # Deep dive
        score += 10
        
    # 4. Keywords
    text = (primary_item.clean_text or primary_item.raw_text or "").lower()
    
    # Benchmarks
    matches = sum(1 for kw in BENCHMARK_KEYWORDS if kw in text)
    if matches > 0:
        score += min(matches * 2, 20)
        
    # First-hand
    is_first_hand = any(kw in text for kw in FIRST_HAND_KEYWORDS)
    if is_first_hand:
        score += 15
        
    # Recency (decay logic not strictly required but good)
    # Keeping raw signal high is okay, display rank handles recency
    
    return min(score, 100)

async def calculate_confidence(story, sources):
    # Number of sources confirming
    count = len(sources)
    if count >= 3:
        return 0.9
    if count == 2:
        return 0.7
    return 0.5 # Single source default

async def job_score_stories():
    """Job D: Signal Scoring"""
    async with SessionLocal() as session:
        # Get active stories or modified ones
        stmt = (
            select(Story)
            .where(Story.is_active == True)
            .options(joinedload(Story.story_items).joinedload(StoryItem.item).joinedload(Item.source))
        )
        
        result = await session.execute(stmt)
        stories = result.scalars().unique().all()
        
        for story in stories:
            sources = [si.item.source for si in story.story_items if si.item and si.item.source]
            
            new_signal = await calculate_signal_score(story, sources)
            new_conf = await calculate_confidence(story, sources)
            
            story.signal_score = new_signal
            story.confidence_score = new_conf
            story.last_scored_at = datetime.utcnow()
            
            # State update logic
            # If no updates > 24h, mark stable
            time_since_update = (datetime.utcnow() - (story.updated_at or story.created_at)).total_seconds() / 3600
            if time_since_update > 24 and story.story_state == StoryState.evolving:
                story.story_state = StoryState.stable
                
            # If > 7 days, stale
            if time_since_update > 24 * 7:
                 story.story_state = StoryState.stale
                 story.is_active = False
            
            logger.info(f"Story {story.canonical_title[:20]}... Score: {new_signal}")
            
        await session.commit()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(job_score_stories())
