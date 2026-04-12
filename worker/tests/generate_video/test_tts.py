# tests/generate_video/test_tts.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess
import requests

from src.generate_video.tts import text_to_speech, _piper_tts, _http_tts, VOICE_MODELS


@pytest.fixture
def temp_output_dir(tmp_path):
    return tmp_path


def test_text_to_speech_piper_default_voice(temp_output_dir, tmp_path):
    """Piper backend with default male voice"""
    with patch("src.generate_video.tts.PIPER_BIN", tmp_path / "piper"):
        with patch(
            "src.generate_video.tts.VOICE_MODELS",
            {
                "male": tmp_path / "voice_male.onnx",
                "female": tmp_path / "voice_female.onnx",
            },
        ):
            (tmp_path / "voice_male.onnx").touch()

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock()

                result = text_to_speech(
                    text="Hello world",
                    voice="male",
                    job_id="test123",
                    out_dir=temp_output_dir,
                )

                assert result == temp_output_dir / "test123.wav"
                mock_run.assert_called_once()
                args = mock_run.call_args[0][0]
                assert str(tmp_path / "piper") in args
                assert "--model" in args
                assert str(tmp_path / "voice_male.onnx") in args


def test_text_to_speech_piper_fallback_on_missing_model(temp_output_dir, tmp_path):
    """Falls back to any available model when requested voice is missing"""
    with patch("src.generate_video.tts.PIPER_BIN", tmp_path / "piper"):
        with patch(
            "src.generate_video.tts.VOICE_MODELS",
            {
                "male": tmp_path / "missing.onnx",
                "female": tmp_path / "exists.onnx",
            },
        ):
            (tmp_path / "exists.onnx").touch()

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock()

                result = text_to_speech(
                    text="Hello", voice="male", job_id="test", out_dir=temp_output_dir
                )

                args = mock_run.call_args[0][0]
                assert str(tmp_path / "exists.onnx") in args


def test_text_to_speech_piper_raises_if_no_models(temp_output_dir, tmp_path):
    """No available models raises FileNotFoundError"""
    with patch("src.generate_video.tts.PIPER_BIN", tmp_path / "piper"):
        with patch(
            "src.generate_video.tts.VOICE_MODELS",
            {
                "male": tmp_path / "missing1.onnx",
                "female": tmp_path / "missing2.onnx",
            },
        ):
            with pytest.raises(FileNotFoundError, match="No Piper model found"):
                text_to_speech("Hello", "male", "test", temp_output_dir)


def test_text_to_speech_http_backend_success(temp_output_dir, monkeypatch):
    """HTTP TTS backend returns audio successfully"""
    monkeypatch.setenv("TTS_BACKEND", "http")
    monkeypatch.setenv("TTS_HTTP_URL", "http://tts.local/synthesize")

    mock_response = MagicMock()
    mock_response.content = b"fake_wav_data"
    mock_response.raise_for_status.return_value = None

    with patch("requests.post", return_value=mock_response) as mock_post:
        result = text_to_speech(
            text="Hello HTTP", voice="any", job_id="http123", out_dir=temp_output_dir
        )

        assert result == temp_output_dir / "http123.wav"
        assert result.read_bytes() == b"fake_wav_data"
        mock_post.assert_called_once_with(
            "http://tts.local/synthesize", json={"text": "Hello HTTP"}, timeout=60.0
        )


def test_text_to_speech_http_backend_missing_url(temp_output_dir, monkeypatch):
    """TTS_BACKEND=http without TTS_HTTP_URL raises RuntimeError"""
    monkeypatch.setenv("TTS_BACKEND", "http")
    monkeypatch.delenv("TTS_HTTP_URL", raising=False)

    with pytest.raises(RuntimeError, match="TTS_HTTP_URL is not set"):
        text_to_speech("Hello", "male", "test", temp_output_dir)


def test_text_to_speech_http_backend_request_fails(temp_output_dir, monkeypatch):
    """HTTP request failure: clear error when Piper fallback also unavailable."""
    monkeypatch.setenv("TTS_BACKEND", "http")
    monkeypatch.setenv("TTS_HTTP_URL", "http://tts.local")

    with patch(
        "requests.post", side_effect=requests.RequestException("Connection refused")
    ):
        with pytest.raises(
            RuntimeError, match="HTTP TTS failed and Piper fallback failed"
        ):
            text_to_speech("Hello", "male", "test", temp_output_dir)


def test_text_to_speech_http_falls_back_to_piper(
    temp_output_dir, tmp_path, monkeypatch
):
    """HTTP TTS failure falls back to Piper when models exist."""
    monkeypatch.setenv("TTS_BACKEND", "http")
    monkeypatch.setenv("TTS_HTTP_URL", "http://tts.local")

    with patch("src.generate_video.tts.PIPER_BIN", tmp_path / "piper"):
        with patch(
            "src.generate_video.tts.VOICE_MODELS",
            {
                "male": tmp_path / "m.onnx",
                "female": tmp_path / "f.onnx",
            },
        ):
            (tmp_path / "m.onnx").touch()
            with patch("requests.post", side_effect=requests.RequestException("down")):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock()
                    out = text_to_speech("Hi", "male", "fb", temp_output_dir)
                    assert out == temp_output_dir / "fb.wav"
                    mock_run.assert_called_once()


def test_text_to_speech_http_custom_timeout(temp_output_dir, monkeypatch):
    """Custom timeout from TTS_HTTP_TIMEOUT env var"""
    monkeypatch.setenv("TTS_BACKEND", "http")
    monkeypatch.setenv("TTS_HTTP_URL", "http://tts.local")
    monkeypatch.setenv("TTS_HTTP_TIMEOUT", "30.5")

    mock_response = MagicMock()
    mock_response.content = b"data"
    mock_response.raise_for_status.return_value = None

    with patch("requests.post", return_value=mock_response) as mock_post:
        text_to_speech("Hello", "male", "test", temp_output_dir)

        mock_post.assert_called_once()
        assert mock_post.call_args[1]["timeout"] == 30.5


def test_piper_tts_invalid_model_path(temp_output_dir, tmp_path):
    """Piper raises CalledProcessError for non-existent model"""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "piper")

        with pytest.raises(subprocess.CalledProcessError):
            _piper_tts(
                "Hello", tmp_path / "nonexistent.onnx", temp_output_dir / "out.wav"
            )
