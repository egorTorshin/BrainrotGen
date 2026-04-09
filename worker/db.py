import os
import sqlite3

# Same SQLite file as FastAPI (see backend SQLITE_FILE / data/app.db).
DB_PATH = os.environ.get("SQLITE_PATH", "/app/data/app.db")


def get_conn():
    return sqlite3.connect(
        DB_PATH,
        timeout=30,
        isolation_level=None,
        check_same_thread=False
    )