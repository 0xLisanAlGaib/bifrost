# 01 — Repo scaffold

## Goal
Minimal installable Python package with lint + tests wired.

## Inputs
- `pyproject.toml` (requires-python >=3.12, deps: pydantic; dev: pytest, ruff).

## Outputs
- `src/bifrost/__init__.py`, `src/bifrost/adapters/__init__.py`
- `tests/` runnable via `python3 -m pytest`
- `README.md`, `.gitignore`

## Acceptance
- `python3 -m pip install -e ".[dev]"` succeeds.
- `python3 -m pytest` collects (0 failures allowed for empty suite).
- `ruff check src tests` clean (or documented exceptions).
