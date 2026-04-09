"""Text-to-speech: Piper (default) or optional HTTP endpoint."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import requests

BASE_DIR = Path("/app")
PIPER_BIN = BASE_DIR / "piper/piper"
# Female: existing alba; male: lessac (downloaded in Dockerfile)
VOICE_MODELS = {
    "female": BASE_DIR / "piper_voice/en_GB-alba-medium.onnx",
    "male": BASE_DIR / "piper_voice/en_US-lessac-medium.onnx",
}


def _piper_tts(text: str, model_path: Path, output_file: Path) -> Path:
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


def _http_tts(text: str, output_file: Path) -> Path:
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
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    output_file = out_dir / f"{job_id}.wav"

    backend = os.environ.get("TTS_BACKEND", "piper").strip().lower()

    if backend == "http":
        try:
            return _http_tts(text, output_file)
        except (requests.RequestException, OSError, RuntimeError) as e:
            raise RuntimeError(f"HTTP TTS failed: {e}") from e

    key = voice.strip().lower() if voice else "male"
    if key not in VOICE_MODELS:
        key = "male"
    model_path = VOICE_MODELS[key]
    if not model_path.is_file():
        # Fallback: any available model (e.g. partial Docker setup)
        for fallback in VOICE_MODELS.values():
            if fallback.is_file():
                model_path = fallback
                break
        else:
            raise FileNotFoundError(f"No Piper model found under {BASE_DIR / 'piper_voice'}")

    return _piper_tts(text, model_path, output_file)
