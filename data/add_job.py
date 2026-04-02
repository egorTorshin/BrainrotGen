import sqlite3

conn = sqlite3.connect("data/app.db")

conn.execute("""
INSERT INTO jobs (id, text, status)
VALUES (?, ?, ?)
""", (
    "job2",
    "I've seen slime blocks with better coordination than me. At this point, the void isn't my enemy — it's my emotional support pit. Please send more than just arrows; send a ladder to my dignity.",
    "queued"
))

conn.commit()
conn.close()

print("Job added")