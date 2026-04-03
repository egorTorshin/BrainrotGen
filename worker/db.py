import sqlite3

DB_PATH = "/app/data/app.db"

def get_conn():
    return sqlite3.connect(
        DB_PATH,
        timeout=30,
        isolation_level=None,
        check_same_thread=False
    )