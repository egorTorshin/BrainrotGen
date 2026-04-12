import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "app.db"


def check():

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    rows = cursor.execute("""
    SELECT * FROM jobs
    """).fetchall()

    for r in rows:
        print(r)

    conn.close()

if __name__ == "__main__":
    check()