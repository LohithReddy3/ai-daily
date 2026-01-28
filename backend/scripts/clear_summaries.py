import asyncio
from backend.database import SessionLocal
from backend.models import StorySummary
from sqlalchemy import delete

async def clear_summaries():
    async with SessionLocal() as session:
        await session.execute(delete(StorySummary))
        await session.commit()
        print("Successfully cleared all story summaries.")

if __name__ == "__main__":
    asyncio.run(clear_summaries())
