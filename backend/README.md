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

The default SQLite file is **`data/app.db`** (same as the worker). Ensure the `data/` directory exists or start once so the app creates it.

Run the API (from `backend/`):

```bash
poetry run uvicorn brainrot_backend.main:app --app-dir src --reload
```

### Docker (from repository root)

```bash
docker compose up --build backend
```

Uses `./data` and `./output` volumes; set `MEDIA_ROOT=/app/output` in compose for alignment with the worker.

Open docs: `http://127.0.0.1:8000/docs`

## Result file download

After a job finishes (`status: done`), the video can be fetched with a JWT:

`GET /api/v1/jobs/{job_id}/result`

Set `MEDIA_ROOT` in `.env` to the same directory the worker writes to (e.g. `output` or `/app/output` in Docker).

## Tests

Tests use a **temporary SQLite file and media directory** (set in `tests/conftest.py` via `pytest_configure`) so they do not touch local `brainrotgen.db`

```bash
poetry run pytest
```

Coverage threshold is **≥ 60%** (per Quality Plan); the suite currently exercises health, auth, jobs, quota (including **429** when the daily limit is exceeded), result download, and `estimate_duration`.

## Quality Commands

```bash
poetry run black --check src tests
poetry run flake8 src tests
poetry run bandit -r src -ll
poetry run radon cc -a -s src
poetry run radon mi -s src
poetry run pytest --cov=src/brainrot_backend --cov-fail-under=60
```
