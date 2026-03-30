from pathlib import Path
from worker.pipeline import run_pipeline


if __name__ == "__main__":
    text = "This is a test of the brainrot video generator. It should create subtitles and voice."

    video_path = Path("/app/assets/sample-5s.mp4")

    result = run_pipeline(text, video_path)

    print(f"Done: {result}")