def fetch_and_lock_job(conn):
    cursor = conn.cursor()

    try:
        cursor.execute("BEGIN IMMEDIATE")

        cursor.execute("""
            SELECT id, text
            FROM jobs
            WHERE status = 'queued'
            ORDER BY created_at
            LIMIT 1
        """)
        row = cursor.fetchone()

        if not row:
            conn.commit()
            return None

        job_id, text = row

        cursor.execute("""
            UPDATE jobs
            SET status = 'processing',
                started_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """ , (job_id,))

        conn.commit()

        return {
            "id": job_id,
            "text": text
        }

    except:
        conn.rollback()
        raise