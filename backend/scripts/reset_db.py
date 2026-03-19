import asyncio
from backend.database import engine, Base
from backend.models import *  # Import all models to ensure they are registered in Base.metadata

async def reset_database():
    print("Resetting database...")
    async with engine.begin() as conn:
        print("Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
    print("Database reset complete.")

if __name__ == "__main__":
    asyncio.run(reset_database())
