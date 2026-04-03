FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    libsndfile1 \
    libgomp1 \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry

# Копируем файлы зависимостей ПОЭТОМУ (для кэширования)
COPY pyproject.toml poetry.lock ./

# Устанавливаем зависимости Python через Poetry
RUN poetry install --no-ansi --no-interaction --no-root

# Отключаем создание виртуального окружения (в Docker оно не нужно)
ENV POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# Piper
RUN wget -O piper.tar.gz https://github.com/rhasspy/piper/releases/latest/download/piper_linux_x86_64.tar.gz \
    && tar -xvf piper.tar.gz \
    && ls -R /app/piper \
    && chmod +x /app/piper/piper

RUN mkdir -p /app/piper_voice

RUN wget -O /app/piper_voice/en_GB-alba-medium.onnx \
    https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alba/medium/en_GB-alba-medium.onnx

RUN wget -O /app/piper_voice/en_GB-alba-medium.onnx.json \
    https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alba/medium/en_GB-alba-medium.onnx.json


COPY . .

RUN mkdir -p /app/output

CMD ["python", "main.py"]