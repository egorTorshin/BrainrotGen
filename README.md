# BrainrotGen

Short-form "Brainrot" video generator: **FastAPI** backend (`backend/`), **Streamlit** frontend (`frontend/`), and a video **worker** (`worker/`). Shared SQLite database (`data/app.db`) and output directory (`output/`) for generated videos.

## Quick Start

```bash
docker compose up --build
```

| Service  | URL                        |
|----------|----------------------------|
| Frontend | http://localhost:8501       |
| Backend  | http://localhost:8000       |
| API docs | http://localhost:8000/docs  |

Before the first run, place at least one `.mp4` gameplay clip into `worker/assets/minecraft/` (and optionally `worker/assets/subway/`).

## Architecture

- **Backend** (FastAPI) — REST API for auth, job management, quota enforcement, video download.
- **Frontend** (Streamlit) — UI for registration, login, video generation, and preview.
- **Worker** — polls the DB for queued jobs, runs TTS (Piper), generates subtitles, composites video with ffmpeg.

## Documentation

- Worker pipeline details: [README-WORKER.md](README-WORKER.md)
- Backend API: [backend/README.md](backend/README.md)
