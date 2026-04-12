import json
import time
from pathlib import Path

from src.db import get_conn
from src.generate_video.video import merge_video_audio_subs
from src.generate_video.backgrounds import pick_background_video, assets_root_from_env
from src.job_queue import fetch_and_lock_job

# ============================================================================
# CONFIG
# ============================================================================

MAX_RETRIES = 3


# ============================================================================
# RETRY (LOW COMPLEXITY VERSION)
# ============================================================================


def sleep_backoff(attempt):
    time.sleep(2**attempt)


def run_render_with_retry(video_path, audio_path, srt_path, output_path):
    attempt = 0

    while attempt < MAX_RETRIES:
        try:
            merge_video_audio_subs(video_path, audio_path, srt_path, output_path)
            return output_path

        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise

            print(f"Render failed (attempt {attempt + 1}): {e}")
            sleep_backoff(attempt)
            attempt += 1


# ============================================================================
# DB HELPERS
# ============================================================================


def mark_failed(job_id, error):
    conn = get_conn()
    try:
        conn.cursor().execute(
            """
            UPDATE jobs
            SET status = 'failed',
                error = ?,
                finished_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (str(error), job_id),
        )
        conn.commit()
    finally:
        conn.close()


def mark_done(job_id, output_path):
    conn = get_conn()
    try:
        conn.cursor().execute(
            """
            UPDATE jobs
            SET status = 'done',
                result_path = ?,
                finished_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (str(output_path), job_id),
        )
        conn.commit()
    finally:
        conn.close()


# ============================================================================
# PIPELINE HELPERS (IMPORTANT FOR MI)
# ============================================================================


def load_pipeline_data(job):
    data = json.loads(job.get("result_path") or "{}")
    return (
        Path(data["audio_path"]),
        Path(data["srt_path"]),
    )


def build_output_path(job_id):
    return Path(f"/app/output/{job_id}.mp4")


def select_background(job):
    assets_root = assets_root_from_env()
    return pick_background_video(assets_root, job["background"])


def render_video(video_path, audio_path, srt_path, output_path):
    return run_render_with_retry(video_path, audio_path, srt_path, output_path)


# ============================================================================
# MAIN LOOP (FLAT, LOW COMPLEXITY)
# ============================================================================


def main():
    print("Render worker started")
    print("Waiting for jobs with status 'merge'...")

    while True:
        conn = get_conn()
        try:
            job = fetch_and_lock_job(conn, status="merge")
        finally:
            conn.close()

        if not job:
            time.sleep(1)
            continue

        job_id = job["id"]
        print(f"Processing job {job_id}")

        try:
            audio_path, srt_path = load_pipeline_data(job)

            video_path = select_background(job)
            output_path = build_output_path(job_id)

            print(f"Job {job_id}: {video_path} -> {output_path}")

            render_video(video_path, audio_path, srt_path, output_path)

            mark_done(job_id, output_path)

            print(f"Job {job_id}: done")

        except Exception as e:
            print(f"Job {job_id}: failed - {e}")
            mark_failed(job_id, e)


# ============================================================================
# ENTRYPOINT
# ============================================================================

if __name__ == "__main__":
    main()
