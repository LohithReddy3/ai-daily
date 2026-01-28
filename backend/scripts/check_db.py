import asyncio
from backend.database import SessionLocal
from backend.models import Item, Story, Source, StorySummary
from sqlalchemy.future import select
from sqlalchemy import func

async def check_stats():
    async with SessionLocal() as session:
        # Count Sources
        r = await session.execute(select(func.count(Source.id)))
        sources_count = r.scalar()
        print(f"Sources: {sources_count}")

        # Count Items
        r = await session.execute(select(func.count(Item.id)))
        items_count = r.scalar()
        print(f"Items: {items_count}")

        # Count Stories
        r = await session.execute(select(func.count(Story.id)))
        stories_count = r.scalar()
        print(f"Stories: {stories_count}")

        # Count Summaries
        r = await session.execute(select(func.count(StorySummary.id)))
        summaries_count = r.scalar()
        print(f"Summaries: {summaries_count}")

        # Check Persona Breakdown
        r = await session.execute(select(StorySummary.persona, func.count(StorySummary.id)).group_by(StorySummary.persona))
        print("\nSummaries per Persona:")
        for persona, count in r.all():
            print(f" - {persona}: {count}")

if __name__ == "__main__":
    asyncio.run(check_stats())
