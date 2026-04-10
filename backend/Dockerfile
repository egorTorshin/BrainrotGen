FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY src ./src

ENV PYTHONPATH=/app/src
EXPOSE 8000

CMD ["uvicorn", "brainrot_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
