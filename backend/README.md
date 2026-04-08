# BrainrotGen Backend

Baseline backend skeleton for BrainrotGen built with FastAPI, Poetry, and SQLite.

## Stack

- Python 3.11+
- Poetry
- FastAPI
- SQLite (via SQLAlchemy + `aiosqlite`)

## Quickstart

```bash
poetry install
```

Optional local configuration:

```bash
cp .env.example .env
```

Run the API (from `backend/`):

```bash
poetry run uvicorn brainrot_backend.main:app --app-dir src --reload
```

Open docs: `http://127.0.0.1:8000/docs`

## Quality Commands

```bash
poetry run black --check src tests
poetry run flake8 src tests
poetry run bandit -r src -ll
poetry run radon cc -a -s src
poetry run radon mi -s src
poetry run pytest --cov=src/brainrot_backend --cov-fail-under=60
```
