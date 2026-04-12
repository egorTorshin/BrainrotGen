import sqlite3

conn = sqlite3.connect("data/app.db")

rows = conn.execute("""
SELECT id, status, result_path, error FROM jobs
""").fetchall()

for r in rows:
    print(r)

conn.close()