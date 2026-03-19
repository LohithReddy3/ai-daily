from backend.database import SessionLocal
from backend.models import Item
from sqlalchemy import select, func
from datetime import datetime, timedelta
import asyncio

async def count_items():
    async with SessionLocal() as session:
        # Check total
        total = await session.execute(select(func.count(Item.id)))
        total_count = total.scalar()
        print(f"Total Items in DB: {total_count}")

        # Check last 48h
        cutoff_48h = datetime.utcnow() - timedelta(hours=48)
        recent_48h = await session.execute(select(func.count(Item.id)).where(Item.ingested_at >= cutoff_48h))
        count_48h = recent_48h.scalar()
        print(f"Items in last 48h: {count_48h}")

        # Check last 7 days
        cutoff_7d = datetime.utcnow() - timedelta(days=7)
        recent_7d = await session.execute(select(func.count(Item.id)).where(Item.ingested_at >= cutoff_7d))
        count_7d = recent_7d.scalar()
        print(f"Items in last 7 days: {count_7d}")

if __name__ == "__main__":
    asyncio.run(count_items())
