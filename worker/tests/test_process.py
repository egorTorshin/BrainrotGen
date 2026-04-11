# tests/test_process.py
import pytest
from unittest.mock import patch, MagicMock, call
from pathlib import Path
from src.process import process_job


@pytest.fixture
def mock_job():
    return {
        "id": "job-123",
        "text": "Hello brainrot world",
        "voice": "male",
        "background": "minecraft",
        "estimated_duration": 15.0
    }


@pytest.fixture
def mock_db_conn():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    return conn


def test_process_job_success(mock_job, mock_db_conn, tmp_path):
    """Успешная обработка задачи"""
    mock_result_path = tmp_path / "output.mp4"
    mock_result_path.write_text("fake video content")

    with patch("src.process.get_conn", return_value=mock_db_conn):
        with patch("src.process.assets_root_from_env", return_value=tmp_path):
            with patch("src.process.pick_background_video", return_value=tmp_path / "bg.mp4"):
                with patch("src.process.run_pipeline", return_value=mock_result_path):
                    process_job(mock_job)

    # Проверяем UPDATE в БД
    mock_db_conn.cursor.return_value.execute.assert_called_once()
    call_args = mock_db_conn.cursor.return_value.execute.call_args[0]

    assert "UPDATE jobs" in call_args[0]
    assert "status = 'done'" in call_args[0]
    assert str(mock_result_path) in call_args[1]  # result_path
    assert mock_job["id"] in call_args[1]  # job_id

    mock_db_conn.commit.assert_called_once()


def test_process_job_failure(mock_job, mock_db_conn):
    """При ошибке в pipeline статус должен стать 'failed'"""
    error_message = "TTS service unavailable"

    with patch("src.process.get_conn") as mock_get_conn:
        # Первый вызов для основного update (который упадет)
        # Второй вызов для error update
        mock_get_conn.side_effect = [mock_db_conn, mock_db_conn]

        with patch("src.process.assets_root_from_env", return_value="/tmp"):
            with patch("src.process.pick_background_video", return_value="/tmp/bg.mp4"):
                with patch("src.process.run_pipeline", side_effect=Exception(error_message)):
                    process_job(mock_job)

    # Проверяем UPDATE с ошибкой
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
    """Проверяем, что соединение закрывается"""
    mock_conn = MagicMock()

    with patch("src.process.get_conn", return_value=mock_conn):
        with patch("src.process.assets_root_from_env", return_value="/tmp"):
            with patch("src.process.pick_background_video", return_value="/tmp/bg.mp4"):
                with patch("src.process.run_pipeline") as mock_pipeline:
                    # Симулируем успех
                    mock_pipeline.return_value = "/tmp/result.mp4"

                    process_job(mock_job)

                    # Проверяем, что close был вызван
                    mock_conn.close.assert_called_once()


def test_process_job_handles_missing_voice(mock_db_conn):
    """Если voice не указан, используем 'male' как default"""
    job_no_voice = {
        "id": "job-456",
        "text": "Test",
        "background": "subway"
        # voice отсутствует
    }

    with patch("src.process.get_conn", return_value=mock_db_conn):
        with patch("src.process.assets_root_from_env", return_value="/tmp"):
            with patch("src.process.pick_background_video", return_value="/tmp/bg.mp4"):
                with patch("src.process.run_pipeline") as mock_pipeline:
                    mock_pipeline.return_value = Path("/tmp/out.mp4")
                    process_job(job_no_voice)

    # Проверяем, что в pipeline передан default голос
    mock_pipeline.assert_called_once()
    _, kwargs = mock_pipeline.call_args
    assert kwargs["voice"] == "male"


def test_process_job_handles_missing_background(mock_job, mock_db_conn):
    """Если background не указан, используем 'minecraft' как default"""
    job_no_bg = {
        "id": "job-789",
        "text": "Test",
        "voice": "female"
        # background отсутствует
    }

    with patch("src.process.get_conn", return_value=mock_db_conn):
        with patch("src.process.assets_root_from_env", return_value="/tmp"):
            with patch("src.process.pick_background_video") as mock_pick:
                with patch("src.process.run_pipeline", return_value=Path("/tmp/out.mp4")):
                    process_job(job_no_bg)

    # Проверяем, что pick_background_video получил 'minecraft'
    mock_pick.assert_called_once()
    assert mock_pick.call_args[0][1] == "minecraft"