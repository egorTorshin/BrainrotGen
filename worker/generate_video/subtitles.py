from pathlib import Path
import wave


def split_text(text: str, max_words=5):
    words = text.split()
    return [
        " ".join(words[i:i+max_words])
        for i in range(0, len(words), max_words)
    ]


def get_audio_duration(path: Path):
    with wave.open(str(path), 'r') as f:
        return f.getnframes() / f.getframerate()


def format_time(seconds: float):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def generate_srt(text: str, audio_path: Path, output_path: Path):
    chunks = split_text(text)
    duration = get_audio_duration(audio_path)

    if len(chunks) == 0:
        return

    chunk_duration = duration / len(chunks)

    with open(output_path, "w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks):
            start = i * chunk_duration
            end = (i + 1) * chunk_duration

            f.write(f"{i+1}\n")
            f.write(f"{format_time(start)} --> {format_time(end)}\n")
            f.write(chunk + "\n\n")