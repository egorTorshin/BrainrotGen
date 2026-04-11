from pathlib import Path
import wave


def split_text(text: str, max_words=5):
    """
    Split text into chunks of max_words per chunk.

    Args:
        text: Input text to split
        max_words: Maximum words per chunk (default: 5)

    Returns:
        List of text chunks
    """
    words = text.split()
    return [" ".join(words[i : i + max_words]) for i in range(0, len(words), max_words)]


def get_audio_duration(path: Path):
    """
    Extract duration in seconds from WAV file.

    Args:
        path: Path to WAV file

    Returns:
        Duration in seconds as float
    """
    with wave.open(str(path), "r") as f:
        return f.getnframes() / f.getframerate()


def format_time(seconds: float):
    """
    Convert seconds to SRT timestamp format (HH:MM:SS,mmm).

    Args:
        seconds: Time in seconds (e.g., 61.5)

    Returns:
        Formatted timestamp (e.g., "00:01:01,500")
    """
    h = int(seconds // 3600)  # Hours
    m = int((seconds % 3600) // 60)  # Minutes
    s = int(seconds % 60)  # Seconds
    ms = int((seconds - int(seconds)) * 1000)  # Milliseconds
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def generate_srt(text: str, audio_path: Path, output_path: Path):
    """
    Generate SRT subtitle file with evenly distributed text chunks.

    Distributes text chunks uniformly across the audio duration.

    Args:
        text: Source text to convert to subtitles
        audio_path: Path to WAV audio file
        output_path: Path where SRT file will be written

    Returns:
        None (writes file directly)
    """
    chunks = split_text(text)
    duration = get_audio_duration(audio_path)

    if len(chunks) == 0:
        return  # Empty text, nothing to generate

    chunk_duration = duration / len(chunks)  # Time per subtitle chunk

    with open(output_path, "w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks):
            start = i * chunk_duration
            end = (i + 1) * chunk_duration

            # Write SRT entry: index, timestamp, text, blank line
            f.write(f"{i + 1}\n")
            f.write(f"{format_time(start)} --> {format_time(end)}\n")
            f.write(chunk + "\n\n")
