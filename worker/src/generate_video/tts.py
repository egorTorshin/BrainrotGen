"""Text-to-speech: Piper (default) or optional HTTP endpoint."""

from __future__ import annotations

import contextlib
import os
import subprocess
import wave
from pathlib import Path

import requests

BASE_DIR = Path("/app")
PIPER_BIN = BASE_DIR / "piper/piper"
# Female: existing alba; male: lessac (downloaded in Dockerfile)
VOICE_MODELS = {
    "female": BASE_DIR / "piper_voice/en_GB-alba-medium.onnx",
    "male": BASE_DIR / "piper_voice/en_GB-northern_english_male-medium.onnx",
}


def wav_duration_seconds(wav_path: Path) -> float | None:
    """Return duration in seconds for a PCM WAV file, or None if unreadable."""
    try:
        with contextlib.closing(wave.open(str(wav_path), "rb")) as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if rate <= 0:
                return None
            return frames / float(rate)
    except (OSError, wave.Error):
        return None


def _piper_tts(text: str, model_path: Path, output_file: Path) -> Path:
    """Run Piper CLI to synthesize speech from text."""
    subprocess.run(
        [
            str(PIPER_BIN),
            "--model",
            str(model_path),
            "--output_file",
            str(output_file),
        ],
        input=text.encode("utf-8"),
        check=True,
    )
    return output_file


def _resolve_model_path(voice: str) -> Path:
    key = voice.strip().lower() if voice else "male"
    if key not in VOICE_MODELS:
        key = "male"
    model_path = VOICE_MODELS[key]
    if not model_path.is_file():
        for fallback in VOICE_MODELS.values():
            if fallback.is_file():
                return fallback
        raise FileNotFoundError(
            f"No Piper model found under {BASE_DIR / 'piper_voice'}",
        )
    return model_path


def _piper_synthesize(text: str, voice: str, output_file: Path) -> Path:
    model_path = _resolve_model_path(voice)
    return _piper_tts(text, model_path, output_file)


def _http_tts(text: str, output_file: Path) -> Path:
    """Use external HTTP API for TTS (alternative to Piper)."""
    url = os.environ.get("TTS_HTTP_URL", "").strip()
    if not url:
        raise RuntimeError("TTS_BACKEND=http but TTS_HTTP_URL is not set")
    timeout = float(os.environ.get("TTS_HTTP_TIMEOUT", "60"))
    response = requests.post(
        url,
        json={"text": text},
        timeout=timeout,
    )
    response.raise_for_status()
    # Accept raw audio bytes (wav) or JSON with base64 — keep minimal: raw body
    output_file.write_bytes(response.content)
    return output_file


def text_to_speech(text: str, voice: str, job_id: str, out_dir: Path) -> Path:
    """
    Synthesize speech to a WAV file under *out_dir* named with *job_id*.

    Args:
        text: Text to synthesize
        voice: "male" or "female"
        job_id: Unique job identifier for output filename
        out_dir: Output directory for WAV file

    Returns:
        Path to generated WAV file
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    output_file = out_dir / f"{job_id}.wav"

    backend = os.environ.get("TTS_BACKEND", "piper").strip().lower()

    if backend == "http":
        try:
            return _http_tts(text, output_file)
        except (requests.RequestException, OSError, RuntimeError) as http_err:
            try:
                return _piper_synthesize(text, voice, output_file)
            except Exception as piper_err:
                raise RuntimeError(
                    "HTTP TTS failed and Piper fallback failed: "
                    f"{http_err!s}; {piper_err!s}",
                ) from piper_err

    return _piper_synthesize(text, voice, output_file)
