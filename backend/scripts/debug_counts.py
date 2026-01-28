import asyncio
from backend.database import SessionLocal
from backend.models import Story, Item, StorySummary
from sqlalchemy.future import select
from sqlalchemy import func

async def check():
    async with SessionLocal() as session:
        result = await session.execute(select(func.count(Story.id)))
        count = result.scalar()
        print(f"Total Stories: {count}")
        
        result = await session.execute(select(func.count(Item.id)))
        items = result.scalar()
        print(f"Total Items: {items}")
        
        # Check LLM query logic
        stmt = (
            select(Story)
            .outerjoin(Story.items)
            .group_by(Story.id)
            .limit(5)
        )
        result = await session.execute(stmt)
        stories = result.scalars().unique().all()
        print(f"LLM Query found: {len(stories)} stories")
        if len(stories) > 0:
             print(f"Sample story items: {len(stories[0].items)}")

if __name__ == "__main__":
    asyncio.run(check())
