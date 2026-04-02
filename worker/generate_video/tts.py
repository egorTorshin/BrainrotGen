from pathlib import Path
import subprocess
import uuid

BASE_DIR = Path("/app")  # Docker root

PIPER_PATH = BASE_DIR / "piper/piper"
MODEL_PATH = BASE_DIR / "piper_voice/en_GB-alba-medium.onnx"
OUTPUT_DIR = BASE_DIR / "output"


def text_to_speech(text: str) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)

    output_file = OUTPUT_DIR / f"{uuid.uuid4()}.wav"

    subprocess.run(
        [
            str(PIPER_PATH),
            "--model", str(MODEL_PATH),
            "--output_file", str(output_file)
        ],
        input=text.encode("utf-8"),
        check=True
    )

    return output_file