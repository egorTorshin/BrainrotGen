# BrainrotGen Worker — Architecture and Usage

## Overview

The Worker is a background process that:

- Picks up tasks from the SQLite queue (`jobs` table)
- Generates audio via TTS (Piper)
- Selects a background video clip
- Composites subtitles and audio using ffmpeg
- Saves the result to `output/`
- Updates the job status in the database

---

# Code Quality (Quality Gates)

| Check | Result | Status |
|-------|--------|--------|
| Unit Tests | 49/49 passed | 100% |
| Coverage | 86% | >= 60% |
| Black formatting | 9 files OK | 0 violations |
| Flake8 style | 0 errors | + |
| Bandit security | 0 med/high | + |
| Radon MI | All files A (>= 67) | >= 65 |
| Radon CC | B (7.5 average) | < 10 |

## Running All Checks

```bash
poetry run black --check src/
poetry run flake8 src/ --max-line-length=88
poetry run bandit -r src/ -ll
poetry run radon mi src/ -s
poetry run radon cc src/ -a -nb --min B
poetry run pytest tests/ -v --cov=src --cov-fail-under=60
```

---

# Project Structure

```
worker/
├── src/
│   ├── generate_video/           # Video generation modules
│   │   ├── pipeline.py           # Pipeline orchestration
│   │   ├── tts.py                # Text-to-Speech (Piper/HTTP)
│   │   ├── subtitles.py          # SRT generation
│   │   ├── backgrounds.py        # Background video selection
│   │   └── video.py              # FFmpeg composition
│   │
│   ├── db.py                     # Database connection
│   ├── job_queue.py              # Job queue with locking
│   ├── process.py                # Single job processing
│   └── main.py                   # Main worker loop
│
├── tests/
├── assets/
│   ├── minecraft/.gitkeep
│   └── subway/.gitkeep
├── Dockerfile
├── pyproject.toml
└── poetry.lock
```

---

# Database (SQLite: `jobs`)

## Table Schema

```sql
CREATE TABLE jobs (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER,
    text TEXT NOT NULL,
    voice VARCHAR(32) NOT NULL,
    background VARCHAR(32) NOT NULL,
    status VARCHAR(16) NOT NULL,
    estimated_duration FLOAT,
    created_at DATETIME NOT NULL,
    started_at DATETIME,
    finished_at DATETIME,
    result_path VARCHAR(256),
    error TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
```

## Column Descriptions

| Column | Description |
|--------|-------------|
| `id` | Unique job identifier (UUID) |
| `text` | Input text for TTS and subtitle generation |
| `status` | `queued` / `processing` / `done` / `failed` |
| `created_at` | When the job was created |
| `started_at` | When the worker began processing |
| `finished_at` | When processing completed |
| `result_path` | Path to the output video (`/app/output/<job_id>.mp4`) |
| `error` | Error message if the pipeline failed |

---

# How the Worker Runs

## Via Docker Compose

```bash
docker compose up --build
```

## Entry Point

```python
# src/main.py
```

## Main Loop

```
fetch job (queued)
    |
lock job (processing)
    |
run pipeline
    |
update DB
```

---

# Video Generation Pipeline

## Input

- `jobs.text`
- Background clip from `worker/assets/`

### 1. Text-to-Speech (Piper)

File: `src/generate_video/tts.py`

- Text is passed to Piper TTS
- Supports male/female voices
- Falls back to any available model if the preferred one is missing
- Output: `output/<job_id>.wav`

### 2. Subtitles

File: `src/generate_video/subtitles.py`

- Text is split into chunks (5 words each)
- Chunks are evenly distributed across the audio duration
- Output: `output/<job_id>.srt`

### 3. Video Composition (FFmpeg)

File: `src/generate_video/video.py`

Inputs:
- Background video (looped with `-stream_loop -1`)
- Audio: `.wav`
- Subtitles: `.srt` (burned in via `subtitles=` filter)

Output: `output/<job_id>.mp4`

## Output Files

All results are saved under `/app/output/`:

- `<job_id>.wav` -- TTS audio
- `<job_id>.srt` -- subtitles
- `<job_id>.mp4` -- final video

### Database Updates

#### On Success

```sql
UPDATE jobs
SET status = 'done',
    result_path = '/app/output/<job_id>.mp4',
    finished_at = CURRENT_TIMESTAMP
WHERE id = ?
```

#### On Failure

```sql
UPDATE jobs
SET status = 'failed',
    error = '<error message>',
    finished_at = CURRENT_TIMESTAMP
WHERE id = ?
```

---

## Background Assets

Place `.mp4` gameplay clips in:

- `worker/assets/minecraft/` -- for Minecraft background
- `worker/assets/subway/` -- for Subway Surfers background

A random clip is selected from the matching folder at generation time.

---

# Architecture Summary

```
SQLite (jobs)
    |
Worker loop
    |
fetch + lock job
    |
TTS (Piper)
    |
Subtitles (.srt)
    |
FFmpeg merge
    |
output/<job_id>.mp4
    |
DB update (done/failed)
```

This is a lightweight job queue built on top of SQLite:

- **SQLite** = task queue
- **Worker** = job processor
- **FFmpeg** = video renderer
