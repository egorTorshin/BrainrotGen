# tests/generate_video/test_pipeline.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from src.generate_video.pipeline import run_pipeline, output_dir


def test_output_dir_from_env(monkeypatch):
    """Reads OUTPUT_DIR from environment"""
    monkeypatch.setenv("OUTPUT_DIR", "/custom/output")
    assert output_dir() == Path("/custom/output")


def test_output_dir_default(monkeypatch):
    """Default OUTPUT_DIR when env var is unset"""
    monkeypatch.delenv("OUTPUT_DIR", raising=False)
    assert output_dir() == Path("/app/output")


def test_run_pipeline_creates_output_dir(tmp_path):
    """Creates output directory if it does not exist"""
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
    """generate_srt receives the correct SRT file path"""
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

                    mock_srt.assert_called_once()
                    call_args = mock_srt.call_args

                    expected_srt = mock_output_dir / f"{job_id}.srt"
                    assert expected_srt in call_args[0] or expected_srt in call_args[1].values()


def test_run_pipeline_pipeline_failure_propagates(tmp_path):
    """Error at any pipeline stage propagates to the caller"""
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
    """Pipeline handles text with special characters"""
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
                    mock_tts.assert_called_once()
                    call_args = mock_tts.call_args
                    assert text in str(call_args)


def test_run_pipeline_debug(tmp_path):
    """Debug test that prints actual call arguments"""
    job_id = "debug"
    text = "Debug text"
    voice = "male"
    video_path = tmp_path / "bg.mp4"
    video_path.touch()

    mock_output_dir = tmp_path / "output"

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

                    print(f"\n=== DEBUG INFO ===")
                    print(f"text_to_speech call args: {mock_tts.call_args}")
                    print(f"generate_srt call args: {mock_srt.call_args}")
                    print(f"merge_video_audio_subs call args: {mock_merge.call_args}")
                    print(f"Result: {result}")
                    print(f"==================\n")

                    assert mock_tts.called
                    assert mock_srt.called
                    assert mock_merge.called
                    assert result is not None
