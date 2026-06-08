# Contributing to PROVE

Thanks for your interest in improving PROVE. This guide covers local setup, the
checks CI runs, and how to propose changes.

## Local setup

```bash
docker compose up -d        # Neo4j (required for the full test suite + app)
uv sync                     # install deps (including dev group)
just dev                    # run the app on :7860
```

## Before you open a PR

CI runs the same three checks — run them locally first:

```bash
uv run ruff check src tests          # lint
uv run ruff format --check src tests  # formatting
uv run pytest tests/ -m "not e2e"     # unit tests (need Neo4j running)
```

- **`-m "not e2e"`** deselects the Playwright browser suite. Those tests need a
  live server (`just dev`) and `BASE_URL`; run them with `uv run pytest tests/e2e`
  only when you've changed frontend/layout behavior.
- Apply formatting with `uv run ruff format src tests`.
- New behavior should come with a test. Pure-logic code is tested with mocks
  (see `tests/test_qa.py`); avoid adding tests that require live LLM API calls.

## Style

- Python ≥ 3.11. Formatting and lint are enforced by `ruff` (config in
  `pyproject.toml`).
- No `print` — use `from src.core import logger`.
- Keep functions small and explicit; prefer standard-library solutions over new
  dependencies. Each new dependency should justify itself.

## Commit / PR conventions

- Keep PRs focused — one logical change per PR.
- Write a clear description of *what* changed and *why*.
- Reference any related issue.

## Reporting bugs / requesting features

Open an issue using the templates in `.github/ISSUE_TEMPLATE/`. For security
issues, see [SECURITY.md](SECURITY.md) — do not open a public issue.
