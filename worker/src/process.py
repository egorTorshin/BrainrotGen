import os
import subprocess
import time

import requests

from db import get_conn
from generate_video.pipeline import output_dir, run_pipeline
from generate_video.backgrounds import assets_root_from_env, pick_background_video
from generate_video.tts import wav_duration_seconds

# Transient failures: HTTP TTS, ffmpeg/piper subprocess flakiness.
_RETRYABLE = (requests.RequestException, subprocess.CalledProcessError)


def process_job(job):
    """Process a single job from the queue."""
    job_id = job["id"]

    conn = None
    try:
        result = _generate_video_with_retries(job)
        wav_path = output_dir() / f"{job_id}.wav"
        actual = wav_duration_seconds(wav_path)
        if actual is None:
            actual = float(job.get("estimated_duration") or 0.0)
        conn = _update_job_status(
            job_id,
            "done",
            result_path=str(result),
            actual_duration_seconds=actual,
        )

    except Exception as e:
        conn = _update_job_status(job_id, "failed", error=str(e))

    finally:
        if conn:
            conn.close()


def _max_pipeline_attempts() -> int:
    return max(1, int(os.environ.get("WORKER_PIPELINE_MAX_ATTEMPTS", "3")))


def _retry_delay_sec() -> float:
    return float(os.environ.get("WORKER_PIPELINE_RETRY_DELAY_SEC", "1.0"))


def _generate_video_with_retries(job):
    """Run the pipeline with limited retries on transient errors."""
    max_attempts = _max_pipeline_attempts()
    base_delay = _retry_delay_sec()
    for attempt in range(max_attempts):
        try:
            return _generate_video(job)
        except _RETRYABLE:
            if attempt >= max_attempts - 1:
                raise
            time.sleep(base_delay * (2**attempt))


def _generate_video(job):
    """Run video generation pipeline."""
    assets_root = assets_root_from_env()
    video_path = pick_background_video(assets_root, job.get("background", "minecraft"))

    return run_pipeline(
        job_id=job["id"],
        text=job["text"],
        voice=job.get("voice", "male"),
        video_path=video_path,
    )


def _update_job_status(
    job_id: str,
    status: str,
    result_path: str = None,
    error: str = None,
    actual_duration_seconds: float = None,
):
    """Update job status in database."""
    conn = get_conn()
    cursor = conn.cursor()

    if status == "done":
        cursor.execute(
            """
            UPDATE jobs
            SET status = 'done',
                result_path = ?,
                actual_duration_seconds = ?,
                finished_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (result_path, actual_duration_seconds, job_id),
        )
    else:  # failed
        cursor.execute(
            """
            UPDATE jobs
            SET status = 'failed', error = ?, finished_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (error, job_id),
        )

    conn.commit()
    return conn
