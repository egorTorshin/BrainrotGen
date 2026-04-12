# tests/test_process.py
import subprocess

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.process import process_job


@pytest.fixture
def mock_job():
    return {
        "id": "job-123",
        "text": "Hello brainrot world",
        "voice": "male",
        "background": "minecraft",
        "estimated_duration": 15.0,
    }


@pytest.fixture
def mock_db_conn():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    return conn


def test_process_job_success(mock_job, mock_db_conn, tmp_path):
    """Successful job processing writes 'done' status to DB"""
    mock_result_path = tmp_path / "output.mp4"
    mock_result_path.write_text("fake video content")

    with patch("src.process.get_conn", return_value=mock_db_conn):
        with patch("src.process.assets_root_from_env", return_value=tmp_path):
            with patch(
                "src.process.pick_background_video", return_value=tmp_path / "bg.mp4"
            ):
                with patch("src.process.run_pipeline", return_value=mock_result_path):
                    process_job(mock_job)

    mock_db_conn.cursor.return_value.execute.assert_called_once()
    call_args = mock_db_conn.cursor.return_value.execute.call_args[0]

    assert "UPDATE jobs" in call_args[0]
    assert "status = 'done'" in call_args[0]
    assert "actual_duration_seconds" in call_args[0]
    params = call_args[1]
    assert str(mock_result_path) in params
    assert mock_job["id"] in params
    assert 15.0 in params  # fallback from mock_job estimated_duration

    mock_db_conn.commit.assert_called_once()


def test_process_job_failure(mock_job, mock_db_conn):
    """Pipeline error sets job status to 'failed'"""
    error_message = "TTS service unavailable"

    with patch("src.process.get_conn") as mock_get_conn:
        mock_get_conn.side_effect = [mock_db_conn, mock_db_conn]

        with patch("src.process.assets_root_from_env", return_value="/tmp"):
            with patch("src.process.pick_background_video", return_value="/tmp/bg.mp4"):
                with patch(
                    "src.process.run_pipeline", side_effect=Exception(error_message)
                ):
                    process_job(mock_job)

    error_cursor = mock_db_conn.cursor.return_value
    error_cursor.execute.assert_called_once()
    call_args = error_cursor.execute.call_args[0]

    assert "UPDATE jobs" in call_args[0]
    assert "status = 'failed'" in call_args[0]
    assert "error = ?" in call_args[0]
    assert error_message in call_args[1]
    assert mock_job["id"] in call_args[1]

    mock_db_conn.commit.assert_called_once()


def test_process_job_closes_connections(mock_job):
    """DB connection is always closed after processing"""
    mock_conn = MagicMock()

    with patch("src.process.get_conn", return_value=mock_conn):
        with patch("src.process.assets_root_from_env", return_value="/tmp"):
            with patch("src.process.pick_background_video", return_value="/tmp/bg.mp4"):
                with patch("src.process.run_pipeline") as mock_pipeline:
                    mock_pipeline.return_value = "/tmp/result.mp4"

                    process_job(mock_job)

                    mock_conn.close.assert_called_once()


def test_process_job_handles_missing_voice(mock_db_conn):
    """Missing voice defaults to 'male'"""
    job_no_voice = {
        "id": "job-456",
        "text": "Test",
        "background": "subway",
        # voice is missing
    }

    with patch("src.process.get_conn", return_value=mock_db_conn):
        with patch("src.process.assets_root_from_env", return_value="/tmp"):
            with patch("src.process.pick_background_video", return_value="/tmp/bg.mp4"):
                with patch("src.process.run_pipeline") as mock_pipeline:
                    mock_pipeline.return_value = Path("/tmp/out.mp4")
                    process_job(job_no_voice)

    mock_pipeline.assert_called_once()
    _, kwargs = mock_pipeline.call_args
    assert kwargs["voice"] == "male"


def test_process_job_handles_missing_background(mock_job, mock_db_conn):
    """Missing background defaults to 'minecraft'"""
    job_no_bg = {
        "id": "job-789",
        "text": "Test",
        "voice": "female",
        # background is missing
    }

    with patch("src.process.get_conn", return_value=mock_db_conn):
        with patch("src.process.assets_root_from_env", return_value="/tmp"):
            with patch("src.process.pick_background_video") as mock_pick:
                with patch(
                    "src.process.run_pipeline", return_value=Path("/tmp/out.mp4")
                ):
                    process_job(job_no_bg)

    mock_pick.assert_called_once()
    assert mock_pick.call_args[0][1] == "minecraft"


def test_process_job_retries_on_called_process_error(
    mock_job, mock_db_conn, tmp_path, monkeypatch
):
    """Transient subprocess failures are retried before success."""
    monkeypatch.setenv("WORKER_PIPELINE_MAX_ATTEMPTS", "3")
    monkeypatch.setenv("WORKER_PIPELINE_RETRY_DELAY_SEC", "0")
    mock_result_path = tmp_path / "output.mp4"
    mock_result_path.write_text("ok")

    with patch("src.process.get_conn", return_value=mock_db_conn):
        with patch("src.process.assets_root_from_env", return_value=tmp_path):
            with patch(
                "src.process.pick_background_video", return_value=tmp_path / "bg.mp4"
            ):
                with patch("src.process.run_pipeline") as mock_run:
                    mock_run.side_effect = [
                        subprocess.CalledProcessError(1, cmd="ffmpeg"),
                        subprocess.CalledProcessError(1, cmd="ffmpeg"),
                        mock_result_path,
                    ]
                    with patch("src.process.time.sleep"):
                        process_job(mock_job)

    assert mock_run.call_count == 3


def test_process_job_fails_after_retry_exhausted(
    mock_job, mock_db_conn, tmp_path, monkeypatch
):
    """After max attempts on transient errors, job is marked failed."""
    monkeypatch.setenv("WORKER_PIPELINE_MAX_ATTEMPTS", "2")
    monkeypatch.setenv("WORKER_PIPELINE_RETRY_DELAY_SEC", "0")
    err = subprocess.CalledProcessError(1, cmd="ffmpeg")

    with patch("src.process.get_conn", return_value=mock_db_conn):
        with patch("src.process.assets_root_from_env", return_value=tmp_path):
            with patch(
                "src.process.pick_background_video", return_value=tmp_path / "bg.mp4"
            ):
                with patch("src.process.run_pipeline") as mock_run:
                    mock_run.side_effect = err
                    with patch("src.process.time.sleep"):
                        process_job(mock_job)

                    assert mock_run.call_count == 2

    error_cursor = mock_db_conn.cursor.return_value
    assert any(
        c[0] and "status = 'failed'" in c[0][0]
        for c in error_cursor.execute.call_args_list
    )
