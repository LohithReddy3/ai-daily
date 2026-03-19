import asyncio
from backend.database import SessionLocal
from backend.models import Story, StorySummary
from sqlalchemy.future import select

async def debug_stories():
    async with SessionLocal() as db:
        stmt = select(Story).join(StorySummary).where(StorySummary.persona == 'builders')
        res = await db.execute(stmt)
        all_stories = res.scalars().unique().all()
        print(f"Total stories with builders summary: {len(all_stories)}")
        if len(all_stories) > 0:
            print(f"Latest created_at with summary: {all_stories[0].created_at}")

        from datetime import datetime, timedelta
        now = datetime.utcnow()
        start_date = now - timedelta(hours=72)
        stmt2 = select(Story).join(StorySummary).where(StorySummary.persona == 'builders').where(Story.created_at >= start_date)
        res2 = await db.execute(stmt2)
        recent_stories = res2.scalars().unique().all()
        print(f"Recent stories (last 72h): {len(recent_stories)}")
        
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(debug_stories())
