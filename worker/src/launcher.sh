#!/bin/sh

python -m src.workers.worker_tts &
python -m src.workers.worker_subtitles &
python -m src.workers.worker_render &

wait