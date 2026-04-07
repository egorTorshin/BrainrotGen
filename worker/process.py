from pathlib import Path
from generate_video.pipeline import run_pipeline
from db import get_conn

def process_job(job):
    job_id = job["id"]
    text = job["text"]

    try:
        video_path = Path("/app/assets/night_parcour.mp4")
        result = run_pipeline(text, video_path)

        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE jobs
            SET status = 'done',
                result_path = ?,
                finished_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (str(result), job_id))

        conn.commit()
        conn.close()

    except Exception as e:
        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE jobs
            SET status = 'failed',
                error = ?,
                finished_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (str(e), job_id))

        conn.commit()
        conn.close()