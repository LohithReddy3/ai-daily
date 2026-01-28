from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
from .services.ingestion import fetch_and_process_feeds
from .services.clustering import cluster_items
from .services.llm import summarize_stories
import logging

logger = logging.getLogger(__name__)

async def full_pipeline():
    logger.info("Starting Full Pipeline Run")
    logger.info("Step 1: Ingestion")
    await fetch_and_process_feeds()
    
    logger.info("Step 2: Clustering")
    await cluster_items()
    
    logger.info("Step 3: Summarization")
    await summarize_stories()
    
    logger.info("Pipeline Complete")

def start_scheduler():
    scheduler = AsyncIOScheduler()
    # Schedule daily at 6 AM ET (approx 10 AM UTC)
    # For testing, we run every hour or manual trigger
    scheduler.add_job(full_pipeline, 'cron', hour=10, minute=0) 
    scheduler.start()
    return scheduler

if __name__ == "__main__":
    # Test run
    logging.basicConfig(level=logging.INFO)
    asyncio.run(full_pipeline())
