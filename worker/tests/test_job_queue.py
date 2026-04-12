import pytest
import sqlite3

from src.job_queue import fetch_and_lock_job


@pytest.fixture
def conn(tmp_path):
    db = tmp_path / "test.db"
    connection = sqlite3.connect(str(db))

    connection.execute("""
        CREATE TABLE jobs (
            id TEXT PRIMARY KEY,
            text TEXT,
            voice TEXT,
            background TEXT,
            estimated_duration REAL,
            status TEXT,
            created_at TEXT,
            started_at TEXT,
            finished_at TEXT,
            result_path TEXT,
            error TEXT
        )
    """)
    connection.commit()

    yield connection
    connection.close()