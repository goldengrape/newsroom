import feedparser
import json
import datetime
import os
import time

# RSS Feed Lists
RSS_FEEDS = {
    # 1. Core Tech News
    "TechCrunch": "https://techcrunch.com/feed/",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "Wired": "https://www.wired.com/feed/rss",
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
    "Engadget": "https://www.engadget.com/rss.xml",
    "CNET": "https://www.cnet.com/rss/news/",
    "VentureBeat": "https://venturebeat.com/feed/",

    # 2. Science & Frontier Research
    "ScienceAlert": "https://www.sciencealert.com/feed",
    "MIT Tech Review": "https://www.technologyreview.com/feed/",
    "IEEE Spectrum": "https://spectrum.ieee.org/rss/fulltext",
    "Scientific American": "https://www.scientificamerican.com/section/news/rss/",
    "Nature News": "https://www.nature.com/nature.rss",

    # 3. Business & Internet Trends
    "The Next Web (TNW)": "https://thenextweb.com/feed",
    "Mashable": "https://mashable.com/feed",
    "Fast Company": "https://www.fastcompany.com/latest/rss",
    "Business Insider": "https://www.businessinsider.com/rss"
}

def fetch_rss_feeds():
    """Fetches news from defined RSS feeds."""
    all_news = []

    print(f"Starting RSS fetch for {len(RSS_FEEDS)} sources...")

    # Set a custom User-Agent to avoid being blocked
    headers = {'User-Agent': 'DailyNewsBot/1.0'}

    for source_name, feed_url in RSS_FEEDS.items():
        print(f"Fetching {source_name}...")
        try:
            # feedparser.parse accepts a URL or a string.
            # To set headers, we can't just pass the URL string directly if we want to be polite.
            # However, feedparser's documentation says it uses the 'agent' parameter for User-Agent.
            # Let's use that.
            feed = feedparser.parse(feed_url, agent='DailyNewsBot/1.0')

            if feed.bozo:
                print(f"  Warning: Possible issue parsing {source_name}: {feed.bozo_exception}")

            entries = feed.entries
            print(f"  Found {len(entries)} entries.")

            for entry in entries:
                # Extract relevant fields
                news_item = {
                    "source": source_name,
                    "title": entry.get("title", "No Title"),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", ""),
                    "published": entry.get("published", entry.get("updated", "")),
                    "fetched_at": datetime.datetime.now().isoformat()
                }
                all_news.append(news_item)

        except Exception as e:
            print(f"  Error fetching {source_name}: {e}")

    return all_news

def save_news_to_json(news_data, filename="raw_news.json"):
    """Saves the fetched news data to a JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(news_data, f, indent=4, ensure_ascii=False)
    print(f"Saved {len(news_data)} news items to {filename}")

if __name__ == "__main__":
    news_data = fetch_rss_feeds()
    save_news_to_json(news_data)
