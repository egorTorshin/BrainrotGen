# add_job_direct.py
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "app.db"


def add_job(text: str, voice: str = "male", background: str = "minecraft", user_id: int = 1):
    """Add a job to the queue directly via SQLite"""
    job_id = str(uuid.uuid4())

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO jobs (
                id, user_id, text, voice, background, 
                status, created_at
            ) VALUES (?, ?, ?, ?, ?, 'queued', ?)
        """, (job_id, user_id, text, voice, background, datetime.now()))

        conn.commit()
        print(f"Job added successfully!")
        print(f"   ID: {job_id}")
        print(f"   Text: {text[:50]}...")
        return job_id
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def show_jobs(limit=5):
    """Show the most recent jobs"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, text, status, created_at 
        FROM jobs 
        ORDER BY created_at DESC 
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    print("\nRecent jobs:")
    for row in rows:
        print(f"   {row[0][:8]}... | {row[2]} | {row[3]} | {row[1][:30]}...")
    conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        add_job(text)
        show_jobs()
    else:
        text = input("Enter job text: ")
        add_job(text)
        show_jobs()
