# tests/test_job_queue.py
import pytest
import sqlite3
from unittest.mock import patch, MagicMock
from src.job_queue import fetch_and_lock_job


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary SQLite DB for tests"""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))

    conn.execute("""
        CREATE TABLE jobs (
            id TEXT PRIMARY KEY,
            text TEXT NOT NULL,
            voice TEXT,
            background TEXT,
            estimated_duration REAL,
            status TEXT DEFAULT 'queued',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            finished_at TIMESTAMP,
            result_path TEXT,
            error TEXT
        )
    """)
    conn.commit()

    yield conn
    conn.close()


@pytest.fixture
def mock_conn(temp_db):
    """Real SQLite connection backed by temp_db"""
    return temp_db


def test_fetch_and_lock_job_returns_none_when_no_jobs(mock_conn):
    """Empty queue returns None"""
    result = fetch_and_lock_job(mock_conn)
    assert result is None


def test_fetch_and_lock_job_returns_oldest_queued_job(mock_conn):
    """Returns the oldest job with status 'queued'"""
    mock_conn.execute(
        "INSERT INTO jobs (id, text, voice, background, estimated_duration, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("job1", "Text 1", "male", "minecraft", 10.0, "queued", "2024-01-01 10:00:00")
    )
    mock_conn.execute(
        "INSERT INTO jobs (id, text, voice, background, estimated_duration, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("job2", "Text 2", "female", "subway", 20.0, "queued", "2024-01-01 10:05:00")
    )
    mock_conn.execute(
        "INSERT INTO jobs (id, text, voice, background, estimated_duration, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("job3", "Text 3", "male", "minecraft", 15.0, "processing", "2024-01-01 09:00:00")
    )
    mock_conn.commit()

    job = fetch_and_lock_job(mock_conn)

    assert job is not None
    assert job["id"] == "job1"
    assert job["text"] == "Text 1"
    assert job["voice"] == "male"
    assert job["background"] == "minecraft"
    assert job["estimated_duration"] == 10.0


def test_fetch_and_lock_job_updates_status_to_processing(mock_conn):
    """Fetched job is marked as 'processing'"""
    mock_conn.execute(
        "INSERT INTO jobs (id, text, status) VALUES (?, ?, ?)",
        ("job1", "Test text", "queued")
    )
    mock_conn.commit()

    fetch_and_lock_job(mock_conn)

    cursor = mock_conn.cursor()
    cursor.execute("SELECT status, started_at FROM jobs WHERE id = ?", ("job1",))
    status, started_at = cursor.fetchone()

    assert status == "processing"
    assert started_at is not None


def test_fetch_and_lock_job_uses_transaction(mock_conn):
    """Verifies transactional behavior (BEGIN IMMEDIATE)"""
    mock_conn.execute(
        "INSERT INTO jobs (id, text, status) VALUES (?, ?, ?)",
        ("test_transaction", "Test", "queued")
    )
    mock_conn.commit()

    job = fetch_and_lock_job(mock_conn)

    assert job is not None
    assert job["id"] == "test_transaction"

    cursor = mock_conn.cursor()
    cursor.execute("SELECT status FROM jobs WHERE id = ?", ("test_transaction",))
    status = cursor.fetchone()[0]
    assert status == "processing"


def test_fetch_and_lock_job_rollback_on_error():
    """Error during fetch triggers a rollback"""
    import tempfile
    import os

    fd, db_path = tempfile.mkstemp()
    os.close(fd)
    test_conn = sqlite3.connect(db_path)

    try:
        test_conn.execute("""
            CREATE TABLE jobs (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                voice TEXT,
                background TEXT,
                estimated_duration REAL,
                status TEXT DEFAULT 'queued',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                finished_at TIMESTAMP,
                result_path TEXT,
                error TEXT
            )
        """)
        test_conn.commit()

        test_conn.execute(
            "INSERT INTO jobs (id, text, status) VALUES (?, ?, ?)",
            ("job1", "Test", "queued")
        )
        test_conn.commit()

        cursor = test_conn.cursor()
        cursor.execute("SELECT status FROM jobs WHERE id = ?", ("job1",))
        assert cursor.fetchone()[0] == "queued"

        job = fetch_and_lock_job(test_conn)

        assert job is not None
        assert job["id"] == "job1"

        cursor.execute("SELECT status FROM jobs WHERE id = ?", ("job1",))
        status = cursor.fetchone()[0]
        assert status == "processing"

    finally:
        test_conn.close()
        os.unlink(db_path)


def test_fetch_and_lock_job_default_values(mock_conn):
    """NULL voice/background/duration get sensible defaults"""
    mock_conn.execute(
        "INSERT INTO jobs (id, text) VALUES (?, ?)",
        ("job1", "Test text")
    )
    mock_conn.commit()

    job = fetch_and_lock_job(mock_conn)

    assert job["voice"] == "male"
    assert job["background"] == "minecraft"
    assert job["estimated_duration"] == 0.0


def test_fetch_and_lock_job_handles_null_estimated_duration(mock_conn):
    """NULL estimated_duration is converted to 0.0"""
    mock_conn.execute(
        "INSERT INTO jobs (id, text, estimated_duration) VALUES (?, ?, ?)",
        ("job1", "Test", None)
    )
    mock_conn.commit()

    job = fetch_and_lock_job(mock_conn)
    assert job["estimated_duration"] == 0.0
