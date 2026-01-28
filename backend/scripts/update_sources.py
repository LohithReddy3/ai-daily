import asyncio
from sqlalchemy.future import select
from backend.database import SessionLocal
from backend.models import Source

async def update_sources():
    async with SessionLocal() as session:
        # 1. Update Google DeepMind
        print("Updating Google DeepMind...")
        result = await session.execute(select(Source).where(Source.name.ilike("%DeepMind%")))
        deepmind = result.scalars().first()
        if deepmind:
            deepmind.feed_url = "https://deepmind.com/blog/feed/basic/"
            print(f"  -> Updated DeepMind to {deepmind.feed_url}")
        else:
            print("  -> DeepMind not found.")

        # 2. Update Anthropic
        print("Updating Anthropic...")
        result = await session.execute(select(Source).where(Source.name.ilike("%Anthropic%")))
        anthropic = result.scalars().first()
        if anthropic:
            anthropic.feed_url = "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml"
            print(f"  -> Updated Anthropic to {anthropic.feed_url}")
        else:
            print("  -> Anthropic not found.")

        # 3. Update Meta AI
        print("Updating Meta AI...")
        result = await session.execute(select(Source).where(Source.name.ilike("%Meta AI%")))
        meta = result.scalars().first()
        if meta:
            meta.feed_url = "https://rsshub.app/meta/ai/blog"
            print(f"  -> Updated Meta AI to {meta.feed_url}")
        else:
            print("  -> Meta AI not found.")

        # 4. Update Weights & Biases
        print("Updating Weights & Biases...")
        result = await session.execute(select(Source).where(Source.name.ilike("%Weights & Biases%")))
        wandb = result.scalars().first()
        if wandb:
            wandb.feed_url = "https://wandb.ai/fully-connected/rss.xml"
            print(f"  -> Updated WandB to {wandb.feed_url}")
        else:
            print("  -> Weights & Biases not found.")

        # 5. Remove The Batch
        print("Removing The Batch...")
        result = await session.execute(select(Source).where(Source.name.ilike("%The Batch%")))
        batch = result.scalars().first()
        if batch:
            await session.delete(batch)
            print("  -> Deleted The Batch")
        else:
            print("  -> The Batch not found.")

        await session.commit()
        print("\nAll updates committed.")

if __name__ == "__main__":
    asyncio.run(update_sources())
