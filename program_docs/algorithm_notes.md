# Algorithm Notes

## Daily Filtering Pipeline

### Stage 1: RSS Aggregation

- Pull from a curated set of technology, science, and medical feeds.
- Normalize entries into a common JSON structure with source, title, link, summary, and timestamps.

### Stage 2: Title Screening

- Send titles in batches to Gemini.
- Apply the plain-text filter profile as the decision policy.
- Keep only candidates that score high enough to survive the first pass.

### Stage 3: Final Ranking

- Send the retained candidate pool to Gemini for final prioritization.
- Ask for compact, mechanism-focused reasoning and ranking metadata.

### Stage 4: Translation

- Run a final translation pass on the selected set.
- Produce Chinese titles and Chinese summaries for the static site.

### Stage 5: Publication

- Write briefing data to `docs/data/news.json`.
- Write timing, token, and estimated cost data to `docs/data/news_stats.json`.

## Feedback Learning Loop

### Input

- Exported JSON containing:
  - `date`
  - `title`
  - `result`

### Processing

- Compare liked and disliked items against the current filter profile.
- Identify false positives and uncovered positive classes.
- Ask Gemini to refactor pass/block rules at the pattern level.

### Output

- A candidate next profile
- A learning report with diagnosis and raw model output

## Important Constraint

The learning step should suggest profile evolution, not silently mutate production rules without review.
