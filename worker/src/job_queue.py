def fetch_and_lock_job(conn):
    """
    Fetch a queued job and lock it for processing.

    Uses BEGIN IMMEDIATE to prevent race conditions between workers.

    Args:
        conn: SQLite database connection

    Returns:
        Job dict with id, text, voice, background, estimated_duration,
        or None if no queued jobs exist
    """
    cursor = conn.cursor()

    try:
        # Lock the database to prevent other workers from taking the same job
        cursor.execute("BEGIN IMMEDIATE")

        # Get the oldest queued job
        cursor.execute("""
            SELECT id, text, voice, background, estimated_duration
            FROM jobs
            WHERE status = 'queued'
            ORDER BY created_at
            LIMIT 1
            """)
        row = cursor.fetchone()

        # No pending jobs - commit and return None
        if not row:
            conn.commit()
            return None

        job_id, text, voice, background, estimated_duration = row

        # Mark job as processing to prevent other workers from taking it
        cursor.execute(
            """
            UPDATE jobs
            SET status = 'processing',
                started_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (job_id,),
        )

        conn.commit()  # Release the lock

        # Return job with defaults for missing values
        return {
            "id": job_id,
            "text": text,
            "voice": voice or "male",  # Default voice
            "background": background or "minecraft",  # Default background
            "estimated_duration": float(estimated_duration or 0.0),
        }

    except Exception:
        conn.rollback()  # Rollback on error to release the lock
        raise
