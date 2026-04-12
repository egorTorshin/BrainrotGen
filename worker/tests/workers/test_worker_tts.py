import sqlite3
import json
import pytest
from unittest.mock import patch

from src.workers.worker_tts import (
    run_tts_with_retry,
    mark_next_stage,
    mark_failed
)
from src.job_queue import fetch_and_lock_job


@pytest.fixture
def conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    conn.execute("""
        CREATE TABLE jobs (
            id TEXT PRIMARY KEY,
            text TEXT,
            voice TEXT,
            background TEXT,
            estimated_duration REAL,
            status TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            started_at TEXT,
            finished_at TEXT,
            result_path TEXT,
            error TEXT
        )
    """)

    yield conn
    conn.close()


def test_tts_retry_success_after_fail():
    job = {"id": "1", "text": "hello", "voice": "male"}

    calls = {"n": 0}

    def fake_tts(text, voice, job_id, out_dir=None):
        calls["n"] += 1
        if calls["n"] < 2:
            raise Exception("fail")
        return "/tmp/audio.wav"

    with patch("src.workers.worker_tts.text_to_speech", side_effect=fake_tts):
        result = run_tts_with_retry(job)

    assert result == "/tmp/audio.wav"
    assert calls["n"] == 2


def test_mark_next_stage_creates_json(conn):
    conn.execute("""
        INSERT INTO jobs (id, text, status, result_path)
        VALUES (?, ?, ?, ?)
    """, ("job1", "hello", "cutting", json.dumps({"old": "value"})))
    conn.commit()

    # Create connection wrapper to prevent closing
    class ConnectionWrapper:
        def __init__(self, real_conn):
            self.real_conn = real_conn

        def cursor(self):
            return self.real_conn.cursor()

        def close(self):
            # Ignore close - prevents the real connection from being closed
            pass

        def commit(self):
            self.real_conn.commit()

        def execute(self, sql, params=None):
            if params:
                return self.real_conn.execute(sql, params)
            return self.real_conn.execute(sql)

        def __getattr__(self, name):
            return getattr(self.real_conn, name)

    def mock_get_conn():
        return ConnectionWrapper(conn)

    with patch("src.workers.worker_tts.get_conn", side_effect=mock_get_conn):
        mark_next_stage("job1", {"audio_path": "/tmp/audio.wav"})

    row = conn.execute(
        "SELECT result_path FROM jobs WHERE id='job1'"
    ).fetchone()

    data = json.loads(row[0])

    assert data["old"] == "value"
    assert data["audio_path"] == "/tmp/audio.wav"


def test_mark_next_stage_empty_state(conn):
    conn.execute("""
        INSERT INTO jobs (id, text, status)
        VALUES (?, ?, ?)
    """, ("job1", "hello", "cutting"))
    conn.commit()

    # Create connection wrapper to prevent closing
    class ConnectionWrapper:
        def __init__(self, real_conn):
            self.real_conn = real_conn

        def cursor(self):
            return self.real_conn.cursor()

        def close(self):
            # Ignore close - prevents the real connection from being closed
            pass

        def commit(self):
            self.real_conn.commit()

        def execute(self, sql, params=None):
            if params:
                return self.real_conn.execute(sql, params)
            return self.real_conn.execute(sql)

        def __getattr__(self, name):
            return getattr(self.real_conn, name)

    def mock_get_conn():
        return ConnectionWrapper(conn)

    with patch("src.workers.worker_tts.get_conn", side_effect=mock_get_conn):
        mark_next_stage("job1", {"audio_path": "/tmp/audio.wav"})

    row = conn.execute(
        "SELECT result_path FROM jobs WHERE id='job1'"
    ).fetchone()

    data = json.loads(row[0])

    assert data == {"audio_path": "/tmp/audio.wav"}


def test_fetch_and_lock_job_basic(conn):
    conn.execute("""
        INSERT INTO jobs (id, text, voice, background, estimated_duration, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ("job1", "text", "male", "minecraft", 10.0, "queued"))
    conn.commit()

    job = fetch_and_lock_job(conn, status="queued")

    assert job["id"] == "job1"

    status = conn.execute(
        "SELECT status FROM jobs WHERE id='job1'"
    ).fetchone()[0]

    assert status == "processing"


def test_fetch_and_lock_job_none(conn):
    job = fetch_and_lock_job(conn, status="queued")
    assert job is None


def test_full_tts_pipeline(conn):
    conn.execute("""
        INSERT INTO jobs (id, text, voice, status)
        VALUES (?, ?, ?, ?)
    """, ("job1", "hello", "male", "queued"))
    conn.commit()

    fake_audio = "/tmp/audio.wav"

    # Create connection wrapper to prevent closing
    class ConnectionWrapper:
        def __init__(self, real_conn):
            self.real_conn = real_conn

        def cursor(self):
            return self.real_conn.cursor()

        def close(self):
            # Ignore close - prevents the real connection from being closed
            pass

        def commit(self):
            self.real_conn.commit()

        def execute(self, sql, params=None):
            if params:
                return self.real_conn.execute(sql, params)
            return self.real_conn.execute(sql)

        def __getattr__(self, name):
            # Forward all other attributes to the real connection
            return getattr(self.real_conn, name)

    def mock_get_conn():
        return ConnectionWrapper(conn)

    with patch("src.workers.worker_tts.text_to_speech", return_value=fake_audio):
        with patch("src.workers.worker_tts.get_conn", side_effect=mock_get_conn):
            job = fetch_and_lock_job(conn, status="queued")

            audio = run_tts_with_retry(job)

            assert audio == fake_audio

            mark_next_stage(job["id"], {"audio_path": audio})

    row = conn.execute(
        "SELECT result_path FROM jobs WHERE id='job1'"
    ).fetchone()

    data = json.loads(row[0])

    assert data["audio_path"] == fake_audio


def test_run_tts_retry_success(monkeypatch):
    calls = {"n": 0}

    def fake_tts(text, voice, job_id, out_dir=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise Exception("fail")
        return "/tmp/audio.wav"

    monkeypatch.setattr(
        "src.workers.worker_tts.text_to_speech",
        fake_tts
    )

    job = {"id": "1", "text": "hi", "voice": "male"}

    result = run_tts_with_retry(job)

    assert result == "/tmp/audio.wav"
    assert calls["n"] == 2


def test_run_tts_retry_fail(monkeypatch):
    def always_fail(*args, **kwargs):
        raise Exception("fail")

    monkeypatch.setattr(
        "src.workers.worker_tts.text_to_speech",
        always_fail
    )

    job = {"id": "1", "text": "hi", "voice": "male"}

    with pytest.raises(Exception, match="fail"):
        run_tts_with_retry(job)


def test_mark_next_stage_merge(conn):
    conn.execute("""
        INSERT INTO jobs (id, status, result_path)
        VALUES (?, ?, ?)
    """, ("job1", "queued", '{"a": 1}'))
    conn.commit()

    # Create connection wrapper to prevent closing
    class ConnectionWrapper:
        def __init__(self, real_conn):
            self.real_conn = real_conn

        def cursor(self):
            return self.real_conn.cursor()

        def close(self):
            # Ignore close - prevents the real connection from being closed
            pass

        def commit(self):
            self.real_conn.commit()

        def execute(self, sql, params=None):
            if params:
                return self.real_conn.execute(sql, params)
            return self.real_conn.execute(sql)

        def __getattr__(self, name):
            # Forward all other attributes to the real connection
            return getattr(self.real_conn, name)

    def mock_get_conn():
        return ConnectionWrapper(conn)

    with patch("src.workers.worker_tts.get_conn", side_effect=mock_get_conn):
        mark_next_stage("job1", {"b": 2})

    row = conn.execute("""
        SELECT result_path FROM jobs WHERE id='job1'
    """).fetchone()

    data = json.loads(row[0])

    assert data == {"a": 1, "b": 2}


def test_fetch_and_lock_job_sets_processing(conn):
    conn.execute("""
        INSERT INTO jobs (id, text, status)
        VALUES (?, ?, ?)
    """, ("job1", "text", "queued"))
    conn.commit()

    job = fetch_and_lock_job(conn, status="queued")

    assert job["id"] == "job1"

    row = conn.execute("""
        SELECT status FROM jobs WHERE id='job1'
    """).fetchone()

    assert row[0] == "processing"


# Additional test for mark_failed
def test_mark_failed_updates_database(conn):
    conn.execute("""
        INSERT INTO jobs (id, status)
        VALUES (?, ?)
    """, ("job1", "queued"))
    conn.commit()

    # Create connection wrapper to prevent closing
    class ConnectionWrapper:
        def __init__(self, real_conn):
            self.real_conn = real_conn

        def cursor(self):
            return self.real_conn.cursor()

        def close(self):
            # Ignore close - prevents the real connection from being closed
            pass

        def commit(self):
            self.real_conn.commit()

        def execute(self, sql, params=None):
            if params:
                return self.real_conn.execute(sql, params)
            return self.real_conn.execute(sql)

        def __getattr__(self, name):
            # Forward all other attributes to the real connection
            return getattr(self.real_conn, name)

    def mock_get_conn():
        return ConnectionWrapper(conn)

    with patch("src.workers.worker_tts.get_conn", side_effect=mock_get_conn):
        mark_failed("job1", Exception("TTS error"))

    row = conn.execute("""
        SELECT status, error FROM jobs WHERE id='job1'
    """).fetchone()

    assert row[0] == "failed"
    assert "TTS error" in row[1]