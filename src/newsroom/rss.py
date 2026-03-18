import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

import feedparser

from newsroom.paths import DATA_DIR


RSS_FEEDS = {
    "TechCrunch": "https://techcrunch.com/feed/",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "Wired": "https://www.wired.com/feed/rss",
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
    "Engadget": "https://www.engadget.com/rss.xml",
    "CNET": "https://www.cnet.com/rss/news/",
    "VentureBeat": "https://venturebeat.com/feed/",
    "ScienceAlert": "https://www.sciencealert.com/feed",
    "MIT Tech Review": "https://www.technologyreview.com/feed/",
    "IEEE Spectrum": "https://spectrum.ieee.org/rss/fulltext",
    "Scientific American": "https://www.scientificamerican.com/section/news/rss/",
    "Nature News": "https://www.nature.com/nature.rss",
    "The Next Web (TNW)": "https://thenextweb.com/feed",
    "Mashable": "https://mashable.com/feed",
    "Fast Company": "https://www.fastcompany.com/latest/rss",
    "Business Insider": "https://www.businessinsider.com/rss",
    "The New England Journal of Medicine (NEJM)": "https://www.nejm.org/action/showFeed?type=etoc&feed=rss&jc=nejm",
    "The Lancet": "https://www.thelancet.com/rssfeed/lancet_current.xml",
    "The BMJ (Recent)": "https://www.bmj.com/rss/recent.xml",
    "British Journal of Ophthalmology": "https://bjo.bmj.com/rss/current.xml",
    "BMJ Open Ophthalmology": "https://bmjophth.bmj.com/rss/current.xml",
}


def load_seen_links(file_path: Path) -> set[str]:
    """Load previously seen links from a JSON file."""
    if not file_path.exists():
        return set()
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return set(data)
        return set()
    except Exception as e:
        print(f"Warning: Could not load seen links from {file_path}: {e}")
        return set()


def save_seen_links(seen_links: set[str], file_path: Path) -> None:
    """Save seen links to a JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        file_path.write_text(
            json.dumps(list(seen_links), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as e:
        print(f"Warning: Could not save seen links to {file_path}: {e}")


def fetch_rss_feeds(
    feeds: dict[str, str] | None = None, seen_links_file: Path | None = None
) -> list[dict[str, Any]]:
    """Fetch news items from the configured RSS feeds."""
    configured_feeds = feeds or RSS_FEEDS
    all_news: list[dict[str, Any]] = []

    seen_links: set[str] = set()
    if seen_links_file:
        seen_links = load_seen_links(seen_links_file)

    new_links: set[str] = set()

    print(f"Starting RSS fetch for {len(configured_feeds)} sources...")
    for source_name, feed_url in configured_feeds.items():
        print(f"Fetching {source_name}...")
        try:
            feed = feedparser.parse(feed_url, agent="DailyNewsBot/1.0")
            if feed.bozo:
                print(
                    f"  Warning: Possible issue parsing {source_name}: {feed.bozo_exception}"
                )

            print(f"  Found {len(feed.entries)} entries.")
            new_entries_count = 0
            for entry in feed.entries:
                link = entry.get("link", "")
                if not link:
                    continue

                if link in seen_links:
                    continue

                new_entries_count += 1
                new_links.add(link)
                all_news.append(
                    {
                        "source": source_name,
                        "title": entry.get("title", "No Title"),
                        "link": link,
                        "summary": entry.get("summary", ""),
                        "published": entry.get("published", entry.get("updated", "")),
                        "fetched_at": dt.datetime.now().isoformat(),
                    }
                )
            print(f"  Added {new_entries_count} new entries.")
        except Exception as error:
            print(f"  Error fetching {source_name}: {error}")

    if seen_links_file and new_links:
        seen_links.update(new_links)
        save_seen_links(seen_links, seen_links_file)

    return all_news


def save_news_to_json(news_data: list[dict[str, Any]], filename: str | Path) -> None:
    """Persist RSS results to a JSON file."""
    output_path = Path(filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(news_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Saved {len(news_data)} news items to {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch RSS news into a JSON file.")
    parser.add_argument(
        "--output",
        default=str(DATA_DIR / "raw_news.json"),
        help="Output path for the raw RSS payload.",
    )
    parser.add_argument(
        "--seen-links",
        default=str(DATA_DIR / "seen_links.json"),
        help="Path to the JSON file tracking seen links.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    news_data = fetch_rss_feeds(seen_links_file=Path(args.seen_links))
    save_news_to_json(news_data, args.output)


if __name__ == "__main__":
    main()
