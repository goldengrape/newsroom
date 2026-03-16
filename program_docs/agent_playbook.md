# Agent Playbook

## Purpose

This document defines how an AI agent should help a user operate and evolve the Newsroom project.

The intended agent is capable of some combination of:

- local repository operations
- terminal execution
- browser-based GitHub configuration
- lightweight product guidance during filter iteration

## Operating Principles

1. Prefer a working daily briefing over premature optimization.
2. Keep the user in control of production filter changes.
3. Treat filter learning as a review loop, not a fully autonomous rewrite loop.
4. Avoid introducing backend complexity unless the workflow clearly outgrows local feedback export.

## Mode 1: Repository Bootstrap

### Goal

Help a new user get the project running locally with minimal friction.

### Agent Checklist

1. Ask whether the user wants:
   - a forked GitHub copy
   - or a local-only clone
2. If using GitHub, help the user fork the repository first.
3. Clone the repository:
   ```bash
   git clone <repo-or-fork-url>
   cd newsroom
   ```
4. Install dependencies:
   ```bash
   uv sync --dev
   ```
5. Help create `.env` with:
   ```dotenv
   GEMINI_API_KEY=...
   ```
6. Run verification:
   ```bash
   uv run newsroom-gemini-smoke
   uv run pytest
   ```

### Agent Success Criteria

- `uv run pytest` passes
- Gemini smoke test succeeds
- user understands the main commands

## Mode 2: GitHub Deployment Support

### Goal

Help the user deploy the static site and enable scheduled automation.

### Agent Checklist

1. Ensure the repository is pushed to `main`.
2. Verify that `main` is the default branch.
3. In GitHub repository settings, add:
   - `GEMINI_API_KEY` under `Settings -> Secrets and variables -> Actions`
4. Check that the following workflows exist and are enabled:
   - `.github/workflows/daily-news.yml`
   - `.github/workflows/deploy-pages.yml`
5. If GitHub Pages asks for a publishing source, select `GitHub Actions`.
6. Confirm that the Pages deployment succeeds after a push to `main`.

### Agent Success Criteria

- daily workflow can run
- Pages deployment succeeds
- user has a reachable public or private site URL

## Mode 3: Daily User Assistance

### Goal

Help the user understand and use the generated briefing without adding friction.

### Agent Checklist

1. Explain that the daily briefing is generated from:
   - RSS aggregation
   - Gemini title screening
   - Gemini ranking
   - Gemini translation
2. Point the user to the feedback controls in the static site:
   - `like`
   - `dislike`
   - export feedback JSON
3. Encourage lightweight interaction rather than exhaustive labeling.

### Recommended Message Pattern

An agent should suggest:

- “Use the default filter first.”
- “Read the briefing normally for a few days.”
- “Only mark strong likes and strong dislikes.”
- “Export once per week instead of over-optimizing daily.”

## Mode 4: Filter Design Assistance

### Goal

Help the user arrive at a useful personal filter without requiring them to manually author a perfect profile up front.

### Initial Strategy

1. Start from `data/FILTER_PROFILE.md`.
2. Do not try to fully customize the filter before observing real outputs.
3. If the output feels too broad, help the user sample a subset of items and react quickly:
   - useful
   - noisy
4. Use feedback patterns to guide profile evolution rather than rewriting from intuition alone.

### When the User Has No Clear Initial Profile

The agent can recommend:

1. Keep the default profile for week one.
2. Ask the user to label only a small number of strong examples.
3. Wait until enough signal accumulates before running profile learning.

This avoids overfitting to first impressions.

## Mode 5: Feedback Collection Loop

### Goal

Convert user reading behavior into a structured improvement signal.

### Minimal Feedback Schema

The current project stores:

- `date`
- `title`
- `result`

### Agent Checklist

1. Remind the user that feedback is stored locally in the browser.
2. Ask the user to export feedback JSON weekly.
3. Suggest placing exported files into:
   - `data/feedback/`
4. Keep raw exports as historical records.

### Weekly Rhythm

Recommended cadence:

1. Read during the week
2. Click `like` / `dislike`
3. Export once per week
4. Review accumulated signal
5. Run filter learning

## Mode 6: Filter Learning and Review

### Goal

Generate a candidate next version of the filter without silently overwriting the production version.

### Agent Checklist

1. Identify the latest feedback export:
   ```bash
   uv run newsroom-learn-filter --feedback data/feedback/feedback-YYYY-MM-DD.json
   ```
2. Review generated outputs:
   - `data/FILTER_PROFILE.updated.md`
   - `data/FILTER_PROFILE.learning_report.md`
3. Summarize:
   - what noise patterns were tightened
   - what high-value patterns were newly protected
   - whether the proposed changes appear too broad
4. Ask the user for approval before replacing `data/FILTER_PROFILE.md`.

### Agent Success Criteria

- candidate profile is generated
- user receives a concise explanation of the proposed changes
- production profile changes only with explicit approval

## Mode 7: Safe Change Promotion

### Goal

Promote only reviewed improvements into the production filter.

### Agent Checklist

1. Compare current and candidate profiles.
2. Summarize the material differences.
3. Highlight likely benefits and likely risks.
4. Only after user approval:
   - replace `data/FILTER_PROFILE.md`
   - rerun the pipeline
   - inspect output quality

### Anti-Pattern

The agent should not:

- automatically overwrite the production profile every time feedback exists
- treat one small batch of dislikes as universal evidence
- aggressively narrow the filter after only a few examples

## Mode 8: When to Recommend a Backend

### A backend is not necessary when:

- there is one user
- feedback is exported manually
- weekly iteration is acceptable

### A backend becomes worth discussing when:

1. feedback must sync across devices
2. multiple users label the briefing
3. the user wants server-side storage directly from GitHub Pages
4. the learning loop should run on a schedule without manual export

### Recommended Lightweight Options

- Cloudflare Workers + KV
- Supabase
- Firebase
- minimal FastAPI service

## Standard Commands for the Agent

### Local setup

```bash
uv sync --dev
uv run pytest
uv run newsroom-gemini-smoke
```

### Daily pipeline

```bash
uv run newsroom-fetch
uv run newsroom-filter
```

### Filter learning

```bash
uv run newsroom-learn-filter --feedback data/feedback/feedback-YYYY-MM-DD.json
```

## Final Guideline

The agent should optimize for calm iteration:

- get the system running
- collect lightweight feedback
- review patterns weekly
- evolve the filter deliberately

That is the intended operating model for this project.
