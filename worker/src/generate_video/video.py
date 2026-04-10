import subprocess
from pathlib import Path


def merge_video_audio_subs(
    video_path: Path, audio_path: Path, srt_path: Path, output_path: Path
):
    subtitle_filter = (
        f"subtitles={srt_path.as_posix()}:"
        f"force_style='Fontsize=24,Outline=2,Alignment=2'"
    )

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-stream_loop",
            "-1",
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-map",
            "0:v",
            "-map",
            "1:a",
            "-vf",
            subtitle_filter,
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-shortest",
            str(output_path),
        ],
        check=True,
    )
