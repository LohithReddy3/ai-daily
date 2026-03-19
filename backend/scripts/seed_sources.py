import asyncio
from backend.database import SessionLocal
from backend.models import Source, SourceKind
from sqlalchemy.future import select

async def seed():
    # Mapping old TrustLevel concepts to new reputation_weight
    # High -> 1.5, Medium -> 1.0
    
    sources = [
        # Source(name="arXiv AI", source_kind=SourceKind.rss, feed_url="http://export.arxiv.org/rss/cs.AI", reputation_weight=1.5),
        # Source(name="arXiv LG", source_kind=SourceKind.rss, feed_url="http://export.arxiv.org/rss/cs.LG", reputation_weight=1.5),
        # Source(name="arXiv CL", source_kind=SourceKind.rss, feed_url="http://export.arxiv.org/rss/cs.CL", reputation_weight=1.5),
        # Source(name="arXiv CV", source_kind=SourceKind.rss, feed_url="http://export.arxiv.org/rss/cs.CV", reputation_weight=1.5),
        Source(name="OpenAI Blog", source_kind=SourceKind.blog, feed_url="https://openai.com/news/rss.xml", reputation_weight=2.0),
        Source(name="Hugging Face Blog", source_kind=SourceKind.blog, feed_url="https://huggingface.co/blog/feed.xml", reputation_weight=1.8),
        Source(name="Google AI Blog", source_kind=SourceKind.blog, feed_url="https://blog.google/technology/ai/rss", reputation_weight=1.8),
        Source(name="DeepMind Blog", source_kind=SourceKind.blog, feed_url="https://deepmind.google/blog/rss.xml", reputation_weight=2.0),
        Source(name="Anthropic Blog", source_kind=SourceKind.blog, feed_url="https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml", reputation_weight=2.0),
        Source(name="AI2 Blog", source_kind=SourceKind.blog, feed_url="https://blog.allenai.org/feed", reputation_weight=1.5),
        Source(name="MIT AI News", source_kind=SourceKind.rss, feed_url="https://news.mit.edu/topic/artificial-intelligence-rss.xml", reputation_weight=1.5),
        Source(name="Stanford HAI", source_kind=SourceKind.blog, feed_url="https://hai.stanford.edu/news/rss.xml", reputation_weight=1.5),
        Source(name="Weights & Biases", source_kind=SourceKind.blog, feed_url="https://wandb.ai/fully-connected/rss.xml", reputation_weight=1.0),
        Source(name="LangChain Blog", source_kind=SourceKind.blog, feed_url="https://blog.langchain.dev/rss/", reputation_weight=1.2),
        Source(name="AWS Machine Learning", source_kind=SourceKind.blog, feed_url="https://aws.amazon.com/blogs/machine-learning/feed/", reputation_weight=1.0),
        
        # Thought Leaders (High Signal)
        Source(name="Lil'Log (Lilian Weng)", source_kind=SourceKind.blog, feed_url="https://lilianweng.github.io/lil-log/feed.xml", reputation_weight=2.0),
        Source(name="Andrej Karpathy", source_kind=SourceKind.blog, feed_url="https://karpathy.ai/feed.xml", reputation_weight=2.0),
        Source(name="Simon Willison", source_kind=SourceKind.blog, feed_url="https://simonwillison.net/atom/entries/", reputation_weight=1.5),
    ]
    
    async with SessionLocal() as session:
        for s in sources:
            # Upsert logic (simplified check by name)
            existing = await session.execute(select(Source).where(Source.name == s.name))
            if not existing.scalars().first():
                session.add(s)
        await session.commit()
    print("Sources seeded.")

if __name__ == "__main__":
    asyncio.run(seed())
