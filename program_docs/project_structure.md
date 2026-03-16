# Project Structure

## Goal

Keep the repository understandable as a small but production-shaped Python application.

## Directory Map

- `src/newsroom/`
  Python package with all executable application logic.
- `tests/`
  Pytest suite covering RSS fetching, filtering, and filter-learning helpers.
- `data/`
  Operational inputs and generated review artifacts.
- `docs/`
  Static web frontend served by GitHub Pages.
- `program_docs/`
  Engineering documentation intended for maintainers.

## Design Rules

1. Application code lives only under `src/`.
2. Tests live only under `tests/`.
3. Operational data and filter assets live under `data/`.
4. Static web assets live under `docs/`.
5. Repository-level workflows and packaging metadata stay at the root.
