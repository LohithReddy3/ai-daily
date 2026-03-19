from fastapi import APIRouter, BackgroundTasks, Depends
from backend.services.ingestion import job_ingest_feeds, job_enrich_content
from backend.services.clustering import job_cluster_stories
from backend.services.scoring import job_score_stories
from backend.services.llm import job_run_agents
from backend.services.brief import job_generate_daily_brief

router = APIRouter(
    prefix="/jobs",
    tags=["admin"],
)

@router.post("/ingest")
async def trigger_ingest(background_tasks: BackgroundTasks):
    background_tasks.add_task(job_ingest_feeds)
    return {"status": "triggered", "job": "ingestion"}

@router.post("/enrich")
async def trigger_enrich(background_tasks: BackgroundTasks):
    background_tasks.add_task(job_enrich_content)
    return {"status": "triggered", "job": "enrichment"}

@router.post("/cluster")
async def trigger_cluster(background_tasks: BackgroundTasks):
    background_tasks.add_task(job_cluster_stories)
    return {"status": "triggered", "job": "clustering"}

@router.post("/score")
async def trigger_score(background_tasks: BackgroundTasks):
    background_tasks.add_task(job_score_stories)
    return {"status": "triggered", "job": "scoring"}

@router.post("/agents")
async def trigger_agents():
    # Use synchronous version to avoid async/greenlet conflicts
    import asyncio
    from backend.services.llm_sync import job_run_agents_sync
    
    # Run sync job in thread pool
    await asyncio.to_thread(job_run_agents_sync)
    return {"status": "completed", "job": "agents"}

@router.post("/brief")
async def trigger_brief(background_tasks: BackgroundTasks):
    background_tasks.add_task(job_generate_daily_brief)
    return {"status": "triggered", "job": "daily_brief"}

from backend.scripts.seed_sources import seed
@router.post("/seed")
async def run_seed_sources():
    await seed()
    return {"status": "seeded", "message": "Sources populating..."}
