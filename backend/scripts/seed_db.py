import asyncio
from backend.database import engine, Base, SessionLocal
from backend.models import Source, SourceType, TrustLevel
from sqlalchemy.future import select

INITIAL_SOURCES = [
    # Research - arXiv
    {"name": "arXiv cs.AI", "url": "http://arxiv.org/abs/cs.AI", "feed_url": "http://export.arxiv.org/rss/cs.AI", "type": SourceType.paper, "trust_level": TrustLevel.high},
    {"name": "arXiv cs.CL", "url": "http://arxiv.org/abs/cs.CL", "feed_url": "http://export.arxiv.org/rss/cs.CL", "type": SourceType.paper, "trust_level": TrustLevel.high},
    {"name": "arXiv cs.LG", "url": "http://arxiv.org/abs/cs.LG", "feed_url": "http://export.arxiv.org/rss/cs.LG", "type": SourceType.paper, "trust_level": TrustLevel.high},
    {"name": "arXiv cs.CV", "url": "http://arxiv.org/abs/cs.CV", "feed_url": "http://export.arxiv.org/rss/cs.CV", "type": SourceType.paper, "trust_level": TrustLevel.high},

    # Industry Labs
    {"name": "OpenAI Blog", "url": "https://openai.com/blog", "feed_url": "https://openai.com/blog/rss.xml", "type": SourceType.blog, "trust_level": TrustLevel.high},
    {"name": "Google DeepMind", "url": "https://deepmind.google/discover/blog", "feed_url": "https://deepmind.com/blog/feed/basic/", "type": SourceType.blog, "trust_level": TrustLevel.high},
    {"name": "Anthropic", "url": "https://www.anthropic.com/news", "feed_url": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml", "type": SourceType.blog, "trust_level": TrustLevel.high},
    {"name": "Microsoft Research", "url": "https://www.microsoft.com/en-us/research/blog/", "feed_url": "https://www.microsoft.com/en-us/research/feed/", "type": SourceType.blog, "trust_level": TrustLevel.high},

    # Engineering / Builder
    {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog", "feed_url": "https://huggingface.co/blog/feed.xml", "type": SourceType.blog, "trust_level": TrustLevel.medium},
    {"name": "LangChain Blog", "url": "https://blog.langchain.dev/", "feed_url": "https://blog.langchain.dev/rss/", "type": SourceType.blog, "trust_level": TrustLevel.medium},
    {"name": "Weights & Biases", "url": "https://wandb.ai/site/blog", "feed_url": "https://wandb.ai/fully-connected/rss.xml", "type": SourceType.blog, "trust_level": TrustLevel.medium},
    {"name": "AWS Machine Learning", "url": "https://aws.amazon.com/blogs/machine-learning/", "feed_url": "https://aws.amazon.com/blogs/machine-learning/feed/", "type": SourceType.blog, "trust_level": TrustLevel.medium},

    # Thought Leaders
    {"name": "Lil'Log (Lilian Weng)", "url": "https://lilianweng.github.io/lil-log/", "feed_url": "https://lilianweng.github.io/lil-log/feed.xml", "type": SourceType.blog, "trust_level": TrustLevel.high},
    {"name": "Andrej Karpathy", "url": "https://karpathy.ai/", "feed_url": "https://karpathy.ai/feed.xml", "type": SourceType.blog, "trust_level": TrustLevel.high},
    {"name": "Simon Willison", "url": "https://simonwillison.net/", "feed_url": "https://simonwillison.net/atom/entries/", "type": SourceType.blog, "trust_level": TrustLevel.high},
]

async def seed_sources():
    async with SessionLocal() as session:
        # Create tables if not exist (quick hack for script)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        for src_data in INITIAL_SOURCES:
            stmt = select(Source).where(Source.name == src_data["name"])
            result = await session.execute(stmt)
            existing = result.scalars().first()
            
            if not existing:
                print(f"Adding source: {src_data['name']}")
                new_source = Source(**src_data)
                session.add(new_source)
            else:
                print(f"Source exists: {src_data['name']}")
        
        await session.commit()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(seed_sources())
