import asyncio
from backend.database import SessionLocal
from backend.models import Story, StorySummary, Persona, Item, Source
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.services.llm import generate_summary

async def force_populate():
    async with SessionLocal() as session:
        # Find stories that contain items from Thought Leaders
        stmt = (
            select(Story)
            .join(Story.items)
            .join(Item.source)
            .where(Source.name.in_([
                "Lil'Log (Lilian Weng)", 
                "Andrej Karpathy", 
                "Simon Willison"
            ]))
            .options(selectinload(Story.items))
        )
        result = await session.execute(stmt)
        stories = result.scalars().unique().all()
        print(f"Found {len(stories)} stories from Thought Leaders")
        
        for story in stories:
            print(f"Processing: {story.canonical_title}")
            story_text = "\n\n".join([f"Title: {i.title}\nText: {i.raw_text}" for i in story.items])
            
            # Force generate for thought_leaders
            data = await generate_summary(story_text, Persona.thought_leaders, "Deep Dives")
            
            if data:
                print("  -> Summary Generated!")
                new_summary = StorySummary(
                    story_id=story.id,
                    persona=Persona.thought_leaders,
                    category="Deep Dives",
                    summary_short=data.get("summary_short", ""),
                    summary_bullets=data.get("bullets", []),
                    confidence="high",
                    key_entities=[data.get("actionable_next_step", "")]
                )
                session.add(new_summary)
            else:
                print("  -> Failed to generate.")
        
        await session.commit()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(force_populate())
