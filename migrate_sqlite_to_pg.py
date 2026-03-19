"""
Migrate all data from local SQLite (ai_daily.db) to Supabase PostgreSQL.
Uses raw SQL reads from SQLite and ORM-aware inserts to Postgres,
with proper type coercion for dates, booleans, and JSON fields.
"""
import asyncio
import os
from datetime import datetime
from dateutil import parser as dateparser
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from dotenv import load_dotenv

import backend.models as models

load_dotenv(override=True)

# --- Engines ---
SQLITE_URL = "sqlite+aiosqlite:////tmp/ai_daily.db"
sqlite_engine = create_async_engine(SQLITE_URL, connect_args={"check_same_thread": False})

PG_URL = os.getenv("DATABASE_URL")
if PG_URL and PG_URL.startswith("postgres://"):
    PG_URL = PG_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif PG_URL and PG_URL.startswith("postgresql://") and "asyncpg" not in PG_URL:
    PG_URL = PG_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

pg_engine = create_async_engine(PG_URL, connect_args={"statement_cache_size": 0})
PgSession = sessionmaker(autocommit=False, autoflush=False, bind=pg_engine, class_=AsyncSession)

# --- Columns that hold DateTime values per table ---
DATETIME_COLS = {
    "sources": ["last_fetched_at"],
    "items": ["published_at", "ingested_at", "enriched_at"],
    "stories": ["created_at", "updated_at", "classified_at", "last_scored_at"],
    "story_items": ["added_at"],
    "story_summaries": ["last_reviewed_at"],
    "daily_briefs": ["generated_at"],
    "users": ["created_at"],
    "user_saves": ["saved_at"],
}

BOOL_COLS = {
    "sources": ["is_enabled"],
    "items": [],
    "stories": ["is_active"],
    "story_items": ["is_primary"],
    "story_summaries": ["insufficient_evidence"],
    "daily_briefs": [],
    "users": [],
    "user_saves": [],
}

def coerce_row(row_dict, table_name):
    """Convert string dates to datetime objects and int bools to proper bools."""
    dt_cols = DATETIME_COLS.get(table_name, [])
    bool_cols = BOOL_COLS.get(table_name, [])
    
    for col in dt_cols:
        val = row_dict.get(col)
        if val is not None and isinstance(val, str):
            try:
                row_dict[col] = dateparser.parse(val)
            except Exception:
                row_dict[col] = None
    
    for col in bool_cols:
        val = row_dict.get(col)
        if val is not None:
            row_dict[col] = bool(val)
    
    return row_dict


async def migrate_table(table_name, model_class):
    """Read all rows from SQLite table and insert into Postgres."""
    print(f"\n--- Migrating: {table_name} ---")
    
    # 1. Read from SQLite
    async with sqlite_engine.connect() as sqlite_conn:
        result = await sqlite_conn.execute(text(f"SELECT * FROM {table_name}"))
        columns = list(result.keys())
        raw_rows = result.fetchall()
    
    print(f"  Read {len(raw_rows)} rows from SQLite.")
    if not raw_rows:
        return
    
    # 2. Convert to list of dicts with proper types
    rows = []
    for raw in raw_rows:
        row_dict = dict(zip(columns, raw))
        rows.append(coerce_row(row_dict, table_name))
    
    # 3. Insert into Postgres in batches
    batch_size = 200
    inserted = 0
    skipped = 0
    
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        async with PgSession() as pg_session:
            try:
                stmt = insert(model_class).values(batch).on_conflict_do_nothing()
                await pg_session.execute(stmt)
                await pg_session.commit()
                inserted += len(batch)
                print(f"  Batch {i//batch_size + 1}: inserted {len(batch)} rows (total: {inserted})")
            except Exception as batch_err:
                await pg_session.rollback()
                print(f"  Batch {i//batch_size + 1} failed: {str(batch_err)[:120]}")
                # Fallback: insert one by one
                for row in batch:
                    async with PgSession() as pg_single:
                        try:
                            stmt = insert(model_class).values([row]).on_conflict_do_nothing()
                            await pg_single.execute(stmt)
                            await pg_single.commit()
                            inserted += 1
                        except Exception:
                            await pg_single.rollback()
                            skipped += 1
    
    print(f"  Done! Inserted: {inserted}, Skipped: {skipped}")


async def run_migration():
    print("=" * 60)
    print("MIGRATION: SQLite -> Supabase PostgreSQL")
    print("=" * 60)
    
    # Ensure all tables exist in PG
    print("\nEnsuring tables exist in Supabase...")
    async with pg_engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
        
        # Add any columns that create_all skips on existing tables
        alter_statements = [
            "ALTER TABLE items ADD COLUMN IF NOT EXISTS image_url VARCHAR",
            "ALTER TABLE stories ADD COLUMN IF NOT EXISTS embedding JSON",
            "ALTER TABLE stories ADD COLUMN IF NOT EXISTS generated_image_url VARCHAR",
            "ALTER TABLE stories ADD COLUMN IF NOT EXISTS universe_x FLOAT",
            "ALTER TABLE stories ADD COLUMN IF NOT EXISTS universe_y FLOAT",
            "ALTER TABLE stories ADD COLUMN IF NOT EXISTS universe_cluster INTEGER",
        ]
        for stmt in alter_statements:
            try:
                await conn.execute(text(stmt))
            except Exception:
                pass
                
    print("Tables verified.\n")
    
    # Migrate in FK-safe order
    migration_order = [
        ("sources", models.Source),
        ("items", models.Item),
        ("stories", models.Story),
        ("story_items", models.StoryItem),
        ("story_summaries", models.StorySummary),
        ("daily_briefs", models.DailyBrief),
        ("users", models.User),
        ("user_saves", models.UserSave),
    ]
    
    for table_name, model_class in migration_order:
        await migrate_table(table_name, model_class)
    
    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_migration())
