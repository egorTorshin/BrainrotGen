# BrainrotGen

Коротко: **FastAPI** (`backend/`) + **worker** (`worker/`) + **React/Vite** (`frontend/`), общая SQLite `data/app.db` и каталог `output/` для готовых видео.

- Запуск всего стека (бэк :8000, воркер, фронт :5173): `docker compose up --build`. UI: http://127.0.0.1:5173 — API для браузера идёт на `http://127.0.0.1:8000` (см. `VITE_API_URL` в compose).
- Локально без Docker-фронта: в одном терминале `docker compose up backend worker`, в другом `cd frontend && npm run dev` (по умолчанию тот же API URL).
- Сквозной сценарий API → worker → файл: [docs/E2E_BACKEND_WORKER.md](docs/E2E_BACKEND_WORKER.md).
- Worker и пайплайн: [README-WORKER.md](README-WORKER.md).
- Backend: [backend/README.md](backend/README.md).

Перед первым прогоном положите хотя бы один `.mp4` в `worker/assets/minecraft/` (и при необходимости `subway/`).