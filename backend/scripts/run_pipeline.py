import asyncio
import sys
import os

# Ensure backend module is found
sys.path.append(os.getcwd())

from backend.services.clustering import job_cluster_stories
from backend.services.scoring import job_score_stories
from backend.services.llm import job_run_agents
import logging

logging.basicConfig(level=logging.INFO)

async def main():
    print("Running clustering...")
    await job_cluster_stories()
    print("Running scoring...")
    await job_score_stories()
    print("Running agents...")
    await job_run_agents()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
