from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Default to sqlite for local dev if no env var, but plan for Postgres
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")

# Handle Postgres dialect for asyncpg if needed later, but using synchronous psycopg2/standard for MVP simplicity with threads 
# or use async engine. The plan mentioned asyncpg. Let's start with standard synchronous for simplicity 
# unless specifically requested otherwise, OR stay consistent with requirements.txt which has asyncpg.
# If using asyncpg, we need AsyncEngine. 
# For MVP speed, let's stick to standard synchronous SQLAlchemy + threads for the web app unless we need high concurrency.
# Actually, FastApi is async. Let's use AsyncEngine to be modern.

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Fix for postgres url scheme if needed
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL and DATABASE_URL.startswith("postgresql://") and "asyncpg" not in DATABASE_URL:
     DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Fallback for local testing without docker
if "sqlite" in DATABASE_URL:
     engine = create_async_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # Production (Postgres via Supabase/PgBouncer)
    # We must disable statement caching for PgBouncer transaction pooling
    engine = create_async_engine(
        DATABASE_URL, 
        echo=True,
        connect_args={
            "statement_cache_size": 0
        }
    )

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session
