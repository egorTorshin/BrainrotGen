FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    libsndfile1 \
    libgomp1 \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Piper
RUN wget -O piper.tar.gz https://github.com/rhasspy/piper/releases/latest/download/piper_linux_x86_64.tar.gz \
    && tar -xvf piper.tar.gz \
    && ls -R /app/piper \
    && chmod +x /app/piper/piper

COPY . .

RUN mkdir -p /app/output

CMD ["python", "main.py"]