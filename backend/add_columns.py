import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

load_dotenv(override=True)

async def check_and_add_columns():
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("No DATABASE_URL found.")
        return

    # Fix for asyncpg
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgresql://") and "asyncpg" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

    print(f"Connecting to {DATABASE_URL.split('@')[-1]}")
    engine = create_async_engine(DATABASE_URL)

    async with engine.begin() as conn:
        print("Checking and adding columns to stories table...")
        
        # We can't use IF NOT EXISTS for ADD COLUMN in older postgres, but since Supabase is modern PG it works
        columns_to_add = [
            "embedding JSON",
            "generated_image_url VARCHAR",
            "universe_x FLOAT",
            "universe_y FLOAT",
            "universe_cluster INTEGER"
        ]
        
        for col in columns_to_add:
            try:
                await conn.execute(text(f"ALTER TABLE stories ADD COLUMN IF NOT EXISTS {col};"))
                print(f"Added/verified column: {col}")
            except Exception as e:
                print(f"Failed to add {col}: {e}")
                
        print("Done!")

if __name__ == "__main__":
    asyncio.run(check_and_add_columns())
