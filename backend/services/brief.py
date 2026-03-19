from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from ..database import SessionLocal
from ..models import Story, StorySummary, DailyBrief, Persona, StoryState
import asyncio
import logging
import json
import uuid

logger = logging.getLogger(__name__)

async def job_generate_daily_brief():
    """Job F: Build Daily Brief"""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    async with SessionLocal() as session:
        for persona in Persona:
            logger.info(f"Generating brief for {persona.value}...")
            
            # Select candidate stories
            # Criteria:
            # - is_active
            # - story_state in (new, evolving) OR updated recently
            # - has summary for this persona
            # - signal_score > threshold
            # - classification_json.show = true
            
            # We can't easily query JSON fields deep in SQLAlchemy without dialect specific operators.
            # So we fetch potential candidates and filter in Python.
            
            stmt = (
                select(Story)
                .join(Story.summaries)
                .where(Story.is_active == True)
                .where(Story.signal_score > 40) # Higher threshold for brief
                .where(StorySummary.persona == persona)
                .options(selectinload(Story.summaries))
            )
            
            result = await session.execute(stmt)
            candidates = result.scalars().unique().all()
            
            final_list = []
            
            for story in candidates:
                # Check show flag
                cls = story.classification_json or {}
                if not cls.get("show", False):
                    continue
                
                # Check narrative importance
                importance = cls.get("importance", "good_to_know")
                
                # Find the summary for this persona
                summary = next((s for s in story.summaries if s.persona == persona), None)
                if not summary:
                    continue
                
                final_list.append({
                    "story_id": str(story.id),
                    "title": story.canonical_title,
                    "summary": summary.summary_short,
                    "importance": importance,
                    "signal_score": story.signal_score,
                    "bullets": summary.summary_bullets,
                    "urls": summary.supporting_urls,
                    "why_it_matters": summary.why_it_matters
                })
            
            # Sort: "must_know" first, then signal_score desc
            def sort_key(item):
                imp_score = 2 if item["importance"] == "must_know" else 1
                return (imp_score, item["signal_score"])
                
            final_list.sort(key=sort_key, reverse=True)
            
            # Top 10
            top_items = final_list[:10]
            
            # Save DailyBrief
            # Check if exists for today/persona
            existing_stmt = select(DailyBrief).where(
                DailyBrief.date == today,
                DailyBrief.persona == persona
            )
            res = await session.execute(existing_stmt)
            brief = res.scalars().first()
            
            if not brief:
                brief = DailyBrief(
                    id=str(uuid.uuid4()),
                    date=today,
                    persona=persona
                )
                session.add(brief)
            
            brief.items_json = top_items
            brief.model_name = "v2-pipeline"
            
            logger.info(f"Saved {len(top_items)} items for {persona.value} brief.")
        
        await session.commit()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(job_generate_daily_brief())
