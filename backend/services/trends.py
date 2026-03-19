
import logging
from datetime import datetime, timedelta
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from ..database import SessionLocal
from ..models import Story, Item
from .llm import call_llm_with_retry

logger = logging.getLogger(__name__)

TRENDS_PROMPT = """
ROLE: StrategicIntelligenceUnit
TASK: Trend Analysis & Pattern Recognition

INPUT:
A list of high-signal AI story titles from the last {days} days.

GOAL:
Identify 3-5 major thematic trends or patterns that connect these stories. 
Do NOT just list the news. Find the underlying current.

REQUIREMENTS:
1. **Connect the dots**: How do "Model X released" and "Chip Y announced" relate?
2. **Themes, not summaries**: "Agentic Coding" is a theme. "Cursor released v2" is just news.
3. **Evidence**: You must cite which stories support this theme (using their exact IDs from the input list).

OUTPUT STRUCTURE (STRICT JSON):
[
  {{
    "title": "Short, Punchy Theme Title (Max 5 words)",
    "explanation": "1-2 sentences explaining the shift or pattern. Why does this matter?",
    "evidence_story_ids": ["id_1", "id_2"]
  }}
]

STORY LIST:
{stories_text}

Return ONLY the JSON.
"""

async def analyze_trends(days: int = 7):
    """
    Analyzes high-signal stories from the window and returns themes.
    """
    async with SessionLocal() as session:
        # 1. Fetch Stories
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        stmt = (
            select(Story)
            .where(Story.is_active == True)
            .where(Story.created_at >= cutoff)
            .where(Story.signal_score >= 50) # Only significant stories
            .order_by(Story.signal_score.desc())
            .options(selectinload(Story.items).selectinload(Item.source))
            .limit(100) # Limit context window usage
        )
        
        result = await session.execute(stmt)
        stories = result.scalars().all()
        
        if not stories:
            return []
            
        # 2. Format for LLM
        stories_text = ""
        story_map = {}
        for s in stories:
            stories_text += f"- [ID: {s.id}] {s.canonical_title} (Score: {s.signal_score})\n"
            story_map[s.id] = s
            
        # 3. Call LLM
        prompt = TRENDS_PROMPT.format(days=days, stories_text=stories_text)
        
        themes = await call_llm_with_retry(prompt, model_name="gemini-2.0-flash")
        
        if not themes:
            logger.warning("Trends analysis returned no themes.")
            return []
            
        # 4. Hydrate Evidence (Return rich objects for UI/Visuals)
        final_themes = []
        for theme in themes:
            evidence_ids = theme.get("evidence_story_ids", [])
            evidence_items = []
            
            for eid in evidence_ids:
                if eid in story_map:
                    story = story_map[eid]
                    
                    # Get primary item for metadata
                    primary_item = story.items[0] if story.items else None
                    url = primary_item.url if primary_item else ""
                    source_name = primary_item.source.name if primary_item and primary_item.source else "Unknown"
                    
                    evidence_items.append({
                        "id": str(story.id),
                        "title": story.canonical_title,
                        "url": url,
                        "signal_score": story.signal_score,
                        "published_at": story.created_at.isoformat() if story.created_at else None,
                        "source": source_name
                    })
            
            # clean up and assign rich evidence
            theme["evidence"] = evidence_items
            # keep legacy fields for compatibility if needed, but UI should switch to 'evidence'
            theme["evidence_titles"] = [e["title"] for e in evidence_items] 
            final_themes.append(theme)
            
        return final_themes

async def get_universe_items(limit: int = 800):
    """
    Fetches recent raw items to populate the background 'Data Universe'.
    """
    async with SessionLocal() as session:
        # Relaxed Constraints: Fetch last N items regardless of time
        # to ensure the universe is populated even if ingestion hasn't run recently.
        
        stmt = (
            select(Story)
            .where(Story.is_active == True, Story.universe_x.isnot(None))
            .order_by(Story.created_at.desc())
            .options(selectinload(Story.items).selectinload(Item.source))
            .limit(limit)
        )
        
        result = await session.execute(stmt)
        stories = result.scalars().all()
        
        universe_data = []
        for story in stories:
            # Fallbacks for source tracking
            source_name = "Unknown"
            published_at = None
            if story.items:
                if story.items[0].source:
                    source_name = story.items[0].source.name
                published_at = story.items[0].published_at

            universe_data.append({
                "id": str(story.id),
                "title": story.canonical_title,
                "url": story.items[0].url if story.items else "",
                "type": "story",
                "source": source_name,
                "published_at": published_at.isoformat() if published_at else None,
                "universe_x": story.universe_x,
                "universe_y": story.universe_y,
                "universe_cluster": story.universe_cluster
            })
            
        return universe_data
