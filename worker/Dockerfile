FROM python:3.11-slim

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    wget \
    libsndfile1 \
    libgomp1 \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

WORKDIR /app

# Runtime deps only (no pytest/flake8/black from the dev group)
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-ansi --no-interaction --no-root --without dev

# Piper binary (single layer) — multi-arch: picks amd64 or arm64 from buildx TARGETARCH
ARG TARGETARCH
RUN case "${TARGETARCH:-$(dpkg --print-architecture)}" in \
      amd64)  PIPER_ARCH=x86_64 ;; \
      arm64)  PIPER_ARCH=aarch64 ;; \
      armhf)  PIPER_ARCH=armv7 ;; \
      *) echo "unsupported TARGETARCH: ${TARGETARCH}" && exit 1 ;; \
    esac \
    && wget -q -O piper.tar.gz "https://github.com/rhasspy/piper/releases/latest/download/piper_linux_${PIPER_ARCH}.tar.gz" \
    && tar -xf piper.tar.gz \
    && chmod +x /app/piper/piper \
    && rm -f piper.tar.gz

# Voice models — one layer; first build downloads ~tens of MB (cache until pyproject/lock changes)
RUN mkdir -p /app/piper_voice \
    && wget -q -O /app/piper_voice/en_GB-alba-medium.onnx \
        https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alba/medium/en_GB-alba-medium.onnx \
    && wget -q -O /app/piper_voice/en_GB-alba-medium.onnx.json \
        https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alba/medium/en_GB-alba-medium.onnx.json \
    && wget -q -O /app/piper_voice/en_GB-northern_english_male-medium.onnx \
        https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx \
    && wget -q -O /app/piper_voice/en_GB-northern_english_male-medium.onnx.json \
        https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx.json

COPY . .

RUN mkdir -p /app/output

CMD ["python", "src/main.py"]
