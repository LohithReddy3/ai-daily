import feedparser
import asyncio
import ssl

if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime
import hashlib
from ..database import SessionLocal
from ..models import Source, Item, SourceType
import logging

logger = logging.getLogger(__name__)

def parse_feed(url):
    return feedparser.parse(url, agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36")

def generate_hash(title, url):
    return hashlib.md5(f"{title}{url}".encode()).hexdigest()

async def fetch_and_process_feeds():
    async with SessionLocal() as session:
        result = await session.execute(select(Source))
        sources = result.scalars().all()
        
        for source in sources:
            if not source.feed_url:
                continue
                
            logger.info(f"Fetching {source.name} from {source.feed_url}")
            
            # Run blocking feedparser in executor
            loop = asyncio.get_event_loop()
            try:
                feed = await loop.run_in_executor(None, parse_feed, source.feed_url)
            except Exception as e:
                logger.error(f"Error fetching {source.name}: {e}")
                continue
            
            if feed.bozo:
                logger.warning(f"Feed {source.name} bozo exception: {feed.bozo_exception}")

            logger.info(f"Found {len(feed.entries)} entries for {source.name}")
                
            new_items_count = 0
            for entry in feed.entries:
                title = entry.get('title', '')
                link = entry.get('link', '')
                published = entry.get('published_parsed') or entry.get('updated_parsed')
                if published:
                    published_dt = datetime(*published[:6])
                else:
                    published_dt = datetime.utcnow()
                    
                item_hash = generate_hash(title, link)
                
                # Check dedupe
                existing = await session.execute(select(Item).where(Item.hash == item_hash))
                if existing.scalars().first():
                    continue
                
                # Normalize content
                content = ""
                if 'summary' in entry:
                    content = entry.summary
                elif 'content' in entry:
                    content = entry.content[0].value
                
                new_item = Item(
                    source_id=source.id,
                    title=title,
                    url=link,
                    published_at=published_dt,
                    raw_text=content,
                    content_type=source.type,
                    hash=item_hash,
                    metadata_json={"author": entry.get('author', '')}
                )
                session.add(new_item)
                new_items_count += 1
            
            await session.commit()
            logger.info(f"Ingested {new_items_count} items from {source.name}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(fetch_and_process_feeds())
