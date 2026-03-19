from datetime import datetime, timedelta
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from ..database import SessionLocal
from ..models import Item, Story, StoryItem, Source, StoryState
import asyncio
import logging
import uuid
from sqlalchemy import func

import logging
import uuid
from sqlalchemy import func
from .embeddings import generate_embedding

logger = logging.getLogger(__name__)


SIMILARITY_THRESHOLD = 0.65 # Conservative baseline

def text_jaccard_similarity(s1, s2):
    set1 = set(s1.lower().split())
    set2 = set(s2.lower().split())
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union else 0.0

async def find_best_match(session, item, window_hours=48):
    # Find active stories in window
    cutoff = datetime.utcnow() - timedelta(hours=720)
    
    # 1. Check title similarity with existing stories
    # We load stories that are active
    stmt = (
        select(Story)
        .where(Story.updated_at >= cutoff)
        .where(Story.is_active == True)
        .options(selectinload(Story.story_items).selectinload(StoryItem.item))
    )
    result = await session.execute(stmt)
    stories = result.scalars().unique().all()
    
    best_story = None
    best_score = 0.0
    
    for story in stories:
        # Check similarity with story title or its items
        # Heuristic: Compare with story canonical title first
        score = text_jaccard_similarity(item.title, story.canonical_title)
        
        # Also check items in the story (expensive? limit to top 3)
        # item_scores = [text_jaccard_similarity(item.title, si.item.title) for si in story.story_items]
        # max_item_score = max(item_scores) if item_scores else 0
        # final_score = max(score, max_item_score)
        
        if score > best_score:
            best_score = score
            best_story = story
            
    if best_score >= SIMILARITY_THRESHOLD:
        return best_story, best_score
    return None, 0.0

async def job_cluster_stories():
    """Job C: Story Formation"""
    async with SessionLocal() as session:
        # Get unclustered items
        # Items that don't have a StoryItem entry
        # Subquery? Or just iterate all recent items?
        # Efficient: SELECT * FROM items WHERE id NOT IN (SELECT item_id FROM story_items) AND created_at > 24h
        
        cutoff = datetime.utcnow() - timedelta(hours=48)
        
        stmt = (
            select(Item)
            .outerjoin(StoryItem, Item.id == StoryItem.item_id)
            .where(StoryItem.story_id == None)
            .where(Item.ingested_at >= cutoff)
            .options(selectinload(Item.source))
        )
        
        result = await session.execute(stmt)
        unclustered = result.scalars().all()
        
        logger.info(f"Clustering {len(unclustered)} items...")
        
        for item in unclustered:
            # Double check to prevent race conditions/IntegrityErrors
            existing_link = await session.execute(
                select(StoryItem).where(StoryItem.item_id == item.id)
            )
            if existing_link.scalars().first():
                logger.info(f"Skipping {item.id}, already clustered.")
                continue

            story, score = await find_best_match(session, item)
            
            if story:
                logger.info(f"Matched {item.title} -> {story.canonical_title} ({score:.2f})")
                new_link = StoryItem(
                    story_id=story.id,
                    item_id=item.id,
                    similarity_score=score,
                    is_primary=False
                )
                session.add(new_link)
                # Update story updated_at
                story.updated_at = datetime.utcnow()
                story.story_state = StoryState.evolving
            else:
                logger.info(f"New Story: {item.title}")
                # Create new story
                new_story = Story(
                    canonical_title=item.title,
                    story_hash=str(uuid.uuid4()), # Placeholder hash or use content hash
                    story_state=StoryState.new
                )
                
                # RAG: Generate Embedding immediately
                try:
                    # Use title + summary/text for embedding
                    text_for_embedding = f"{item.title}\n{item.clean_text[:500] if item.clean_text else ''}"
                    emb = await generate_embedding(text_for_embedding)
                    if emb:
                        new_story.embedding = emb
                        logger.info(f"Generated embedding for new story: {item.title[:30]}...")
                except Exception as e:
                    logger.error(f"Failed to generate embedding during clustering: {e}")
                    
                session.add(new_story)
                await session.flush() # Get ID
                
                new_link = StoryItem(
                    story_id=new_story.id,
                    item_id=item.id,
                    is_primary=True, # First one is primary
                    similarity_score=1.0
                )
                session.add(new_link)
            
            # Commit every 10 items to prevent DB lock
            if (unclustered.index(item) + 1) % 10 == 0:
                await session.commit()
        
        await session.commit()

# Also ensure "primary" item selection logic runs periodically or after clustering
async def update_story_metadata():
    pass # Implementation details: pick best title based on source weights

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(job_cluster_stories())
