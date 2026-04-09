"""
Legacy helper: optional SQLite PRAGMAs on an existing database file.

The canonical schema is created by the FastAPI app (SQLAlchemy ``create_all``).
Run the backend once before using the worker, or use ``docker compose up backend``.

Do not use this script to CREATE TABLE — it will conflict with the ORM schema.
"""

import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT / "app.db"


def main() -> None:
    if not DB.exists():
        print(
            f"No database at {DB}. Start the backend first to create tables, "
            "or copy a migrated app.db here.",
        )
        return
    conn = sqlite3.connect(os.fspath(DB))
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.commit()
        print(f"Applied PRAGMA on existing {DB}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
