import sqlite3
import os

os.makedirs("data", exist_ok=True)

conn = sqlite3.connect("data/app.db")

conn.execute("""
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    text TEXT,
    status TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME,
    finished_at DATETIME,
    result_path TEXT,
    error TEXT
);
""")

conn.commit()
conn.close()

print("DB created")