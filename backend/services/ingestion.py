import feedparser
import asyncio
import ssl
import hashlib
import logging
from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from ..database import SessionLocal
from ..models import Source, Item, SourceKind, EnrichmentStatus
import httpx
from readability import Document
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Semaphores
FEED_SEMAPHORE = asyncio.Semaphore(5)
ENRICH_SEMAPHORE = asyncio.Semaphore(3)

# Emulate Browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def generate_hash(title, url):
    return hashlib.sha256(f"{title}{url}".encode()).hexdigest()

def clean_url(url):
    # Basic utm stripping
    if "?" in url:
        base, params = url.split("?", 1)
        # filtered = [p for p in params.split("&") if not p.startswith("utm_")]
        # return f"{base}?{'&'.join(filtered)}" if filtered else base
        # For now just simpler split for known trackers, or keep it simple
        pass
    return url

async def fetch_feed_content(client, url, etag=None, last_modified=None):
    headers = HEADERS.copy()
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified
        
    try:
        response = await client.get(url, headers=headers, timeout=10.0)
        return response
    except Exception as e:
        logger.warning(f"Fetch error {url}: {e}")
        return None

def parse_feed_data(content, url):
    # feedparser handles strings or bytes
    return feedparser.parse(content)

async def process_source(source_id):
    async with FEED_SEMAPHORE:
        async with SessionLocal() as session:
            try:
                result = await session.execute(select(Source).where(Source.id == source_id))
                source = result.scalars().first()
                if not source:
                    logger.warning(f"Source {source_id} not found.")
                    return

                logger.info(f"Fetching {source.name}...")
                
                async with httpx.AsyncClient(verify=False, follow_redirects=True) as client:
                    response = await fetch_feed_content(client, source.feed_url, source.etag, source.last_modified)
                
                if not response:
                    source.fail_count += 1
                    source.last_error = "Network/Timeout error"
                    await session.commit()
                    return
                
                if response.status_code == 304:
                    logger.info(f"{source.name} not modified.")
                    source.last_fetched_at = datetime.utcnow()
                    source.fail_count = 0
                    await session.commit()
                    return

                if response.status_code >= 400:
                    source.fail_count += 1
                    source.last_error = f"HTTP {response.status_code}"
                    await session.commit()
                    return

                # Parse
                feed = feedparser.parse(response.content)
                
                # Update source metadata
                source.etag = response.headers.get("ETag")
                source.last_modified = response.headers.get("Last-Modified")
                source.last_fetched_at = datetime.utcnow()
                source.fail_count = 0
                
                # Collect entries
                entries_to_insert = []
                hashes = []
                
                for entry in feed.entries:
                    title = entry.get('title', '')
                    link = entry.get('link', '')
                    
                    # Normalize
                    if not title or not link:
                        continue
                        
                    canonical_url = clean_url(link)
                    item_hash = generate_hash(title, canonical_url)
                    hashes.append(item_hash)
                    
                    # Extract date
                    published_dt = datetime.utcnow()
                    if 'published_parsed' in entry and entry.published_parsed:
                        published_dt = datetime(*entry.published_parsed[:6])
                    elif 'updated_parsed' in entry and entry.updated_parsed:
                        published_dt = datetime(*entry.updated_parsed[:6])
                    
                    # Content fallback
                    content = ""
                    if 'summary' in entry:
                        content = entry.summary
                    elif 'content' in entry:
                        content = entry.content[0].value
                        
                    entries_to_insert.append({
                        "hash": item_hash,
                        "title": title,
                        "url": link,
                        "canonical_url": canonical_url,
                        "published_at": published_dt,
                        "raw_text": content,
                        "source_id": source.id,
                        "content_length": len(content) if content else 0
                    })
                    
                if not hashes:
                    await session.commit()
                    return

                # Batch Dedupe
                # Since hashes are unique, we check which usage exists
                # In asyncpg/sqlalchemy, filtering by IN list
                # We need to process in chunks if hashes is too large, but usually rss feed is small (<100)
                result = await session.execute(
                    select(Item.hash).where(Item.hash.in_(hashes))
                )
                existing_hashes = {r for r in result.scalars().all()}
                new_count = 0
                added_hashes = set() # Track hashes added in this batch to avoid internal duplicates
                
                for entry in entries_to_insert:
                    if entry["hash"] in existing_hashes or entry["hash"] in added_hashes:
                        continue
                    
                    new_item = Item(
                        source_id=source.id,
                        title=entry["title"],
                        url=entry["url"],
                        canonical_url=entry["canonical_url"],
                        published_at=entry["published_at"],
                        raw_text=entry["raw_text"],
                        hash=entry["hash"],
                        content_length=entry["content_length"],
                        enrichment_status=EnrichmentStatus.none # Default
                    )
                    session.add(new_item)
                    added_hashes.add(entry["hash"])
                    new_count += 1
                    
                logger.info(f"{source.name}: {new_count} new items.")
                try:
                    await session.commit()
                except Exception as e:
                    logger.error(f"Commit failed for source {source.name}: {e}")
                    await session.rollback()
                
            except Exception as e:
                logger.error(f"Error processing source {source_id}: {e}")
                await session.rollback()

async def job_ingest_feeds():
    """JOB A: Ingest Feeds"""
    async with SessionLocal() as session:
        result = await session.execute(select(Source.id).where(Source.is_enabled == True))
        source_ids = result.scalars().all()
        
    # Run tasks concurrently, each manages its own session
    tasks = [process_source(sid) for sid in source_ids]
    await asyncio.gather(*tasks)

async def job_enrich_content():
    """JOB B: Enrichment (Fetch full text)"""
    async with SessionLocal() as session:
        # Select items needing enrichment
        # enrichment_status = none AND (raw_text empty OR short)
        stmt = select(Item).where(
            Item.enrichment_status == EnrichmentStatus.none
        ).limit(50) # Batch size
        
        result = await session.execute(stmt)
        items = result.scalars().all()
        
        if not items:
            return

        async with httpx.AsyncClient(follow_redirects=True, verify=False, timeout=15.0) as client:
            tasks = []
            for item in items:
                tasks.append(enrich_item(client, item))
            
            await asyncio.gather(*tasks)
            
        await session.commit()

async def enrich_item(client, item):
    async with ENRICH_SEMAPHORE:
        item.enrichment_status = EnrichmentStatus.queued
        
        try:
            logger.info(f"Enriching: {item.url}")
            response = await client.get(item.url)
            if response.status_code >= 400:
                item.enrichment_status = EnrichmentStatus.failed
                item.enrichment_error = f"HTTP {response.status_code}"
                return

            item.raw_html = response.text
            
            # Parse with Readability
            doc = Document(response.text)
            item.clean_text = doc.summary() # actually doc.summary() gives HTML. doc.title()
            # We want plain text usually, or clean HTML. doc.summary() is 'clean html'.
            # To get text, we might need bs4 on top.
            # Let's clean the html from summary.
            import bs4
            soup = bs4.BeautifulSoup(doc.summary(), "html.parser")
            text_content = soup.get_text(separator="\n", strip=True)
            
            # Extract image from original raw_html (better chance than readability output)
            clean_image_url = None
            if item.raw_html:
                full_soup = bs4.BeautifulSoup(item.raw_html, "html.parser")
                og_image = full_soup.find("meta", property="og:image")
                if og_image and og_image.get("content"):
                    clean_image_url = og_image["content"]
            
            item.clean_text = text_content
            item.content_length = len(text_content)
            item.image_url = clean_image_url
            item.enrichment_status = EnrichmentStatus.done
            item.enriched_at = datetime.utcnow()
            
        except Exception as e:
            item.enrichment_status = EnrichmentStatus.failed
            item.enrichment_error = str(e)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(job_ingest_feeds())
    asyncio.run(job_enrich_content())
