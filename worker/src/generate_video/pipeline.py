from __future__ import annotations

import os
from pathlib import Path

from .subtitles import generate_srt
from .tts import text_to_speech
from .video import merge_video_audio_subs


def output_dir() -> Path:
    return Path(os.environ.get("OUTPUT_DIR", "/app/output"))


def run_pipeline(
    *,
    job_id: str,
    text: str,
    voice: str,
    video_path: Path,
) -> Path:
    """
    TTS → SRT → ffmpeg merge. Output files use *job_id*
    so ``result_path`` matches the job row.
    """
    out = output_dir()
    out.mkdir(parents=True, exist_ok=True)

    audio_path = text_to_speech(text, voice, job_id, out_dir=out)

    srt_path = out / f"{job_id}.srt"
    generate_srt(text, audio_path, srt_path)

    output_video = out / f"{job_id}.mp4"

    merge_video_audio_subs(
        video_path=video_path,
        audio_path=audio_path,
        srt_path=srt_path,
        output_path=output_video,
    )

    return output_video
