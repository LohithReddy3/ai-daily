import feedparser
import requests
from datetime import datetime

sources = [
    "https://huggingface.co/blog/feed.xml",
    "https://blog.langchain.dev/rss/",
    "https://aws.amazon.com/blogs/machine-learning/feed/",
    "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml"
]

for url in sources:
    print(f"\nChecking {url}...")
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        if response.status_code != 200:
            print(f"Status: {response.status_code}")
            continue
            
        feed = feedparser.parse(response.content)
        if not feed.entries:
            print("No entries.")
            continue
            
        entry = feed.entries[0]
        published = entry.get('published_parsed') or entry.get('updated_parsed')
        if published:
            dt = datetime(*published[:6])
            print(f" - LATEST: {dt} | {entry.title}")
        else:
            print(f" - LATEST: NO DATE | {entry.title}")
            
    except Exception as e:
        print(f"Error: {e}")
print(f"Fetching {url}...")

response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
print(f"Status: {response.status_code}")

feed = feedparser.parse(response.content)
print(f"Entries: {len(feed.entries)}")

for entry in feed.entries[:5]:
    published = entry.get('published_parsed') or entry.get('updated_parsed')
    if published:
        dt = datetime(*published[:6])
        print(f" - {dt} | {entry.title}")
    else:
        print(f" - NO DATE | {entry.title}")

print("\nChecking Google AI...")
url = "https://blog.google/innovation-and-ai/technology/ai/rss/"
response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
feed = feedparser.parse(response.content)
for entry in feed.entries[:5]:
    published = entry.get('published_parsed') or entry.get('updated_parsed')
    if published:
        dt = datetime(*published[:6])
        print(f" - {dt} | {entry.title}")
