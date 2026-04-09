# BrainrotGen Worker — архитектура и запуск

## Общая идея

Worker — это фоновый процесс, который:

- забирает задачи из SQLite очереди (`jobs`)
- генерирует аудио (TTS через Piper)
- берёт видео-фон
- накладывает субтитры и аудио через ffmpeg
- сохраняет результат в `output/`
- обновляет статус задачи в базе

---

# Структура проекта
```commandline
BrainrotGen/
├── data/
│ ├── app.db          # shared with FastAPI (see backend SQLITE_FILE)
│ ├── init_db.py      # optional PRAGMA only; schema from API
│ ├── add_job.py      # debug enqueue only
│
├── output/           # generated videos (same as backend MEDIA_ROOT)
│
├── worker/
│ ├── assets/
│ │ ├── minecraft/    # .mp4 clips (random pick)
│ │ └── subway/
│ │
│ ├── generate_video/
│ │ ├── pipeline.py
│ │ ├── tts.py
│ │ ├── subtitles.py
│ │ ├── video.py
│ │
│ ├── db.py
│ ├── job_queue.py
│ ├── process.py
│ ├── main.py
│ ├── Dockerfile
│ ├── pyproject.toml
│ ├── poetry.lock
│
├── docker-compose.yml
```


---

# База данных (SQLite)

Файл по умолчанию: **`data/app.db`** (локально) или **`/app/data/app.db`** в Docker.  
**Схему создаёт FastAPI** при старте (`SQLAlchemy create_all`). Worker только читает/обновляет строки.

## Таблица `jobs` (соответствует ORM в backend)

| Колонка | Описание |
|--------|----------|
| `id` | UUID задачи (TEXT PK) |
| `user_id` | FK на `users.id`, может быть NULL (отладочные вставки) |
| `text` | Текст озвучки и субтитров |
| `voice` | `male` / `female` — выбор модели Piper |
| `background` | `minecraft` / `subway` — папка ассетов |
| `status` | `queued` → `processing` → `done` \| `failed` |
| `estimated_duration` | Оценка секунд (учёт квоты на API) |
| `created_at`, `started_at`, `finished_at` | Временные метки |
| `result_path` | Путь к готовому `.mp4` (часто `/app/output/<job_id>.mp4`) |
| `error` | Текст ошибки при `failed` |

Таблица `users` создаётся API; для нормального сценария задачи создаются через **POST /api/v1/jobs**.

# Как запускается worker
## Через Docker Compose
```bash
docker-compose up --build
```
## Worker стартует через:
```python
main.py
```
## Основной цикл работы
```
fetch job (queued)
    ↓
lock job (processing)
    ↓
run pipeline
    ↓
update DB
```
# Pipeline генерации видео
## Входные данные

- `jobs.text`, `jobs.voice`, `jobs.background`
- случайный `.mp4` из `worker/assets/minecraft/` или `worker/assets/subway/` (`generate_video/backgrounds.py`)

### 1. Text-to-Speech

`generate_video/tts.py`

- По умолчанию **Piper**: `male` → `en_US-lessac`, `female` → `en_GB-alba`.
- Опционально: `TTS_BACKEND=http` и `TTS_HTTP_URL` — POST с JSON `{"text": "..."}`, ответ — сырой аудиофайл (например WAV).

Аудио: `OUTPUT_DIR/<job_id>.wav`

### 2. Субтитры

`generate_video/subtitles.py` → `OUTPUT_DIR/<job_id>.srt`

### 3. Сборка (FFmpeg)

`generate_video/video.py` — наложение аудио и субтитров на выбранный клип.

Итог: **`OUTPUT_DIR/<job_id>.mp4`** (имя совпадает с id задачи).

## Output (результаты)

Каталог задаётся переменной **`OUTPUT_DIR`** (в Docker: `/app/output`, локально обычно `./output`).

Файлы на один job: `<job_id>.wav`, `<job_id>.srt`, `<job_id>.mp4`.
### Обновление базы данных
#### Успешное выполнение
```sql
UPDATE jobs
SET status = 'done',
    result_path = '/app/output/<job_id>.mp4',
    finished_at = CURRENT_TIMESTAMP
WHERE id = ?
```
#### Ошибка выполнения
```sql
UPDATE jobs
SET status = 'failed',
    error = '<error message>',
    finished_at = CURRENT_TIMESTAMP
WHERE id = ?
```
## Видео-источник (assets)

Корень: **`ASSETS_ROOT`** (по умолчанию `/app/assets`). Подкаталоги **`minecraft/`** и **`subway/`** — положите туда несколько `.mp4`; для каждого job выбирается случайный файл.

# Итог архитектуры
```
SQLite (jobs)
    ↓
Worker loop
    ↓
fetch + lock job
    ↓
TTS (Piper)
    ↓
Subtitles (.srt)
    ↓
FFmpeg merge
    ↓
output/<job_id>.mp4
    ↓
DB update (done/failed)
```
# Ключевая идея

Это lightweight job queue поверх SQLite:

- SQLite = очередь задач
- Worker = обработчик
- FFmpeg = рендеринг видео

---