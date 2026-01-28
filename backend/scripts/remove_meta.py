import asyncio
from sqlalchemy.future import select
from backend.database import SessionLocal
from backend.models import Source

async def remove_meta():
    async with SessionLocal() as session:
        print("Searching for Meta AI source...")
        result = await session.execute(select(Source).where(Source.name.ilike("%Meta AI%")))
        meta = result.scalars().first()
        
        if meta:
            await session.delete(meta)
            await session.commit()
            print(f"✅ Removed source: {meta.name}")
        else:
            print("ℹ️ Meta AI source not found in database.")

if __name__ == "__main__":
    asyncio.run(remove_meta())
