import asyncio
from backend.database import SessionLocal
from backend.models import Story, StorySummary, Item
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from datetime import datetime, timedelta

async def test_api():
    async with SessionLocal() as db:
        persona = "builders"
        category = "Models"
        now = datetime.utcnow()
        start_date = now - timedelta(hours=24)

        try:
            # Simplified but equivalent query to the one in routers/stories.py
            stmt = (
                select(Story)
                .outerjoin(StorySummary)
                .outerjoin(Item)
                # Removed date filter for testing if it's too restrictive
                #.where(Story.created_at >= start_date)
            )

            if persona:
                stmt = stmt.where(StorySummary.persona == persona)
            
            if category:
                stmt = stmt.where(StorySummary.category == category)

            stmt = (
                stmt.group_by(Story.id)
                .options(selectinload(Story.items), selectinload(Story.summaries))
                .order_by(func.count(Item.id).desc(), Story.created_at.desc())
                .limit(10)
            )
            
            print("Executing query...")
            result = await db.execute(stmt)
            stories = result.scalars().unique().all()
            print(f"Found {len(stories)} stories")
            for s in stories:
                print(f" - {s.canonical_title} ({len(s.items)} items)")

        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api())
