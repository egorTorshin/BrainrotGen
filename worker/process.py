from pathlib import Path

from db import get_conn
from generate_video.pipeline import run_pipeline
from generate_video.backgrounds import assets_root_from_env, pick_background_video


def process_job(job):
    job_id = job["id"]
    text = job["text"]
    voice = job.get("voice") or "male"
    background = job.get("background") or "minecraft"

    conn = None
    try:
        assets_root = assets_root_from_env()
        video_path = pick_background_video(assets_root, background)
        result = run_pipeline(
            job_id=job_id,
            text=text,
            voice=voice,
            video_path=video_path,
        )

        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE jobs
            SET status = 'done',
                result_path = ?,
                finished_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (str(result), job_id),
        )

        conn.commit()

    except Exception as e:
        err_conn = get_conn()
        try:
            cursor = err_conn.cursor()
            cursor.execute(
                """
                UPDATE jobs
                SET status = 'failed',
                    error = ?,
                    finished_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (str(e), job_id),
            )
            err_conn.commit()
        finally:
            err_conn.close()
    finally:
        if conn is not None:
            conn.close()
