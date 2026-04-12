import sqlite3
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.workers import worker_render
from src.workers.worker_render import (
    run_render_with_retry,
    mark_failed,
    mark_done,
    main
)
from src.job_queue import fetch_and_lock_job


# --------------------
# FIXTURES
# --------------------
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


@pytest.fixture
def sample_job_data():
    return {
        "audio_path": "/app/audio/job1.wav",
        "srt_path": "/app/subtitles/job1.srt"
    }


# --------------------
# TESTS FOR run_render_with_retry
# --------------------
def test_render_retry_success(monkeypatch):
    """Test that render succeeds after retries"""
    calls = {"n": 0}

    def fake_merge(video_path, audio_path, srt_path, output_path):
        calls["n"] += 1
        if calls["n"] < 2:
            raise Exception("fail")
        return None

    monkeypatch.setattr(
        "src.workers.worker_render.merge_video_audio_subs",
        fake_merge
    )

    with patch("time.sleep"):
        result = run_render_with_retry(
            "video.mp4",
            "audio.wav",
            "subs.srt",
            "output.mp4"
        )

    assert calls["n"] == 2
    assert result == "output.mp4"


def test_render_retry_fail(monkeypatch):
    """Test that render fails after all retries"""

    def always_fail(*args, **kwargs):
        raise Exception("render failed")

    monkeypatch.setattr(
        "src.workers.worker_render.merge_video_audio_subs",
        always_fail
    )

    with patch("time.sleep"):
        with pytest.raises(Exception, match="render failed"):
            run_render_with_retry(
                "video.mp4",
                "audio.wav",
                "subs.srt",
                "output.mp4"
            )


def test_render_success_first_try(monkeypatch):
    """Test that render succeeds on first try"""
    mock_merge = MagicMock()
    monkeypatch.setattr(
        "src.workers.worker_render.merge_video_audio_subs",
        mock_merge
    )

    result = run_render_with_retry(
        "video.mp4",
        "audio.wav",
        "subs.srt",
        "output.mp4"
    )

    mock_merge.assert_called_once_with(
        "video.mp4",
        "audio.wav",
        "subs.srt",
        "output.mp4"
    )
    assert result == "output.mp4"


# --------------------
# TESTS FOR mark_failed
# --------------------
def test_mark_failed_updates_database(conn):
    """Test that mark_failed correctly updates job status"""
    conn.execute("""
        INSERT INTO jobs (id, status)
        VALUES (?, ?)
    """, ("job1", "merge"))
    conn.commit()

    def mock_get_conn():
        return conn

    with patch("src.workers.worker_render.get_conn", side_effect=mock_get_conn):
        with patch.object(sqlite3.Connection, 'close', return_value=None):
            mark_failed("job1", Exception("render error"))

    row = conn.execute("""
        SELECT status, error FROM jobs WHERE id='job1'
    """).fetchone()

    assert row[0] == "failed"
    assert "render error" in row[1]


def test_mark_failed_with_string_error(conn):
    """Test mark_failed with string error"""
    conn.execute("""
        INSERT INTO jobs (id, status)
        VALUES (?, ?)
    """, ("job1", "merge"))
    conn.commit()

    def mock_get_conn():
        return conn

    with patch("src.workers.worker_render.get_conn", side_effect=mock_get_conn):
        with patch.object(sqlite3.Connection, 'close', return_value=None):
            mark_failed("job1", "custom error message")

    row = conn.execute("""
        SELECT status, error FROM jobs WHERE id='job1'
    """).fetchone()

    assert row[0] == "failed"
    assert "custom error message" in row[1]


def test_mark_failed_nonexistent_job(conn):
    """Test mark_failed with non-existent job"""

    def mock_get_conn():
        return conn

    with patch("src.workers.worker_render.get_conn", side_effect=mock_get_conn):
        with patch.object(sqlite3.Connection, 'close', return_value=None):
            # Should not raise exception
            mark_failed("nonexistent", Exception("error"))


# --------------------
# TESTS FOR mark_failed
# --------------------
def test_mark_failed_updates_database(conn):
    """Test that mark_failed correctly updates job status"""
    conn.execute("""
        INSERT INTO jobs (id, status)
        VALUES (?, ?)
    """, ("job1", "merge"))
    conn.commit()

    # Create connection wrapper to prevent closing
    class ConnectionWrapper:
        def __init__(self, real_conn):
            self.real_conn = real_conn

        def cursor(self):
            return self.real_conn.cursor()

        def close(self):
            # Ignore close
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

    with patch("src.workers.worker_render.get_conn", side_effect=mock_get_conn):
        mark_failed("job1", Exception("render error"))

    row = conn.execute("""
        SELECT status, error FROM jobs WHERE id='job1'
    """).fetchone()

    assert row[0] == "failed"
    assert "render error" in row[1]


def test_mark_failed_with_string_error(conn):
    """Test mark_failed with string error"""
    conn.execute("""
        INSERT INTO jobs (id, status)
        VALUES (?, ?)
    """, ("job1", "merge"))
    conn.commit()

    # Create connection wrapper to prevent closing
    class ConnectionWrapper:
        def __init__(self, real_conn):
            self.real_conn = real_conn

        def cursor(self):
            return self.real_conn.cursor()

        def close(self):
            # Ignore close
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

    with patch("src.workers.worker_render.get_conn", side_effect=mock_get_conn):
        mark_failed("job1", "custom error message")

    row = conn.execute("""
        SELECT status, error FROM jobs WHERE id='job1'
    """).fetchone()

    assert row[0] == "failed"
    assert "custom error message" in row[1]


def test_mark_failed_nonexistent_job(conn):
    """Test mark_failed with non-existent job"""

    # Create connection wrapper to prevent closing
    class ConnectionWrapper:
        def __init__(self, real_conn):
            self.real_conn = real_conn

        def cursor(self):
            return self.real_conn.cursor()

        def close(self):
            # Ignore close
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

    with patch("src.workers.worker_render.get_conn", side_effect=mock_get_conn):
        # Should not raise exception
        mark_failed("nonexistent", Exception("error"))


# --------------------
# TESTS FOR mark_done
# --------------------
def test_mark_done_updates_database(conn):
    """Test that mark_done correctly updates job status"""
    conn.execute("""
        INSERT INTO jobs (id, status)
        VALUES (?, ?)
    """, ("job1", "merge"))
    conn.commit()

    # Create connection wrapper to prevent closing
    class ConnectionWrapper:
        def __init__(self, real_conn):
            self.real_conn = real_conn

        def cursor(self):
            return self.real_conn.cursor()

        def close(self):
            # Ignore close
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

    with patch("src.workers.worker_render.get_conn", side_effect=mock_get_conn):
        mark_done("job1", "/app/output/job1.mp4")

    row = conn.execute("""
        SELECT status, result_path, finished_at
        FROM jobs
        WHERE id='job1'
    """).fetchone()

    assert row[0] == "done"
    assert row[1] == "/app/output/job1.mp4"
    assert row[2] is not None  # finished_at should be set


def test_mark_done_with_existing_result_path(conn, sample_job_data):
    """Test mark_done when result_path already has data"""
    conn.execute("""
        INSERT INTO jobs (id, status, result_path)
        VALUES (?, ?, ?)
    """, ("job1", "merge", json.dumps(sample_job_data)))
    conn.commit()

    # Create connection wrapper to prevent closing
    class ConnectionWrapper:
        def __init__(self, real_conn):
            self.real_conn = real_conn

        def cursor(self):
            return self.real_conn.cursor()

        def close(self):
            # Ignore close
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

    with patch("src.workers.worker_render.get_conn", side_effect=mock_get_conn):
        mark_done("job1", "/app/output/job1.mp4")

    row = conn.execute("""
        SELECT status, result_path FROM jobs WHERE id='job1'
    """).fetchone()

    assert row[0] == "done"
    # result_path should be replaced with output path
    assert row[1] == "/app/output/job1.mp4"


# --------------------
# TESTS FOR fetch_and_lock_job with merge status
# --------------------
@pytest.fixture
def mock_conn_wrapper(conn):
    """Fixture that mocks get_conn to return a wrapper that ignores close()"""

    class ConnectionWrapper:
        def __init__(self, real_conn):
            self.real_conn = real_conn

        def cursor(self):
            return self.real_conn.cursor()

        def close(self):
            # Ignore close
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

    with patch("src.workers.worker_render.get_conn", side_effect=mock_get_conn):
        yield


# Then you can simplify tests like this:
def test_mark_failed_updates_database_refactored(conn, mock_conn_wrapper):
    """Test that mark_failed correctly updates job status"""
    conn.execute("""
        INSERT INTO jobs (id, status)
        VALUES (?, ?)
    """, ("job1", "merge"))
    conn.commit()

    mark_failed("job1", Exception("render error"))

    row = conn.execute("""
        SELECT status, error FROM jobs WHERE id='job1'
    """).fetchone()

    assert row[0] == "failed"
    assert "render error" in row[1]


def test_fetch_and_lock_job_no_jobs(conn):
    """Test fetching when no jobs available"""
    job = fetch_and_lock_job(conn, status="merge")
    assert job is None


# --------------------
# INTEGRATION TESTS
# --------------------
def test_render_pipeline_success(conn, tmp_path, monkeypatch):
    """Full pipeline test for render worker"""
    # Setup
    original_output_dir = worker_render.OUTPUT_DIR if hasattr(worker_render, 'OUTPUT_DIR') else None
    worker_render.OUTPUT_DIR = tmp_path

    try:
        # Insert job
        job_data = {
            "audio_path": str(tmp_path / "audio.wav"),
            "srt_path": str(tmp_path / "subs.srt")
        }

        conn.execute("""
            INSERT INTO jobs (id, text, background, status, result_path)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "job1",
            "hello world",
            "forest",
            "merge",
            json.dumps(job_data)
        ))
        conn.commit()

        # Mock dependencies
        mock_merge = MagicMock()
        monkeypatch.setattr(
            "src.workers.worker_render.merge_video_audio_subs",
            mock_merge
        )

        mock_pick_background = MagicMock(return_value=str(tmp_path / "background.mp4"))
        monkeypatch.setattr(
            "src.workers.worker_render.pick_background_video",
            mock_pick_background
        )

        mock_assets_root = MagicMock(return_value=tmp_path)
        monkeypatch.setattr(
            "src.workers.worker_render.assets_root_from_env",
            mock_assets_root
        )

        # Create connection wrapper to prevent closing
        class ConnectionWrapper:
            def __init__(self, real_conn):
                self.real_conn = real_conn

            def cursor(self):
                return self.real_conn.cursor()

            def close(self):
                # Ignore close
                pass

            def commit(self):
                self.real_conn.commit()

            def execute(self, sql, params=None):
                if params:
                    return self.real_conn.execute(sql, params)
                return self.real_conn.execute(sql)

            def __getattr__(self, name):
                return getattr(self.real_conn, name)

        # Mock get_conn to return wrapper
        def mock_get_conn():
            return ConnectionWrapper(conn)

        monkeypatch.setattr(
            "src.workers.worker_render.get_conn",
            mock_get_conn
        )

        # Fetch job
        job = fetch_and_lock_job(conn, status="merge")
        assert job is not None

        # Process job
        temp = json.loads(job["result_path"])
        audio_path = Path(temp["audio_path"])
        srt_path = Path(temp["srt_path"])

        assets_root = mock_assets_root()
        video_path = mock_pick_background(assets_root, job["background"])
        output_path = Path(f"/app/output/{job['id']}.mp4")

        # Run render
        result = run_render_with_retry(
            video_path,
            audio_path,
            srt_path,
            output_path
        )

        # Mark done
        mark_done(job["id"], result)

        # Assertions
        row = conn.execute("""
            SELECT status, result_path FROM jobs WHERE id='job1'
        """).fetchone()

        assert row[0] == "done"
        assert row[1] == str(output_path)

        mock_merge.assert_called_once()
        mock_pick_background.assert_called_once()

    finally:
        if original_output_dir:
            worker_render.OUTPUT_DIR = original_output_dir


def test_render_pipeline_failure(conn, tmp_path, monkeypatch):
    """Test render pipeline when rendering fails"""
    # Insert job
    job_data = {
        "audio_path": str(tmp_path / "audio.wav"),
        "srt_path": str(tmp_path / "subs.srt")
    }

    conn.execute("""
        INSERT INTO jobs (id, text, background, status, result_path)
        VALUES (?, ?, ?, ?, ?)
    """, (
        "job1",
        "hello world",
        "forest",
        "merge",
        json.dumps(job_data)
    ))
    conn.commit()

    # Mock merge to fail
    def failing_merge(*args, **kwargs):
        raise Exception("render failed")

    monkeypatch.setattr(
        "src.workers.worker_render.merge_video_audio_subs",
        failing_merge
    )

    mock_pick_background = MagicMock(return_value=str(tmp_path / "background.mp4"))
    monkeypatch.setattr(
        "src.workers.worker_render.pick_background_video",
        mock_pick_background
    )

    mock_assets_root = MagicMock(return_value=tmp_path)
    monkeypatch.setattr(
        "src.workers.worker_render.assets_root_from_env",
        mock_assets_root
    )

    # Create connection wrapper to prevent closing
    class ConnectionWrapper:
        def __init__(self, real_conn):
            self.real_conn = real_conn

        def cursor(self):
            return self.real_conn.cursor()

        def close(self):
            # Ignore close
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

    monkeypatch.setattr(
        "src.workers.worker_render.get_conn",
        mock_get_conn
    )

    # Fetch job
    job = fetch_and_lock_job(conn, status="merge")
    assert job is not None

    # Process and expect failure
    try:
        temp = json.loads(job["result_path"])
        audio_path = Path(temp["audio_path"])
        srt_path = Path(temp["srt_path"])

        assets_root = mock_assets_root()
        video_path = mock_pick_background(assets_root, job["background"])
        output_path = Path(f"/app/output/{job['id']}.mp4")

        run_render_with_retry(video_path, audio_path, srt_path, output_path)
    except Exception as e:
        mark_failed(job["id"], e)

    # Check that job is marked as failed
    row = conn.execute("""
        SELECT status, error FROM jobs WHERE id='job1'
    """).fetchone()

    assert row[0] == "failed"
    assert "render failed" in row[1]


def test_render_pipeline_missing_audio_path(conn, tmp_path, monkeypatch):
    """Test render pipeline when audio_path is missing from result_path"""
    # Insert job with missing audio_path
    conn.execute("""
        INSERT INTO jobs (id, text, background, status, result_path)
        VALUES (?, ?, ?, ?, ?)
    """, (
        "job1",
        "hello world",
        "forest",
        "merge",
        json.dumps({"srt_path": "/tmp/subs.srt"})  # missing audio_path
    ))
    conn.commit()

    # Create connection wrapper to prevent closing
    class ConnectionWrapper:
        def __init__(self, real_conn):
            self.real_conn = real_conn

        def cursor(self):
            return self.real_conn.cursor()

        def close(self):
            # Ignore close
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

    monkeypatch.setattr(
        "src.workers.worker_render.get_conn",
        mock_get_conn
    )

    # Fetch job
    job = fetch_and_lock_job(conn, status="merge")
    assert job is not None

    # Process job - should fail due to missing audio_path
    with pytest.raises(KeyError):
        temp = json.loads(job["result_path"])
        audio_path = Path(temp["audio_path"])  # This should raise KeyError


def test_render_pipeline_empty_result_path(conn, monkeypatch):
    """Test render pipeline when result_path is empty"""
    # Insert job with empty result_path
    conn.execute("""
        INSERT INTO jobs (id, text, background, status, result_path)
        VALUES (?, ?, ?, ?, ?)
    """, (
        "job1",
        "hello world",
        "forest",
        "merge",
        None
    ))
    conn.commit()

    # Create connection wrapper to prevent closing
    class ConnectionWrapper:
        def __init__(self, real_conn):
            self.real_conn = real_conn

        def cursor(self):
            return self.real_conn.cursor()

        def close(self):
            # Ignore close
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

    monkeypatch.setattr(
        "src.workers.worker_render.get_conn",
        mock_get_conn
    )

    # Fetch job
    job = fetch_and_lock_job(conn, status="merge")
    assert job is not None

    # This should not raise exception (uses {} as default)
    temp = json.loads(job.get("result_path") or "{}")
    assert temp == {}


# --------------------
# EDGE CASES
# --------------------
def test_run_render_with_retry_invalid_paths(monkeypatch):
    """Test render with invalid paths"""

    def fake_merge(video_path, audio_path, srt_path, output_path):
        raise FileNotFoundError("File not found")

    monkeypatch.setattr(
        "src.workers.worker_render.merge_video_audio_subs",
        fake_merge
    )

    with patch("time.sleep"):
        with pytest.raises(FileNotFoundError):
            run_render_with_retry(
                "nonexistent.mp4",
                "nonexistent.wav",
                "nonexistent.srt",
                "output.mp4"
            )