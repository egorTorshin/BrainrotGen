def fetch_and_lock_job(conn):
    cursor = conn.cursor()

    try:
        cursor.execute("BEGIN IMMEDIATE")

        cursor.execute(
            """
            SELECT id, text, voice, background, estimated_duration
            FROM jobs
            WHERE status = 'queued'
            ORDER BY created_at
            LIMIT 1
            """
        )
        row = cursor.fetchone()

        if not row:
            conn.commit()
            return None

        job_id, text, voice, background, estimated_duration = row

        cursor.execute(
            """
            UPDATE jobs
            SET status = 'processing',
                started_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (job_id,),
        )

        conn.commit()

        return {
            "id": job_id,
            "text": text,
            "voice": voice or "male",
            "background": background or "minecraft",
            "estimated_duration": float(estimated_duration or 0.0),
        }

    except Exception:
        conn.rollback()
        raise
