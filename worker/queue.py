def fetch_and_lock_job(conn):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, text
        FROM jobs
        WHERE status = 'queued'
        ORDER BY created_at
        LIMIT 1
    """)
    row = cursor.fetchone()

    if not row:
        return None

    job_id, text = row

    cursor.execute("""
        UPDATE jobs
        SET status = 'processing',
            started_at = CURRENT_TIMESTAMP
        WHERE id = ? AND status = 'queued'
    """, (job_id,))

    if cursor.rowcount == 0:
        return None

    conn.commit()

    return {
        "id": job_id,
        "text": text
    }
