
import logging
import math
from typing import List, Tuple, Optional
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.database import SessionLocal
from backend.models import Story
from backend.services.embeddings import generate_embedding

logger = logging.getLogger(__name__)

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_v1 = math.sqrt(sum(a * a for a in v1))
    norm_v2 = math.sqrt(sum(b * b for b in v2))
    
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
        
    return dot_product / (norm_v1 * norm_v2)

async def search_similar_stories(query_text: str, exclude_story_id: str = None, limit: int = 3) -> List[Tuple[Story, float]]:
    """
    Search for stories similar to the query text using vector embeddings.
    Performs in-memory search over active stories.
    """
    # 1. Generate embedding for query
    query_embedding = await generate_embedding(query_text)
    if not query_embedding:
        logger.warning("Could not generate embedding for query.")
        return []

    # 2. Fetch all candidate stories (active, with embeddings)
    # Optimization: In production, use pgvector (DB side). 
    # For <10k stories, fetching ID, Title, Embedding is fast enough.
    async with SessionLocal() as session:
        stmt = (
            select(Story)
            .where(Story.is_active == True)
            .where(Story.embedding != None)
        )
        if exclude_story_id:
            stmt = stmt.where(Story.id != exclude_story_id)
            
        result = await session.execute(stmt)
        candidates = result.scalars().all()
        
        scores = []
        for story in candidates:
            if not story.embedding:
                continue
                
            score = cosine_similarity(query_embedding, story.embedding)
            scores.append((story, score))
            
        # 3. Sort and limit
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores[:limit]
