# CLAUDE.md — langchain-goodsender

LangChain integration package for GoodSender (Python). A thin SDK over the
GoodSender public API — business logic lives in `goodsender-web` (source of
truth). See the workspace umbrella `CLAUDE.md` for cross-repo rules.

## Setup & gates

```bash
pip install -e ".[test]"        # editable install with test extras
pytest tests/unit_tests/        # unit tests (HTTP mocked via respx — no network)
```
Integration tests (`tests/integration_tests/`) hit the live API and need
`GOODSENDER_API_KEY`; they are skipped without it. CI
(`.github/workflows/ci.yml`) runs the unit tests on Python 3.12 for PRs.

- Python: supports 3.9–3.13. Build backend: setuptools.
- No linter/formatter is configured yet — if you add one (ruff recommended), add
  it to `pyproject.toml` and to CI, and update this file.

## Conventions

Conventional Commits; branch off `main` (`feat/ fix/ …`), one PR per backlog
item, label PRs `autopilot`. `main` is protected; `publish.yml` releases to PyPI
on `v*` tags — never tag/release without approval. Keep this package additive and
backwards-compatible with the public API contract (umbrella golden rule #2).
