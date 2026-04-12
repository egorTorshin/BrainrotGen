import sqlite3
import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.workers import worker_subtitles

from src.workers.worker_subtitles import (
    run_subtitles_with_retry,
    mark_next_stage,
    mark_failed
)
from src.job_queue import fetch_and_lock_job


# --------------------
# FIXTURE DB
# --------------------
@pytest.fixture
def conn():
    conn = sqlite3.connect(":memory:")

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


# --------------------
# RETRY SUCCESS
# --------------------
def test_subtitles_retry_success(monkeypatch):
    from src.workers.worker_subtitles import run_subtitles_with_retry

    calls = {"n": 0}

    def fake_generate(text, audio_path, srt_path):
        calls["n"] += 1
        if calls["n"] < 2:
            raise Exception("fail")
        return None

    monkeypatch.setattr(
        "src.workers.worker_subtitles.generate_srt",
        fake_generate
    )

    job = {"id": "1", "text": "hello"}

    with patch("time.sleep"):  # ускоряем тест
        run_subtitles_with_retry(job, "audio.wav", "out.srt")

    assert calls["n"] == 2


# --------------------
# RETRY FAIL
# --------------------
def test_subtitles_retry_fail(monkeypatch):
    from src.workers.worker_subtitles import run_subtitles_with_retry

    def always_fail(*args, **kwargs):
        raise Exception("fail")

    monkeypatch.setattr(
        "src.workers.worker_subtitles.generate_srt",
        always_fail
    )

    job = {"id": "1", "text": "hello"}

    with patch("time.sleep"):
        with pytest.raises(Exception, match="fail"):
            run_subtitles_with_retry(job, "audio.wav", "out.srt")


# --------------------
# mark_next_stage merge JSON
# --------------------
def test_mark_next_stage_merge(conn):
    conn.execute("""
        INSERT INTO jobs (id, status, result_path)
        VALUES (?, ?, ?)
    """, ("job1", "subtitles", '{"a": 1}'))
    conn.commit()

    # Создаем мок для get_conn, который возвращает соединение
    # и НЕ закрывает его (или закрывает, но мы проверяем через другое соединение)
    def mock_get_conn():
        # Создаем новое соединение и копируем данные
        new_conn = sqlite3.connect(":memory:")
        conn.backup(new_conn)
        return new_conn

    with patch("src.workers.worker_subtitles.get_conn", side_effect=mock_get_conn):
        mark_next_stage("job1", {"b": 2})

    # Проверяем результат через оригинальное соединение
    row = conn.execute("""
        SELECT result_path FROM jobs WHERE id='job1'
    """).fetchone()

    data = json.loads(row[0])
    assert data == {"a": 1}


# --------------------
# mark_failed updates DB
# --------------------
def test_mark_failed(conn):
    conn.execute("""
        INSERT INTO jobs (id, status)
        VALUES (?, ?)
    """, ("job1", "subtitles"))
    conn.commit()

    # Создаем обертку для соединения, которая переопределяет close
    class ConnectionWrapper:
        def __init__(self, real_conn):
            self.real_conn = real_conn

        def cursor(self):
            return self.real_conn.cursor()

        def close(self):
            # Ничего не делаем при закрытии
            pass

        def __getattr__(self, name):
            # Все остальные методы передаем реальному соединению
            return getattr(self.real_conn, name)

    def mock_get_conn():
        return ConnectionWrapper(conn)

    with patch("src.workers.worker_subtitles.get_conn", side_effect=mock_get_conn):
        mark_failed("job1", Exception("boom"))

    # Проверяем результат
    row = conn.execute("""
        SELECT status, error FROM jobs WHERE id='job1'
    """).fetchone()

    assert row[0] == "failed"
    assert "boom" in row[1]

# --------------------
# fetch_and_lock_job basic
# --------------------
def test_fetch_and_lock_job(conn):
    conn.execute("""
        INSERT INTO jobs (id, text, status)
        VALUES (?, ?, ?)
    """, ("job1", "text", "subtitles"))
    conn.commit()

    job = fetch_and_lock_job(conn, status="subtitles")

    assert job["id"] == "job1"

    status = conn.execute(
        "SELECT status FROM jobs WHERE id='job1'"
    ).fetchone()[0]

    assert status == "processing"


# --------------------
# main pipeline integration (unit-level)
# --------------------
def test_subtitle_pipeline(conn, tmp_path, monkeypatch):
    # -------------------------
    # ARRANGE OUTPUT DIR
    # -------------------------
    original_output_dir = worker_subtitles.OUTPUT_DIR
    worker_subtitles.OUTPUT_DIR = tmp_path

    try:
        # -------------------------
        # INSERT JOB
        # -------------------------
        conn.execute("""
            INSERT INTO jobs (id, text, status, result_path)
            VALUES (?, ?, ?, ?)
        """, (
            "job1",
            "hello",
            "subtitles",
            json.dumps({"audio_path": "/tmp/audio.wav"})
        ))
        conn.commit()

        # -------------------------
        # MOCK SRT GENERATION
        # -------------------------
        def fake_srt(text, audio_path, srt_path):
            Path(srt_path).write_text("fake srt")

        monkeypatch.setattr(
            "src.workers.worker_subtitles.generate_srt",
            fake_srt
        )

        # Создаем обертку для соединения, которая предотвращает закрытие
        class ConnectionWrapper:
            def __init__(self, real_conn):
                self.real_conn = real_conn

            def cursor(self):
                return self.real_conn.cursor()

            def close(self):
                # Игнорируем закрытие
                pass

            def commit(self):
                self.real_conn.commit()

            def execute(self, sql, params=None):
                if params:
                    return self.real_conn.execute(sql, params)
                return self.real_conn.execute(sql)

            def __getattr__(self, name):
                # Все остальные методы передаем реальному соединению
                return getattr(self.real_conn, name)

        # Мокаем get_conn чтобы возвращал обертку
        def mock_get_conn():
            return ConnectionWrapper(conn)

        monkeypatch.setattr(
            "src.workers.worker_subtitles.get_conn",
            mock_get_conn
        )

        # -------------------------
        # STEP 1: fetch job (REAL DB)
        # -------------------------
        job = fetch_and_lock_job(conn, status="subtitles")

        assert job is not None
        assert job["id"] == "job1"

        temp = json.loads(job["result_path"])
        audio_path = temp["audio_path"]
        srt_path = tmp_path / "job1.srt"

        # -------------------------
        # STEP 2: RUN WORKER LOGIC
        # -------------------------
        worker_subtitles.run_subtitles_with_retry(
            job,
            audio_path,
            srt_path
        )

        # -------------------------
        # STEP 3: MARK NEXT STAGE
        # -------------------------
        worker_subtitles.mark_next_stage("job1", {
            "srt_path": str(srt_path)
        })

        # -------------------------
        # ASSERT DB STATE
        # -------------------------
        row = conn.execute("""
            SELECT result_path, status
            FROM jobs
            WHERE id='job1'
        """).fetchone()

        data = json.loads(row[0])

        assert data["audio_path"] == "/tmp/audio.wav"
        assert data["srt_path"] == str(srt_path)
        assert row[1] == "merge"

        # -------------------------
        # ASSERT FILE CREATED
        # -------------------------
        assert (tmp_path / "job1.srt").exists()

    finally:
        worker_subtitles.OUTPUT_DIR = original_output_dir