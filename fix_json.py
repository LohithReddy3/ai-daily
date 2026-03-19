import asyncio
import os
import json
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv(override=True)

async def fix():
    url = os.getenv("DATABASE_URL")
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url and url.startswith("postgresql://") and "asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(url, connect_args={"statement_cache_size": 0})
    async with engine.begin() as conn:
        # Fix ALL supporting_urls that are double-encoded strings
        r = await conn.execute(text("UPDATE story_summaries SET supporting_urls = supporting_urls::text::json WHERE jsonb_typeof(supporting_urls::jsonb) = 'string'"))
        print(f"Fixed supporting_urls: {r.rowcount} rows")
        # Fix ALL summary_bullets that are double-encoded
        r2 = await conn.execute(text("UPDATE story_summaries SET summary_bullets = summary_bullets::text::json WHERE jsonb_typeof(summary_bullets::jsonb) = 'string'"))
        print(f"Fixed summary_bullets: {r2.rowcount} rows")
        # Fix ALL evidence_snippets that are double-encoded
        r3 = await conn.execute(text("UPDATE story_summaries SET evidence_snippets = evidence_snippets::text::json WHERE jsonb_typeof(evidence_snippets::jsonb) = 'string'"))
        print(f"Fixed evidence_snippets: {r3.rowcount} rows")
        # Fix ALL key_entities that are double-encoded
        r4 = await conn.execute(text("UPDATE story_summaries SET key_entities = key_entities::text::json WHERE jsonb_typeof(key_entities::jsonb) = 'string'"))
        print(f"Fixed key_entities: {r4.rowcount} rows")
        # Fix classification_json on stories
        r5 = await conn.execute(text("UPDATE stories SET classification_json = classification_json::text::json WHERE classification_json IS NOT NULL AND jsonb_typeof(classification_json::jsonb) = 'string'"))
        print(f"Fixed classification_json: {r5.rowcount} rows")
        # Fix topic_bias on sources
        r6 = await conn.execute(text("UPDATE sources SET topic_bias = topic_bias::text::json WHERE topic_bias IS NOT NULL AND jsonb_typeof(topic_bias::jsonb) = 'string'"))
        print(f"Fixed topic_bias: {r6.rowcount} rows")
        # Fix items metadata_json 
        r7 = await conn.execute(text("UPDATE items SET metadata_json = metadata_json::text::json WHERE metadata_json IS NOT NULL AND jsonb_typeof(metadata_json::jsonb) = 'string'"))
        print(f"Fixed metadata_json: {r7.rowcount} rows")
    print("All JSON fields fixed!")

asyncio.run(fix())
