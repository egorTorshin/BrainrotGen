# BrainrotGen

Коротко: **FastAPI** (`backend/`) + **worker** (`worker/`) + общая SQLite `data/app.db` и каталог `output/` для готовых видео.

- Запуск всего стека: `docker compose up --build` (сначала поднимается backend и создаёт схему БД).
- Сквозной сценарий API → worker → файл: [docs/E2E_BACKEND_WORKER.md](docs/E2E_BACKEND_WORKER.md).
- Worker и пайплайн: [README-WORKER.md](README-WORKER.md).
- Backend: [backend/README.md](backend/README.md).

Перед первым прогоном положите хотя бы один `.mp4` в `worker/assets/minecraft/` (и при необходимости `subway/`).