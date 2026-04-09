"""
Manual enqueue helper for debugging only.

Prefer creating jobs via the FastAPI API (POST /api/v1/jobs) so quota and fields stay consistent.

Requires an existing ``app.db`` with the ORM schema (start backend once).
"""

import os
import sqlite3
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "app.db"


def add_job(text: str, job_id: str | None = None) -> str:
    jid = job_id or str(uuid.uuid4())
    conn = sqlite3.connect(os.fspath(DB_PATH), timeout=30)
    try:
        conn.execute(
            """
            INSERT INTO jobs (
                id, user_id, text, voice, background, status,
                estimated_duration, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                jid,
                None,
                text,
                "male",
                "minecraft",
                "queued",
                60.0,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return jid


if __name__ == "__main__":
    if not DB_PATH.exists():
        raise SystemExit(f"Missing {DB_PATH}; start the backend once to create the schema.")

    jid = add_job(
        "I've seen gold blocks with better coordination than me...",
    )
    print(f"Inserted job {jid}")
