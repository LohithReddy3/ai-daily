import asyncio
from backend.database import SessionLocal
from backend.models import Story, Item
from sqlalchemy import select, func

async def check_latest_dates():
    async with SessionLocal() as session:
        # Check latest Story
        stmt = select(Story.created_at).order_by(Story.created_at.desc()).limit(1)
        res = await session.execute(stmt)
        latest_story = res.scalar()
        print(f"Latest Story Date: {latest_story}")

        # Check latest Item
        stmt = select(Item.ingested_at).order_by(Item.ingested_at.desc()).limit(1)
        res = await session.execute(stmt)
        latest_item = res.scalar()
        print(f"Latest Item Date: {latest_item}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(check_latest_dates())
