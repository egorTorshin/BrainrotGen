from db import get_conn
from generate_video.pipeline import run_pipeline
from generate_video.backgrounds import assets_root_from_env, pick_background_video


def process_job(job):
    """Process a single job from the queue."""
    job_id = job["id"]

    conn = None
    try:
        result = _generate_video(job)
        conn = _update_job_status(job_id, "done", result_path=str(result))

    except Exception as e:
        conn = _update_job_status(job_id, "failed", error=str(e))

    finally:
        if conn:
            conn.close()


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
    job_id: str, status: str, result_path: str = None, error: str = None
):
    """Update job status in database."""
    conn = get_conn()
    cursor = conn.cursor()

    if status == "done":
        cursor.execute(
            """
            UPDATE jobs
            SET status = 'done', result_path = ?, finished_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (result_path, job_id),
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
