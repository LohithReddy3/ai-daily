import requests
import feedparser
import time

INITIAL_SOURCES = [
    # Research - arXiv
    {"name": "arXiv cs.AI", "feed_url": "http://export.arxiv.org/rss/cs.AI"},
    {"name": "arXiv cs.CL", "feed_url": "http://export.arxiv.org/rss/cs.CL"},
    {"name": "arXiv cs.LG", "feed_url": "http://export.arxiv.org/rss/cs.LG"},
    {"name": "arXiv cs.CV", "feed_url": "http://export.arxiv.org/rss/cs.CV"},

    # Industry Labs
    {"name": "OpenAI Blog", "feed_url": "https://openai.com/blog/rss.xml"},
    {"name": "Google DeepMind", "feed_url": "https://deepmind.com/blog/feed/basic/"},
    {"name": "Anthropic", "feed_url": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml"},
    {"name": "Microsoft Research", "feed_url": "https://www.microsoft.com/en-us/research/feed/"},

    # Engineering / Builder
    {"name": "Hugging Face Blog", "feed_url": "https://huggingface.co/blog/feed.xml"},
    {"name": "LangChain Blog", "feed_url": "https://blog.langchain.dev/rss/"},
    {"name": "Weights & Biases", "feed_url": "https://wandb.ai/fully-connected/rss.xml"}, 
    {"name": "AWS Machine Learning", "feed_url": "https://aws.amazon.com/blogs/machine-learning/feed/"},

    # Thought Leaders
    {"name": "Lil'Log (Lilian Weng)", "feed_url": "https://lilianweng.github.io/lil-log/feed.xml"},
    {"name": "Andrej Karpathy", "feed_url": "https://karpathy.ai/feed.xml"},
    {"name": "Simon Willison", "feed_url": "https://simonwillison.net/atom/entries/"},
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
}

print(f"{'SOURCE NAME':<25} | {'STATUS':<10} | {'DETAILS'}")
print("-" * 80)

for source in INITIAL_SOURCES:
    try:
        response = requests.get(source['feed_url'], headers=headers, timeout=10)
        status = response.status_code
        
        if status == 200:
            # Try parsing
            feed = feedparser.parse(response.content)
            if feed.bozo and feed.bozo_exception:
                 # Some valid feeds trigger bozo (encoding etc), but if entries > 0 it's usually fine
                 if len(feed.entries) > 0:
                     print(f"{source['name']:<25} | \033[92mONLINE\033[0m   | Found {len(feed.entries)} entries")
                 else:
                     print(f"{source['name']:<25} | \033[93mWARNING\033[0m  | Status 200 but parse error: {feed.bozo_exception}")
            elif len(feed.entries) > 0:
                print(f"{source['name']:<25} | \033[92mONLINE\033[0m   | Found {len(feed.entries)} entries")
            else:
                 print(f"{source['name']:<25} | \033[93mEMPTY\033[0m    | Status 200 but 0 entries found")
        else:
            print(f"{source['name']:<25} | \033[91mFAIL\033[0m     | HTTP {status}")
            
    except Exception as e:
        print(f"{source['name']:<25} | \033[91mERROR\033[0m    | {str(e)}")
