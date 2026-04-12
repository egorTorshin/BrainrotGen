import time
import json
from pathlib import Path

from src.db import get_conn
from src.generate_video.subtitles import generate_srt
from src.job_queue import fetch_and_lock_job

# ============================================================================
# CONFIG
# ============================================================================

MAX_RETRIES = 3
OUTPUT_DIR = Path("/app/output")


# ============================================================================
# HELPERS (LOW COMPLEXITY)
# ============================================================================


def sleep_backoff(attempt):
    time.sleep(2**attempt)


def safe_json_load(value):
    try:
        return json.loads(value) if value else {}
    except Exception:
        return {}


def build_srt_path(job_id):
    return OUTPUT_DIR / f"{job_id}.srt"


# ============================================================================
# RETRY (SIMPLIFIED CONTROL FLOW)
# ============================================================================


def run_subtitles_with_retry(job, audio_path, srt_path):
    attempt = 0

    while attempt < MAX_RETRIES:
        try:
            generate_srt(job["text"], audio_path, srt_path)
            return
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise
            print(f"SRT generation failed (attempt {attempt + 1}): {e}")
            sleep_backoff(attempt)
            attempt += 1


# ============================================================================
# DATABASE LAYER (SIMPLIFIED BRANCHING)
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


def _load_result(cursor, job_id):
    cursor.execute("SELECT result_path FROM jobs WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    return safe_json_load(row[0] if row else None)


def _save_result(cursor, job_id, data):
    cursor.execute(
        """
        UPDATE jobs
        SET status = 'merge',
            result_path = ?
        WHERE id = ?
        """,
        (json.dumps(data), job_id),
    )


def mark_next_stage(job_id, new_data):
    conn = get_conn()
    try:
        cursor = conn.cursor()

        data = _load_result(cursor, job_id)
        data.update(new_data)

        _save_result(cursor, job_id, data)

        conn.commit()
    finally:
        conn.close()


# ============================================================================
# JOB HANDLING (FLAT FLOW)
# ============================================================================


def get_next_subtitle_job():
    conn = get_conn()
    try:
        return fetch_and_lock_job(conn, status="subtitles")
    finally:
        conn.close()


def extract_audio_path(job):
    data = safe_json_load(job.get("result_path"))
    if "audio_path" not in data:
        raise RuntimeError("audio_path missing in result_path")
    return Path(data["audio_path"])


# ============================================================================
# CORE PROCESS (MINIMAL BRANCHING)
# ============================================================================


def process_single_subtitle_job(job):
    job_id = job["id"]

    audio_path = extract_audio_path(job)
    srt_path = build_srt_path(job_id)

    print(f"Job {job_id}: {audio_path} -> {srt_path}")

    run_subtitles_with_retry(job, audio_path, srt_path)

    mark_next_stage(job_id, {"srt_path": str(srt_path)})


def handle_job_failure(job_id, error):
    print(f"Job {job_id}: Failed - {error}")
    mark_failed(job_id, error)


# ============================================================================
# MAIN LOOP (FLAT + LOW COMPLEXITY)
# ============================================================================


def main():
    print("Subtitle worker started")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    while True:
        job = get_next_subtitle_job()

        if job is None:
            time.sleep(1)
            continue

        job_id = job["id"]
        print(f"Processing job {job_id}")

        try:
            process_single_subtitle_job(job)
        except Exception as e:
            handle_job_failure(job_id, e)


# ============================================================================
# ENTRYPOINT
# ============================================================================

if __name__ == "__main__":
    main()
