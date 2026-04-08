from pathlib import Path
import uuid

from .tts import text_to_speech
from .subtitles import generate_srt
from .video import merge_video_audio_subs

OUTPUT_DIR = Path("/app/output")


def run_pipeline(text: str, video_path: Path) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)

    job_id = uuid.uuid4()

    audio_path = text_to_speech(text)

    srt_path = OUTPUT_DIR / f"{job_id}.srt"
    generate_srt(text, audio_path, srt_path)

    output_video = OUTPUT_DIR / f"{job_id}.mp4"

    merge_video_audio_subs(
        video_path=video_path,
        audio_path=audio_path,
        srt_path=srt_path,
        output_path=output_video
    )

    print(f"OUTPUT_DIR exists: {OUTPUT_DIR.exists()}")
    print(f"Writing SRT to: {srt_path}")
    print(f"Writing video to: {output_video}")

    return output_video