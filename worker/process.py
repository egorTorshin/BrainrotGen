from pathlib import Path
from generate_video.pipeline import run_pipeline

def process_job(conn, job):
    cursor = conn.cursor()
    job_id = job["id"]
    text = job["text"]

    try:
        video_path = Path("/app/assets/sample-5s.mp4")

        result = run_pipeline(text, video_path)

        cursor.execute("""
            UPDATE jobs
            SET status = 'done',
                result_path = ?,
                finished_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (str(result), job_id))

    except Exception as e:
        cursor.execute("""
            UPDATE jobs
            SET status = 'failed',
                error = ?,
                finished_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (str(e), job_id))

    conn.commit()