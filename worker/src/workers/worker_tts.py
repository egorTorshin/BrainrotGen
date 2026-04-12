import time
import json
from pathlib import Path

from src.db import get_conn
from src.generate_video.tts import text_to_speech
from src.job_queue import fetch_and_lock_job

# ============================================================================
# CONFIG
# ============================================================================

MAX_RETRIES = 3
OUTPUT_DIR = Path("/app/output")


# ============================================================================
# SMALL HELPERS (REDUCE CYCLOMATIC COMPLEXITY)
# ============================================================================


def sleep_backoff(attempt):
    time.sleep(2**attempt)


def safe_json_load(value):
    try:
        return json.loads(value) if value else {}
    except Exception:
        return {}


# ============================================================================
# RETRY LOGIC (SIMPLIFIED FLOW)
# ============================================================================


def run_tts_with_retry(job):
    job_id = job["id"]

    attempt = 0

    while attempt < MAX_RETRIES:
        try:
            return text_to_speech(
                job["text"],
                job["voice"],
                job_id,
                out_dir=OUTPUT_DIR,
            )

        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise

            print(f"TTS failed (attempt {attempt + 1}): {e}")
            sleep_backoff(attempt)
            attempt += 1


# ============================================================================
# DB HELPERS (SIMPLIFIED)
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
        SET status = 'subtitles',
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
# JOB HELPERS
# ============================================================================


def get_next_job():
    conn = get_conn()
    try:
        return fetch_and_lock_job(conn, status="queued")
    finally:
        conn.close()


# ============================================================================
# CORE PIPELINE STEP (FLAT)
# ============================================================================


def process_job(job):
    job_id = job["id"]

    print(f"Job {job_id}: generating TTS")

    audio_path = run_tts_with_retry(job)

    print(f"Job {job_id}: audio -> {audio_path}")

    mark_next_stage(job_id, {"audio_path": str(audio_path)})

    print(f"Job {job_id}: moved to subtitles")


# ============================================================================
# FAILURE HANDLER
# ============================================================================


def handle_failure(job_id, error):
    print(f"Job {job_id}: failed - {error}")
    mark_failed(job_id, error)


# ============================================================================
# MAIN LOOP (LOW COMPLEXITY)
# ============================================================================


def main():
    print("TTS worker started")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    while True:
        job = get_next_job()

        if job is None:
            time.sleep(1)
            continue

        job_id = job["id"]

        try:
            process_job(job)
        except Exception as e:
            handle_failure(job_id, e)


# ============================================================================
# ENTRYPOINT
# ============================================================================

if __name__ == "__main__":
    main()
