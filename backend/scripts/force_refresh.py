import asyncio
from backend.services.brief import job_generate_daily_brief
from backend.services.ingestion import job_ingest_feeds

async def force_run():
    print("Running Ingestion...")
    await job_ingest_feeds()
    print("Running Brief Generation...")
    await job_generate_daily_brief()
    print("Done!")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(force_run())
