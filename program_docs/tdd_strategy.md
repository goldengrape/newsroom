# TDD Strategy

## Intent

The project uses tests to stabilize prompt plumbing, file IO, and orchestration logic rather than to validate live model quality.

## Scope

### Unit-Level

- JSON extraction and parsing helpers
- Feedback normalization and profile-output extraction
- RSS fetch success and failure handling
- Main-function file writing behavior through mocks

### Non-Goals

- Golden-output testing of live model responses
- Snapshot testing of the full static website
- Network-dependent integration tests in CI

## Test Stack

- Runner: `pytest`
- Import path: configured through `pyproject.toml`
- Network calls: mocked or stubbed

## Workflow

1. Add or adjust a test before changing orchestration logic.
2. Keep API tests deterministic by stubbing `_request_json` or `LearnFilterEngine.generate`.
3. Run `uv run pytest` locally before pushing workflow changes.
