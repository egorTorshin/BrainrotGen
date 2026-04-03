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
│ ├── app.db
│ ├── init_db.py
│ ├── add_job.py
│ ├── check.py
│
├── output/
│
├── worker/
│ ├── assets/
│ │ └── night_parcour.mp4
│ │
│ ├── generate_video/
│ │ ├── pipeline.py
│ │ ├── tts.py
│ │ ├── subtitles.py
│ │ ├── video.py
│ │
│ ├── db.py
│ ├── queue.py
│ ├── process.py
│ ├── main.py
│ ├── Dockerfile
│ ├── pyproject.toml
│ ├── poetry.lock
│
├── docker-compose.yml
```


---

# База данных (SQLite: `jobs`)

## Таблица `jobs`

```sql
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,
    text TEXT,
    status TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME,
    finished_at DATETIME,
    result_path TEXT,
    error TEXT
);
```

## Поля таблицы
```sql
id
```
Уникальный идентификатор задачи.
```sql
text
```
Входной текст для генерации:
- используется для TTS (Piper)
- используется для генерации субтитров
```sql
status
```
Состояние задачи:
- status	- значение
- queued -	ожидает обработки
- processing -	выполняется worker’ом
- done	- успешно завершена
- failed - ошибка
- created_at

Время создания задачи.
```sql
started_at
```
Когда worker начал обработку.
```sql
finished_at
```
Когда обработка завершилась.
```sql
result_path
```
Путь к итоговому видео:
```bash
/app/output/<uuid>.mp4
```
```bash
error
```
Текст ошибки при падении pipeline.

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

- jobs.text
- worker/assets/night_parcour.mp4

### 1. Text-to-Speech (Piper)

Файл:

```generate_video/tts.py```

Процесс:

- текст → Piper
- создаётся аудио файл: \
```output/<uuid>.wav```
### 2. Субтитры

Файл:

```generate_video/subtitles.py```

- текст разбивается на строки
- генерируется .srt \
```output/<uuid>.srt```
### 3. Сборка видео (FFmpeg)

Файл:

```generate_video/video.py```

Используется:

- фон: ```worker/assets/night_parcour.mp4```
- аудио: .wav
- субтитры: .srt

Результат:

- финальный .mp4

### Итоговый результат
```output/<uuid>.mp4```
## Output (результаты)

Все результаты сохраняются в:

```/app/output/```\
Файлы:
- <uuid>.wav — аудио (TTS)
- <uuid>.srt — субтитры
- <uuid>.mp4 — итоговое видео
### Обновление базы данных
#### Успешное выполнение
```sql
UPDATE jobs
SET status = 'done',
    result_path = '/app/output/<uuid>.mp4',
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

Сейчас используется:

```worker/assets/night_parcour.mp4```
### Роль:
- фон для всех видео
- пока статический
## Планируемое улучшение

Добавить в БД:

```video_path TEXT```

И позволить каждому job использовать свой фон.

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
output/<uuid>.mp4
    ↓
DB update (done/failed)
```
# Ключевая идея

Это lightweight job queue поверх SQLite:

- SQLite = очередь задач
- Worker = обработчик
- FFmpeg = рендеринг видео

---