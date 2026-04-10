# tests/generate_video/test_video.py
import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.generate_video.video import merge_video_audio_subs


def test_merge_video_audio_subs_success(tmp_path):
    """Успешное слияние видео, аудио и субтитров"""
    video_path = tmp_path / "input.mp4"
    audio_path = tmp_path / "audio.wav"
    srt_path = tmp_path / "subs.srt"
    output_path = tmp_path / "output.mp4"

    # Создаем фейковые файлы
    video_path.touch()
    audio_path.touch()
    srt_path.touch()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock()

        merge_video_audio_subs(video_path, audio_path, srt_path, output_path)

        # Проверяем вызов ffmpeg
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]

        assert args[0] == "ffmpeg"
        assert "-y" in args
        assert "-stream_loop" in args
        assert "-1" in args
        assert str(video_path) in args
        assert str(audio_path) in args
        assert "-vf" in args

        # Проверяем, что srt путь есть в аргументе subtitles
        vf_index = args.index("-vf")
        vf_value = args[vf_index + 1]
        assert f"subtitles={srt_path.as_posix()}" in vf_value or str(srt_path) in vf_value

        assert "-c:v" in args
        assert "libx264" in args
        assert "-c:a" in args
        assert "aac" in args
        assert "-shortest" in args
        assert str(output_path) in args


def test_merge_video_audio_subs_ffmpeg_failure(tmp_path):
    """FFmpeg падает → пробрасываем исключение"""
    video_path = tmp_path / "input.mp4"
    audio_path = tmp_path / "audio.wav"
    srt_path = tmp_path / "subs.srt"
    output_path = tmp_path / "output.mp4"

    video_path.touch()
    audio_path.touch()
    srt_path.touch()

    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "ffmpeg")):
        with pytest.raises(subprocess.CalledProcessError):
            merge_video_audio_subs(video_path, audio_path, srt_path, output_path)


def test_merge_video_audio_subs_handles_spaces_in_paths(tmp_path):
    """Пути с пробелами должны корректно обрабатываться"""
    video_path = tmp_path / "my video.mp4"
    audio_path = tmp_path / "my audio.wav"
    srt_path = tmp_path / "my subs.srt"
    output_path = tmp_path / "my output.mp4"

    video_path.touch()
    audio_path.touch()
    srt_path.touch()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock()

        merge_video_audio_subs(video_path, audio_path, srt_path, output_path)

        # Получаем аргументы вызова
        call_args = mock_run.call_args[0][0]

        # Проверяем, что пути присутствуют (как строки или экранированные)
        # Видео путь может быть как есть или в кавычках
        assert str(video_path) in " ".join(call_args) or video_path.name in " ".join(call_args)
        assert str(audio_path) in " ".join(call_args) or audio_path.name in " ".join(call_args)

        # Для srt проверяем, что он есть в аргументе -vf
        args_string = " ".join(call_args)
        assert str(srt_path) in args_string or srt_path.name in args_string


def test_merge_video_audio_subs_subtitle_style(tmp_path):
    """Проверяем, что стиль субтитров передается правильно"""
    video_path = tmp_path / "input.mp4"
    audio_path = tmp_path / "audio.wav"
    srt_path = tmp_path / "subs.srt"
    output_path = tmp_path / "output.mp4"

    video_path.touch()
    audio_path.touch()
    srt_path.touch()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock()

        merge_video_audio_subs(video_path, audio_path, srt_path, output_path)

        # Находим аргумент -vf
        args = mock_run.call_args[0][0]
        vf_index = args.index("-vf")
        vf_value = args[vf_index + 1]

        assert "Fontsize=24" in vf_value
        assert "Outline=2" in vf_value
        assert "Alignment=2" in vf_value


def test_merge_video_audio_subs_check_full_command(tmp_path):
    """Проверяем полную команду ffmpeg"""
    video_path = tmp_path / "input.mp4"
    audio_path = tmp_path / "audio.wav"
    srt_path = tmp_path / "subs.srt"
    output_path = tmp_path / "output.mp4"

    video_path.touch()
    audio_path.touch()
    srt_path.touch()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock()

        merge_video_audio_subs(video_path, audio_path, srt_path, output_path)

        # Получаем команду
        command = mock_run.call_args[0][0]

        # Проверяем ключевые элементы команды
        expected_parts = [
            "ffmpeg", "-y", "-stream_loop", "-1",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-map", "0:v", "-map", "1:a",
            "-c:v", "libx264", "-c:a", "aac",
            "-shortest", str(output_path)
        ]

        for part in expected_parts:
            assert part in command, f"Expected '{part}' not found in command"

        # Проверяем наличие subtitles в -vf аргументе
        vf_index = command.index("-vf")
        vf_value = command[vf_index + 1]
        assert "subtitles" in vf_value
        assert str(srt_path) in vf_value or srt_path.name in vf_value