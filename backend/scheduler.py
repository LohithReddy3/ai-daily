from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import logging

from backend.services.ingestion import job_ingest_feeds, job_enrich_content
from backend.services.clustering import job_cluster_stories
from backend.services.scoring import job_score_stories
from backend.services.llm import job_run_agents
from backend.services.brief import job_generate_daily_brief

logger = logging.getLogger(__name__)

def start_scheduler():
    scheduler = AsyncIOScheduler()
    
    # JOB: Full Pipeline (Every 8 hours as requested)
    # Running sequentially ensures data integrity (Ingest -> Cluster -> Score -> Agent)
    scheduler.add_job(
        full_pipeline,
        IntervalTrigger(hours=8),
        id="full_pipeline",
        replace_existing=True,
        coalesce=True,               # If Mac/Server sleeps for hours, only run ONCE on wakeup
        misfire_grace_time=3600      # Give it up to an hour to catch up after waking up
    )
    
    # Keep Pulse Check (Every 15 min check for VERY fresh content just ingestion)
    scheduler.add_job(
        job_ingest_feeds,
        IntervalTrigger(minutes=15),
        id="quick_ingest",
        replace_existing=True,
        coalesce=True,
        misfire_grace_time=900
    )

    scheduler.start()
    logger.info("Scheduler started with V2 pipeline jobs.")
    return scheduler

# For manual triggering via API
async def full_pipeline():
    logger.info("Running full pipeline manually...")
    await job_ingest_feeds()
    await job_enrich_content()
    await job_cluster_stories()
    await job_score_stories()
    await job_run_agents()
    await job_generate_daily_brief()
    logger.info("Full pipeline complete.")
