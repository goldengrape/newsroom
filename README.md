# Jules Daily Tech Intel

This project fetches daily tech news from various RSS sources, filters them based on a specific "Hardcore Engineering" persona, and presents them in a clean, distraction-free web interface.

## Project Structure

- **`fetch_rss.py`**: A Python script to fetch the latest headlines from configured RSS feeds (TechCrunch, Ars Technica, The Verge, etc.).
- **`docs/`**: A static web application (hosted via GitHub Pages) to display the filtered news.
  - **`data/news.json`**: The structured data file containing the selected 25 daily news items.
  - **`index.html`**: The main dashboard.
- **`2026-02-27-daily-tech-intel.md`**: An archive of the daily report in Markdown format.

## How it works

1. **Fetch**: Run `python3 fetch_rss.py` to get the raw news stream.
2. **Filter**: The raw stream is processed (currently by Jules) to select the top 25 items matching the "Systemic Architecture & Engineering" criteria.
3. **Publish**: The selected items are saved to `docs/data/news.json` and rendered on the website.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the fetcher:
   ```bash
   python3 fetch_rss.py
   ```
3. Serve the site locally:
   ```bash
   python3 -m http.server 8000 --directory docs
   ```
