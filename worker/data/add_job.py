import sqlite3

conn = sqlite3.connect("data/app.db")

conn.execute("""
INSERT INTO jobs (id, text, status)
VALUES (?, ?, ?)
""", (
    "job9",
    "This is a test brainrot video from Windows",
    "queued"
))

conn.commit()
conn.close()

print("Job added")