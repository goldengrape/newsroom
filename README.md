# Jules Daily Tech Intel

This project fetches daily tech news from a curated RSS list, filters it with Gemini Flash Lite against the plain-text rules in `FILTER_PROFILE.md`, and publishes the selected morning brief to the static site in `docs/`.

## Project Structure

- `fetch_rss.py`: Fetches the raw RSS stream from the configured sources.
- `filter_news.py`: Uses `gemini-flash-lite-latest` to do title screening, final ranking, Chinese summaries, timing, token, and cost stats.
- `docs/data/news.json`: The generated morning brief consumed by the site.
- `docs/data/news_stats.json`: Runtime, batch timing, token, and cost statistics for each run.
- `.github/workflows/daily-news.yml`: GitHub Actions workflow that runs the pipeline automatically.

## How It Works

1. Run `python fetch_rss.py` to collect the raw feed into `raw_news.json`.
2. Run `python filter_news.py` to apply the plain-text filter profile.
3. The filter script first sends only titles in batches, then sends the shortlisted candidates to Gemini for final ranking and Chinese summaries.
4. The selected items are written to `docs/data/news.json`, and run stats are written to `docs/data/news_stats.json`.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Add your Gemini API key.
   Local development can use either an environment variable or a local `.env` file:
   ```dotenv
   GEMINI_API_KEY=your_api_key
   ```
3. Fetch the raw RSS feed:
   ```bash
   python fetch_rss.py
   ```
4. Run the AI filter:
   ```bash
   python filter_news.py --input raw_news.json --output docs/data/news.json --batch-size 50
   ```
5. Serve the site locally if needed:
   ```bash
   python -m http.server 8000 --directory docs
   ```

## Gemini Integration

- Provider: Google Gemini API via the `google-genai` Python SDK.
- Default model: `gemini-flash-lite-latest`.
- The filter profile is read directly from `FILTER_PROFILE.md`.
- First pass is title-only to keep latency and token usage down.
- Second pass ranks the shortlisted candidates and generates concise Chinese summaries.
- Timing, prompt tokens, completion tokens, and estimated cost are saved per batch.
- Cost calculation currently uses:
  - input: `$0.10 / 1M tokens`
  - output: `$0.40 / 1M tokens`

## GitHub Automation

- Workflow file: [`.github/workflows/daily-news.yml`](/Users/golde/code/newsroom/.github/workflows/daily-news.yml)
- Pages deploy workflow: [`.github/workflows/deploy-pages.yml`](/Users/golde/code/newsroom/.github/workflows/deploy-pages.yml)
- Trigger modes:
  - manual: `workflow_dispatch`
  - scheduled: every day at `7:00 AM` America/Los_Angeles
- Because GitHub cron uses UTC only, the workflow schedules both `14:00 UTC` and `15:00 UTC`, then keeps only the run whose Pacific local time is `07`.
- Before enabling it on GitHub, add the repository secret:
  - `GEMINI_API_KEY`
- GitHub Pages is deployed from the `docs/` directory through GitHub Actions, so you do not need the legacy "main /docs" Pages source mode.
- The workflow will:
  1. install dependencies
  2. run unit tests
  3. fetch RSS news
  4. run Gemini filtering
  5. commit updated `docs/data/news.json` and `docs/data/news_stats.json` back to `main`
  6. trigger the Pages deployment workflow on the resulting push to `main`
