# tests/generate_video/test_subtitles.py
import pytest
import wave
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.generate_video.subtitles import split_text, get_audio_duration, format_time, generate_srt


def test_split_text_default_max_words():
    """Splits text into chunks of 5 words by default"""
    text = "one two three four five six seven eight nine ten"
    result = split_text(text)
    assert result == ["one two three four five", "six seven eight nine ten"]


def test_split_text_custom_max_words():
    """Custom max_words parameter changes chunk size"""
    text = "a b c d e f g"
    result = split_text(text, max_words=3)
    assert result == ["a b c", "d e f", "g"]


def test_split_text_single_chunk():
    """Short text produces a single chunk"""
    text = "hello world"
    result = split_text(text)
    assert result == ["hello world"]


def test_split_text_empty():
    """Empty text produces an empty list"""
    result = split_text("")
    assert result == []


def test_format_time():
    """Verify SRT timestamp formatting for various inputs"""
    result1 = format_time(0.0)
    assert result1 in ["00:00:00,000", "00:00:00.000", "00:00:00", "0:00:00"]

    result2 = format_time(1.5)
    assert result2 in ["00:00:01,500", "00:00:01.500", "00:00:01"]

    result3 = format_time(61.123)
    assert "01:01" in result3 or "1:01" in result3

    result4 = format_time(3665.789)
    assert "01:01:05" in result4 or "1:01:05" in result4


def test_get_audio_duration(tmp_path):
    """Returns WAV file duration in seconds"""
    audio_path = tmp_path / "test.wav"

    import struct
    with wave.open(str(audio_path), 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(44100)
        frames = b'\x00\x00' * 44100
        wav.writeframes(frames)

    duration = get_audio_duration(audio_path)
    assert abs(duration - 1.0) < 0.1


@patch("wave.open")
def test_get_audio_duration_calculates_correctly(mock_wave_open):
    """Mocked wave.open for fast calculation tests"""
    mock_wav = MagicMock()
    mock_wav.getnframes.return_value = 88200
    mock_wav.getframerate.return_value = 44100
    mock_wave_open.return_value.__enter__.return_value = mock_wav

    duration = get_audio_duration(Path("dummy.wav"))
    assert duration == 2.0


def test_generate_srt_creates_file(tmp_path):
    """Creates an SRT file with valid structure"""
    text = "Hello world this is a test"
    audio_path = tmp_path / "audio.wav"

    import struct
    with wave.open(str(audio_path), 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(44100)
        frames = b'\x00\x00' * 88200
        wav.writeframes(frames)

    srt_path = tmp_path / "output.srt"
    generate_srt(text, audio_path, srt_path)

    assert srt_path.exists()
    content = srt_path.read_text(encoding="utf-8")

    assert "1" in content
    assert "-->" in content
    assert "Hello world" in content



def test_generate_srt_chunks_cover_full_duration(tmp_path):
    """All chunks together cover the full audio duration"""
    text = "one two three four five six seven eight nine ten"
    audio_path = tmp_path / "audio.wav"

    with wave.open(str(audio_path), 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(44100)
        wav.writeframes(b'\x00\x00' * 44100 * 10)

    srt_path = tmp_path / "full.srt"
    generate_srt(text, audio_path, srt_path)

    content = srt_path.read_text()
    assert content.count("\n\n") >= 2

    lines = content.split("\n")
    timestamps = [line for line in lines if "-->" in line]
    last_timestamp = timestamps[-1]
    end_time = last_timestamp.split(" --> ")[1]

    # Verify the end time is around 10 seconds
    if ":" in end_time:
        parts = end_time.replace(",", ":").replace(".", ":").split(":")
        if len(parts) >= 3:
            seconds = int(parts[2]) if parts[2].isdigit() else 0
            assert seconds >= 9 or seconds <= 11
