"""Print job rows from the shared SQLite file (debug)."""

import os
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent / "app.db"

conn = sqlite3.connect(os.fspath(DB))

rows = conn.execute(
    """
    SELECT id, status, result_path, error
    FROM jobs
    """
).fetchall()

for r in rows:
    print(r)

conn.close()
