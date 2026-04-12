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

# Качество кода (Quality Gates)
|Проверка	| Результат | 	Статус |
|-|-|------|
|Unit Tests | 49/49 passed | 100% |
|Coverage |	86%	|  ≥60% |
|Black formatting |	9 files| OK   | 0 violations|
|Flake8 style |	0 errors	| +    |
|Bandit security	| 0 med/high	| +    |
|Radon MI	| Все файлы A (≥67)	| ≥65  |
|Radon CC |	B (7.5 average)| <10  |


## Запуск всех проверок
```bash
poetry run black --check src/
poetry run flake8 src/ --max-line-length=88
poetry run bandit -r src/ -ll
poetry run radon mi src/ -s
poetry run radon cc src/ -a -nb --min B
poetry run pytest tests/ -v --cov=src --cov-fail-under=60
```
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
├── ├── worker/
│   ├── assets/                   # Видео-фоны
│   │   └── minecraft.mp4
│   │   └── subway.mp4
│   │
│   ├── generate_video/           # Модули генерации
│   │   ├── pipeline.py           # Оркестрация пайплайна
│   │   ├── tts.py                # Text-to-Speech (Piper/HTTP)
│   │   ├── subtitles.py          # Генерация SRT
│   │   └── video.py              # FFmpeg сборка
│   │
│   ├── db.py                     # Подключение к БД
│   ├── job_queue.py              # Очередь задач (блокировки)
│   ├── process.py                # Обработка одной задачи
│   ├── main.py                   # Основной цикл воркера
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── poetry.lock
│
└── docker-compose.yml
```


---

# База данных (SQLite: `jobs`)

## Таблица `jobs`

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
- поддержка male/female голосов
- fallback при отсутствии модели
- создаётся аудио файл: \
```output/<uuid>.wav```
### 2. Субтитры

Файл:

```generate_video/subtitles.py```

- текст разбивается на строки
- равномерное распределение по длительности аудио
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