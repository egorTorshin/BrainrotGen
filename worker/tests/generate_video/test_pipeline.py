# tests/generate_video/test_pipeline.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from src.generate_video.pipeline import run_pipeline, output_dir


def test_output_dir_from_env(monkeypatch):
    """Читаем OUTPUT_DIR из окружения"""
    monkeypatch.setenv("OUTPUT_DIR", "/custom/output")
    assert output_dir() == Path("/custom/output")


def test_output_dir_default(monkeypatch):
    """Дефолтный OUTPUT_DIR"""
    monkeypatch.delenv("OUTPUT_DIR", raising=False)
    assert output_dir() == Path("/app/output")


def test_run_pipeline_creates_output_dir(tmp_path):
    """Если output директории нет → создает"""
    job_id = "test"
    output_path = tmp_path / "nonexistent" / "deep" / "dir"

    with patch("src.generate_video.pipeline.output_dir", return_value=output_path):
        with patch("src.generate_video.pipeline.text_to_speech") as mock_tts:
            mock_tts.return_value = output_path / f"{job_id}.wav"
            with patch("src.generate_video.pipeline.generate_srt"):
                with patch("src.generate_video.pipeline.merge_video_audio_subs"):
                    run_pipeline(
                        job_id=job_id,
                        text="Test",
                        voice="male",
                        video_path=Path("/dummy.mp4")
                    )

                    assert output_path.exists()
                    assert output_path.is_dir()


def test_run_pipeline_passes_correct_srt_path(tmp_path):
    """Проверяем, что generate_srt получает правильный путь"""
    job_id = "srt_test"
    mock_output_dir = tmp_path / "output"
    mock_audio_path = mock_output_dir / f"{job_id}.wav"

    with patch("src.generate_video.pipeline.output_dir", return_value=mock_output_dir):
        with patch("src.generate_video.pipeline.text_to_speech") as mock_tts:
            mock_tts.return_value = mock_audio_path

            with patch("src.generate_video.pipeline.generate_srt") as mock_srt:
                with patch("src.generate_video.pipeline.merge_video_audio_subs"):
                    run_pipeline(
                        job_id=job_id,
                        text="Test",
                        voice="male",
                        video_path=Path("/dummy.mp4")
                    )

                    # Проверяем, что generate_srt вызван с правильными аргументами
                    mock_srt.assert_called_once()
                    call_args = mock_srt.call_args

                    # Один из аргументов должен быть путем к srt файлу
                    expected_srt = mock_output_dir / f"{job_id}.srt"
                    assert expected_srt in call_args[0] or expected_srt in call_args[1].values()


def test_run_pipeline_pipeline_failure_propagates(tmp_path):
    """Ошибка на любом этапе пайплайна пробрасывается наверх"""
    job_id = "fail"

    with patch("src.generate_video.pipeline.output_dir", return_value=tmp_path):
        with patch("src.generate_video.pipeline.text_to_speech", side_effect=RuntimeError("TTS failed")):
            with pytest.raises(RuntimeError, match="TTS failed"):
                run_pipeline(
                    job_id=job_id,
                    text="Test",
                    voice="male",
                    video_path=Path("/dummy.mp4")
                )


def test_run_pipeline_handles_special_characters(tmp_path):
    """Pipeline должен работать с текстом, содержащим спецсимволы"""
    job_id = "special"
    text = "Hello @#$%^&*() world! 🚀"
    voice = "male"
    video_path = tmp_path / "bg.mp4"
    video_path.touch()

    mock_output_dir = tmp_path / "output"

    with patch("src.generate_video.pipeline.output_dir", return_value=mock_output_dir):
        with patch("src.generate_video.pipeline.text_to_speech") as mock_tts:
            mock_tts.return_value = mock_output_dir / f"{job_id}.wav"
            with patch("src.generate_video.pipeline.generate_srt"):
                with patch("src.generate_video.pipeline.merge_video_audio_subs"):
                    result = run_pipeline(
                        job_id=job_id,
                        text=text,
                        voice=voice,
                        video_path=video_path
                    )

                    assert result == mock_output_dir / f"{job_id}.mp4"
                    # Проверяем, что текст передан правильно (независимо от порядка аргументов)
                    mock_tts.assert_called_once()
                    call_args = mock_tts.call_args
                    # Проверяем, что text присутствует в аргументах
                    assert text in str(call_args)


def test_run_pipeline_debug(tmp_path):
    """Отладочный тест - выводит реальные вызовы"""
    job_id = "debug"
    text = "Debug text"
    voice = "male"
    video_path = tmp_path / "bg.mp4"
    video_path.touch()

    mock_output_dir = tmp_path / "output"

    # Создаем реальные моки с записью вызовов
    with patch("src.generate_video.pipeline.output_dir", return_value=mock_output_dir):
        with patch("src.generate_video.pipeline.text_to_speech") as mock_tts:
            mock_tts.return_value = mock_output_dir / f"{job_id}.wav"

            with patch("src.generate_video.pipeline.generate_srt") as mock_srt:
                with patch("src.generate_video.pipeline.merge_video_audio_subs") as mock_merge:
                    result = run_pipeline(
                        job_id=job_id,
                        text=text,
                        voice=voice,
                        video_path=video_path
                    )

                    # Выводим информацию для отладки
                    print(f"\n=== DEBUG INFO ===")
                    print(f"text_to_speech call args: {mock_tts.call_args}")
                    print(f"generate_srt call args: {mock_srt.call_args}")
                    print(f"merge_video_audio_subs call args: {mock_merge.call_args}")
                    print(f"Result: {result}")
                    print(f"==================\n")

                    # Просто проверяем, что все вызвано хотя бы раз
                    assert mock_tts.called
                    assert mock_srt.called
                    assert mock_merge.called
                    assert result is not None