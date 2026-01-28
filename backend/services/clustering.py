import asyncio
from sqlalchemy.future import select
from sqlalchemy import or_
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from ..database import SessionLocal
from ..models import Item, Story
import logging
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.65  # Adjust based on testing

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

async def cluster_items():
    async with SessionLocal() as session:
        # Get unclustered items
        result = await session.execute(select(Item).where(Item.story_id == None))
        unclustered_items = result.scalars().all()
        
        if not unclustered_items:
            logger.info("No unclustered items found.")
            return

        # Get recent stories (last 72 hours)
        three_days_ago = datetime.utcnow() - timedelta(hours=72)
        result = await session.execute(
            select(Story).where(Story.created_at >= three_days_ago).options(selectinload(Story.items))
        )
        recent_stories = result.scalars().all()
        
        created_stories = 0
        updated_stories = 0
        
        for item in unclustered_items:
            best_match = None
            best_score = 0.0
            
            # Simple title comparison against story canonical titles
            # (In production, comparing against all items in story is better, but this is MVP)
            for story in recent_stories:
                score = similarity(item.title.lower(), story.canonical_title.lower())
                if score > best_score:
                    best_score = score
                    best_match = story
            
            if best_match and best_score >= SIMILARITY_THRESHOLD:
                # Add to existing story
                item.story_id = best_match.id
                updated_stories += 1
                logger.info(f"Matched '{item.title}' to story '{best_match.canonical_title}' (Score: {best_score:.2f})")
            else:
                # Create new story
                new_story = Story(
                    canonical_title=item.title,
                    score=0.0, # Initial score
                    tags=[]
                )
                session.add(new_story)
                await session.flush() # Get ID
                
                item.story_id = new_story.id
                # Add to local list for subsequent matches in this loop
                recent_stories.append(new_story)
                created_stories += 1
                logger.info(f"Created new story for '{item.title}'")
        
        await session.commit()
        logger.info(f"Clustering complete. Created {created_stories} stories, updated {updated_stories}.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(cluster_items())
