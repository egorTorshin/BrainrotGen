def find_pending_job(conn, status):
    """Find oldest pending job with given status."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, text, voice, background, estimated_duration, result_path
        FROM jobs
        WHERE status = ?
        ORDER BY created_at
        LIMIT 1
    """,
        (status,),
    )
    return cursor.fetchone()


def lock_job(conn, job_id):
    """Lock a job by setting its status to 'processing'."""
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE jobs SET status = 'processing' WHERE id = ?",
        (job_id,),
    )


def format_job_data(row):
    """
    Convert database row to job dictionary with defaults.

    Args:
        row: Tuple (id, text, voice, background, estimated_duration, result_path)

    Returns:
        Dictionary with formatted job data
    """
    job_id, text, voice, background, estimated_duration, result_path = row

    return {
        "id": job_id,
        "text": text,
        "voice": voice or "male",
        "background": background or "minecraft",
        "estimated_duration": float(estimated_duration or 0.0),
        "result_path": result_path or "{}",
    }


def fetch_and_lock_job(conn, status):
    """
    Find and lock a pending job for processing.

    Complexity: A (~3-4) instead of B (~7-8)
    """
    cursor = conn.cursor()

    try:
        cursor.execute("BEGIN IMMEDIATE")

        row = find_pending_job(conn, status)

        if not row:
            conn.commit()
            return None

        lock_job(conn, row[0])  # row[0] is job_id

        conn.commit()

        return format_job_data(row)

    except Exception:
        conn.rollback()
        raise
