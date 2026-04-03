import sqlite3

def add_job(job_id, text):
    conn = sqlite3.connect("data/app.db", timeout=30)
    try:
        conn.execute("""
        INSERT INTO jobs (id, text, status)
        VALUES (?, ?, ?)
        """, (job_id, text, "queued"))
        conn.commit()
    finally:
        conn.close()


add_job(
    "job8",
    "I've seen gold blocks with better coordination than me...",
)

print("Job added")