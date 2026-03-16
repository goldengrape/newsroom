# Module Reference

## `newsroom.rss`

- Responsibility: fetch RSS feeds and persist a raw JSON snapshot.
- Main entrypoint: `newsroom-fetch`
- Core functions:
  - `fetch_rss_feeds`
  - `save_news_to_json`

## `newsroom.filtering`

- Responsibility: run Gemini-based title screening, ranking, translation, and cost tracking.
- Main entrypoint: `newsroom-filter`
- Key outputs:
  - `docs/data/news.json`
  - `docs/data/news_stats.json`

## `newsroom.feedback_learning`

- Responsibility: learn a candidate next version of the plain-text filter profile from exported feedback JSON.
- Main entrypoint: `newsroom-learn-filter`
- Key outputs:
  - `data/FILTER_PROFILE.updated.md`
  - `data/FILTER_PROFILE.learning_report.md`

## `newsroom.gemini_smoke`

- Responsibility: minimal API connectivity check for Gemini configuration.
- Main entrypoint: `newsroom-gemini-smoke`

## `newsroom.paths`

- Responsibility: shared project-root path definitions used by CLI defaults and scripts.
