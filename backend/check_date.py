import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

load_dotenv(override=True)

async def check_date():
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL and DATABASE_URL.startswith("postgresql://") and "asyncpg" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(DATABASE_URL, connect_args={"statement_cache_size": 0})
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT max(created_at) FROM stories;"))
        max_date = result.scalar()
        print(f"Max created_at in DB: {max_date}")

if __name__ == "__main__":
    asyncio.run(check_date())
