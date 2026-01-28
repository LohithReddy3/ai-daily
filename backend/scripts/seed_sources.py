import asyncio
from backend.database import SessionLocal
from backend.models import Source, SourceType, TrustLevel
from sqlalchemy.future import select

async def seed():
    sources = [
        Source(name="arXiv AI", type=SourceType.paper, feed_url="http://export.arxiv.org/rss/cs.AI", trust_level=TrustLevel.high),
        Source(name="arXiv LG", type=SourceType.paper, feed_url="http://export.arxiv.org/rss/cs.LG", trust_level=TrustLevel.high),
        Source(name="arXiv CL", type=SourceType.paper, feed_url="http://export.arxiv.org/rss/cs.CL", trust_level=TrustLevel.high),
        Source(name="arXiv CV", type=SourceType.paper, feed_url="http://export.arxiv.org/rss/cs.CV", trust_level=TrustLevel.high),
        Source(name="OpenAI Blog", type=SourceType.blog, feed_url="https://openai.com/blog/rss.xml", trust_level=TrustLevel.high),
        Source(name="Hugging Face Blog", type=SourceType.blog, feed_url="https://huggingface.co/blog/feed.xml", trust_level=TrustLevel.high),
        Source(name="Google AI Blog", type=SourceType.blog, feed_url="https://blog.google/technology/ai/rss", trust_level=TrustLevel.high),
        Source(name="DeepMind Blog", type=SourceType.blog, feed_url="https://deepmind.com/blog/feed/basic/", trust_level=TrustLevel.high),
        Source(name="Anthropic Blog", type=SourceType.blog, feed_url="https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml", trust_level=TrustLevel.high),
        Source(name="AI2 Blog", type=SourceType.blog, feed_url="https://blog.allenai.org/feed", trust_level=TrustLevel.high),
        Source(name="MIT AI News", type=SourceType.news, feed_url="https://news.mit.edu/topic/artificial-intelligence-rss.xml", trust_level=TrustLevel.high),
        Source(name="Stanford HAI", type=SourceType.blog, feed_url="https://hai.stanford.edu/news/rss.xml", trust_level=TrustLevel.high),
        Source(name="Weights & Biases", type=SourceType.blog, feed_url="https://wandb.ai/fully-connected/rss.xml", trust_level=TrustLevel.medium),
        Source(name="LangChain Blog", type=SourceType.blog, feed_url="https://blog.langchain.dev/rss/", trust_level=TrustLevel.medium),
        Source(name="AWS Machine Learning", type=SourceType.blog, feed_url="https://aws.amazon.com/blogs/machine-learning/feed/", trust_level=TrustLevel.medium),
        
        # Thought Leaders (High Signal)
        Source(name="Lil'Log (Lilian Weng)", type=SourceType.blog, feed_url="https://lilianweng.github.io/lil-log/feed.xml", trust_level=TrustLevel.high),
        Source(name="Andrej Karpathy", type=SourceType.blog, feed_url="https://karpathy.ai/feed.xml", trust_level=TrustLevel.high),
        Source(name="Simon Willison", type=SourceType.blog, feed_url="https://simonwillison.net/atom/entries/", trust_level=TrustLevel.high),
    ]
    
    async with SessionLocal() as session:
        for s in sources:
            # Upsert logic (simplified)
            existing = await session.execute(select(Source).where(Source.name == s.name))
            if not existing.scalars().first():
                session.add(s)
        await session.commit()
    print("Sources seeded.")

if __name__ == "__main__":
    asyncio.run(seed())
