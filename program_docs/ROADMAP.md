# Roadmap

## Objective

Make the project evolve from a reliable personal daily-briefing tool into a maintainable intelligence system with an explicit review loop.

## Phase 1: Stable Daily Production

Status: completed

- RSS aggregation is automated.
- Gemini-based filtering, ranking, and translation are automated.
- GitHub Pages publishing is automated.
- Local feedback capture is available in the static site.

## Phase 2: Feedback-to-Rule Learning

Status: in progress

### Current State

- The site stores local `like` and `dislike` feedback in browser storage.
- Feedback can be exported as JSON.
- `newsroom-learn-filter` can read exported feedback and propose an updated filter profile.

### Next Hardening Steps

1. Add a review-friendly diff artifact between `data/FILTER_PROFILE.md` and `data/FILTER_PROFILE.updated.md`.
2. Add a small approval workflow for promoting the updated profile into production.
3. Track a minimal changelog history of approved profile revisions.

## Phase 3: Review and Governance

Status: planned

### Goal

Prevent silent prompt drift and keep the filtering persona coherent over time.

### Planned Features

1. Introduce a manual review checklist for profile changes.
2. Require explicit promotion from candidate profile to production profile.
3. Keep a versioned archive of approved profile snapshots.
4. Add regression checks using a small curated set of historically liked/disliked examples.

## Phase 4: Better Evaluation

Status: planned

### Goal

Move from informal taste adjustment to measurable filtering quality.

### Planned Features

1. Build a gold dataset from exported feedback.
2. Measure false positives and false negatives across profile versions.
3. Compare prompt or rule variants before adopting them.
4. Separate “selection quality” from “translation quality” in evaluation.

## Phase 5: Optional Multi-Device Sync

Status: exploratory

### When a Backend Becomes Worth It

Only introduce a backend if one or more of the following become real needs:

1. Feedback must sync across devices.
2. Feedback should be stored directly from GitHub Pages without manual export.
3. More than one user will review and label news.
4. You want the learning loop to run automatically on a schedule.

### Lightweight Backend Options

- Cloudflare Workers + KV
- Supabase
- Firebase
- A minimal FastAPI service

## Recommended Near-Term Sequence

1. Keep the current local-feedback workflow for a few weeks.
2. Accumulate enough liked/disliked examples to form a small evaluation set.
3. Add profile diff generation and manual approval.
4. Only then decide whether sync or server-side storage is worth the extra complexity.

## Non-Goals for Now

1. Fully autonomous profile rewriting without review.
2. Overfitting the filter to a tiny amount of feedback.
3. Premature backend complexity for a single-user workflow.
